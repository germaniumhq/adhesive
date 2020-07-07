import logging
import os
import sys
import time
import traceback
import uuid
from concurrent.futures import Future
from threading import Lock
from typing import Optional, Dict, TypeVar, Any, List, Tuple, Union, Set, cast

import pebble.pool
import schedule

import adhesive
from adhesive import logredirect
from adhesive.consoleui.color_print import red, yellow, white
from adhesive.execution import token_utils
from adhesive.execution.ExecutionData import ExecutionData
from adhesive.execution.ExecutionMessageCallbackEvent import ExecutionMessageCallbackEvent
from adhesive.execution.ExecutionMessageEvent import ExecutionMessageEvent
from adhesive.execution.ExecutionToken import ExecutionToken
from adhesive.execution.ExecutionUserTask import ExecutionUserTask
from adhesive.execution.call_script_task import call_script_task
from adhesive.execution.deduplication import get_deduplication_id
from adhesive.graph.Edge import Edge
from adhesive.graph.Event import Event
from adhesive.graph.ExecutableNode import ExecutableNode
from adhesive.graph.NonWaitingGateway import NonWaitingGateway
from adhesive.graph.ScriptTask import ScriptTask
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.graph.WaitingGateway import WaitingGateway
from adhesive.graph.time.TimerBoundaryEvent import TimerBoundaryEvent
from adhesive.model.GatewayController import GatewayController
from adhesive.model.MessageEventExecutor import MessageEventExecutor
from adhesive.model.ProcessEvents import ProcessEvents
from adhesive.model.ProcessExecutorConfig import ProcessExecutorConfig
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.model.time.ActiveTimer import ActiveTimer
from adhesive.model.time.active_timer_factory import create_active_timer
from adhesive.storage.task_storage import get_folder

T = TypeVar('T')

import concurrent.futures

from adhesive.graph.ProcessTask import ProcessTask
from adhesive.graph.Process import Process
from adhesive.execution.ExecutionTask import ExecutionTask
from adhesive import config

from adhesive.model import lane_controller
from adhesive.model import loop_controller

from adhesive.model.ActiveEventStateMachine import ActiveEventState
from adhesive.model.ActiveLoopType import ActiveLoopType
from adhesive.model.ActiveEvent import ActiveEvent, is_potential_predecessor, copy_event, DONE_STATES, \
    ACTIVE_STATES
from adhesive.model.AdhesiveProcess import AdhesiveProcess

import signal


LOG = logging.getLogger(__name__)


class TaskError:
    def __init__(self,
                 *,
                 error: str,
                 exception: Exception,
                 failed_event: ActiveEvent) -> None:
        self.error = error
        self.exception = exception
        self.failed_event = failed_event


class TaskFinishMode:
    """
    Defines how a task is being finishing. Depending of this,
    we can decide what needs to be done when cleaning up the
    """
    pass


class CancelTaskFinishModeException(Exception, TaskFinishMode):
    def __init__(self,
                 *,
                 root_node: bool = False,
                 task_error: Optional[TaskError] = None) -> None:
        self.root_node = root_node
        self.task_error = task_error


class OutgoingEdgesFinishMode(TaskFinishMode):
    def __init__(self,
                 outgoing_edges: Optional[List[Edge]]) -> None:
        self.outgoing_edges = outgoing_edges


def raise_unhandled_exception(task_error: TaskError):
    log_path = get_folder(task_error.failed_event)

    LOG.error(red("Process execution failed. Unhandled error from ") +
              red(str(task_error.failed_event), bold=True))

    if logredirect.is_enabled():
        stdout_file = os.path.join(log_path, "stdout")
        if os.path.isfile(stdout_file):
            with open(stdout_file) as f:
                LOG.error(white("STDOUT:", bold=True))
                LOG.error(white(f.read()))
        else:
            LOG.error(white("STDOUT:", bold=True) + white(" not found"))

        stderr_file = os.path.join(log_path, "stderr")
        if os.path.isfile(stderr_file):
            with open(stderr_file) as f:
                LOG.error(red("STDERR:"))
                LOG.error(red(f.read()))
        else:
            LOG.error(red("STDERR:", bold=True) + red(" not found"))

    LOG.error(red("Exception:", bold=True))
    LOG.error(red(task_error.error))

    sys.exit(1)


class ProcessExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool_size = int(config.current.pool_size) if config.current.pool_size else 8
    pool: Union[pebble.pool.ProcessPool, pebble.pool.ThreadPool] = \
        pebble.pool.ProcessPool(max_workers=pool_size) \
        if config.current.parallel_processing == "process" \
        else pebble.pool.ThreadPool(max_workers=pool_size)

    def __init__(self,
                 process: AdhesiveProcess,
                 ut_provider: Optional[UserTaskProvider] = None,
                 wait_tasks: bool = True) -> None:
        self.adhesive_process = process
        self.tasks_impl: Dict[str, ExecutionTask] = dict()
        self.user_tasks_impl: Dict[str, ExecutionUserTask] = dict()
        self.mevent_impl: Dict[str, ExecutionMessageEvent] = dict()
        self.mevent_callback_impl: Dict[str, ExecutionMessageCallbackEvent] = dict()

        # A dictionary of events that are currently active. This is just to find out
        # the parent of an event, since from it we can also derive the current parent
        # process.
        self.events: ProcessEvents = ProcessEvents()
        self.futures: Dict[Future, str] = dict()
        self.ut_provider = ut_provider

        self.active_timers: Dict[str, Set[ActiveTimer]] = dict()

        self.enqueued_events: List[Tuple[Event, Any]] = list()
        self.enqueued_events_lock = Lock()

        self.config = ProcessExecutorConfig(wait_tasks=wait_tasks)
        self.execution_id = str(uuid.uuid4())

    def execute(self,
                initial_data=None) -> ExecutionData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        process = self.adhesive_process.process
        self.tasks_impl = dict()

        _validate_tasks(self, process)

        if adhesive.config.current.verify_mode:
            return ExecutionData(initial_data)

        signal.signal(signal.SIGUSR1, self.print_state)

        # since the workspaces are allocated by lanes, we need to ensure
        # our default lane is existing.
        lane_controller.ensure_default_lane(self.adhesive_process)

        # FIXME: it's getting pretty crowded
        token_id = str(uuid.uuid4())
        process_context: ExecutionToken = ExecutionToken(
            task=process,
            execution_id=self.execution_id,
            token_id=token_id,
            data=initial_data
        )

        fake_event = ActiveEvent(
            execution_id=self.execution_id,
            parent_id=None,
            context=process_context
        )
        fake_event.token_id = ""  # FIXME: why

        root_event = self.clone_event(fake_event, process)
        self.root_event = root_event

        self.start_message_event_listeners(root_event=root_event)
        self.execute_process_event_loop()

        return root_event.context.data

    def print_state(self, x, y) -> None:
        LOG.info("Events list:")
        for event in self.events.events.values():
            LOG.info(event)

        LOG.info("Futures:")
        for f in self.futures:
            LOG.info(f)

    def start_message_event_listeners(self, root_event: ActiveEvent):
        def create_callback_code(mevent_id, mevent):
            message_event = self.adhesive_process.process.message_events[mevent_id]
            event_name_parsed = token_utils.parse_name(
                self.root_event.context,
                message_event.name)

            params = token_utils.matches(mevent.re_expressions,
                                         event_name_parsed)

            def callback_code(event_data):
                self.enqueue_event(
                    event=message_event,
                    event_data=event_data)

            mevent.code(root_event.context, callback_code, *params)

        for mevent_id, mevent in self.mevent_callback_impl.items():
            create_callback_code(mevent_id, mevent)

        for callback_event_id, callback_event in self.mevent_impl.items():
            executor = MessageEventExecutor(
                root_event=root_event,
                message_event=self.adhesive_process.process.message_events[callback_event_id],
                execution_message_event=callback_event,
                enqueue_event=self.enqueue_event)

            self.futures[executor.future] = "__message_executor"

    def consume_events(self,
                       state: ActiveEventState,
                       callback):
        event, data = self.events.pop(state)
        while event:
            callback(event, data)
            event, data = self.events.pop(state)

    def new_event(self,
                  event: ActiveEvent,
                  data: Any):
        # we keep track how many deduplication events are in flight
        if event.deduplication_id:
            self.events.register_deduplication_event(event)

        self.events.transition(event=event,
                               state=ActiveEventState.PROCESSING)

    def execute_process_event_loop(self) -> None:
        """
        Main event loop. Processes the events from a process until no more
        events are available.  For example an event is the start of the
        process. The events are then creating futures (i.e. actual stuff that's
        being processed) that in turn might generate new events.
        :return: data from the last execution token.
        """
        while self.events or self.futures:
            # we ensure we have only events to be processed
            self.events.changed = True

            while self.events.changed:
                self.events.changed = False
                self.consume_events(ActiveEventState.NEW, self.new_event)
                self.consume_events(ActiveEventState.PROCESSING, self.process_event)
                self.consume_events(ActiveEventState.WAITING, self.wait_task)
                self.consume_events(ActiveEventState.ERROR, self.done_check)
                self.consume_events(ActiveEventState.RUNNING, self.run_task)
                self.consume_events(ActiveEventState.ROUTING, self.route_task)
                self.consume_events(ActiveEventState.DONE_CHECK, self.done_check)
                self.consume_events(ActiveEventState.DONE, self.done_task)

            if not self.futures:
                time.sleep(0.1)

            done_futures, not_done_futures = concurrent.futures.wait(
                self.futures.keys(),
                return_when=concurrent.futures.FIRST_COMPLETED,
                timeout=0.1)

            # We need to read the enqueued events before dealing with the done futures. If
            # a message has finished generating events, and the events are only enqueued
            # they are not yet visible in the `done_check()` so our root process might
            # inadvertently exit to soon, before trying to clone the enqueued events.
            self.read_enqueued_events()

            for future in done_futures:
                token_id = self.futures[future]
                del self.futures[future]

                # a message executor has finished
                if token_id == "__message_executor":
                    # FIXME: this is duplicated code from done_task
                    # check sub-process termination
                    found = False
                    for ev in self.events.excluding(ActiveEventState.DONE):
                        if ev.parent_id == self.root_event.token_id and ev != self.root_event:
                            found = True
                            break

                    # FIXME: why could this be not found?
                    if not found:
                        self.events.transition(
                            event=self.root_event,
                            state=ActiveEventState.ROUTING,
                            data=self.root_event.context)

                    continue

                try:
                    context = future.result()

                    self.events.transition(
                        event=token_id,
                        state=ActiveEventState.ROUTING,
                        data=context)
                except CancelTaskFinishModeException:
                    pass
                except concurrent.futures.CancelledError:
                    pass
                except Exception as e:
                    self.handle_task_error(
                        TaskError(
                            error = traceback.format_exc(),
                            exception = e,
                            failed_event = self.events[token_id],
                        )
                    )

            # we evaluate all timers that might still be pending
            schedule.run_pending()

    def register_event(self,
                       event: ActiveEvent) -> ActiveEvent:
        """
        Register the event into a big map for finding, so we can access it later
        for parents and what not, without serializing the event graph to
        the subprocesses.

        :param event:
        :return:
        """
        if event.token_id in self.events:
            raise Exception(f"Event {event.token_id} is already registered as "
                            f"{self.events[event.token_id]}. Got a new request to register "
                            f"it as {event}.")

        LOG.debug(f"Register {event}")

        lane_controller.allocate_workspace(self.adhesive_process, event)

        self.events[event.token_id] = event

        return event

    def unregister_event(self,
                         event: ActiveEvent) -> None:
        if event.token_id not in self.events:
            raise Exception(f"{event} not found in events. Either the event was "
                            f"already terminated, either it was not registered.")

        lane_controller.deallocate_workspace(self.adhesive_process, event)

        LOG.debug(f"Unregister {event}")

        # We unregister all the timers for this token.
        timers = self.active_timers.get(event.token_id, None)
        if timers:
            schedule.clear(event.token_id)
            del self.active_timers[event.token_id]

        del self.events[event.token_id]

    def enqueue_event(self,
                      *,
                      event: Event,
                      event_data: Any) -> None:
        with self.enqueued_events_lock:
            self.enqueued_events.append((event, event_data))

    def read_enqueued_events(self) -> None:
        """
        Reads all the events that are being injected from different threads,
        and clone them from the root_event into our process.
        :return:
        """
        new_events = []

        # we release the lock ASAP
        with self.enqueued_events_lock:
            new_events.extend(self.enqueued_events)
            self.enqueued_events.clear()

        for event, event_data in new_events:
            new_event = self.clone_event(
                self.root_event,
                event,
                parent_id=self.root_event.token_id)
            new_event.context.data.event = event_data

    def get_parent(self,
                   token_id: str) -> ActiveEvent:
        """
        Find the parent of an event by looking at the event ids.
        :param token_id:
        :return:
        """
        event = self.events[token_id]
        assert event.parent_id

        parent = self.events[event.parent_id]

        return parent

    def fire_timer(
            self,
            parent_event: ActiveEvent,
            boundary_event: TimerBoundaryEvent) -> None:
        """
        Called when a timer was fired. If the event is supposed to be
        cancelled, it will attempt to cancel it.
        """
        LOG.debug(f"Fired timer for {boundary_event}")
        self.clone_event(parent_event, boundary_event)

        if not boundary_event.cancel_activity:
            return

        self.cancel_subtree(parent_event,
                            CancelTaskFinishModeException(root_node=True))

    def cancel_subtree(self,
                       parent_event: ActiveEvent,
                       e: CancelTaskFinishModeException) -> None:
        # we move the nested events into error
        for potential_child in list(self.events.events.values()):
            if potential_child.parent_id != parent_event.token_id:
                continue

            self.cancel_subtree(potential_child, CancelTaskFinishModeException(task_error=e.task_error))

        if parent_event.future:
            # cancel the task for this event
            if config.current.parallel_processing != "process":
                LOG.warning(f"Cancel task on boundary event was requested, "
                            f"but the ADHESIVE_PARALLEL_PROCESSING is not set "
                            f"to 'process', but '{config.current.parallel_processing}'. "
                            f"The result of the task is ignored, but the thread "
                            f"keeps running in the background.")

            parent_event.future.cancel()
            # FIXME: hack. It seems that the `set_exception` is not needed, but
            # if cancel isn't called, the process isn't terminated. If it's called
            # after set_exception, again it isn't terminated.
            try:
                parent_event.future.set_exception(e)
            except Exception:
                pass

        self.events.transition(
            event=parent_event,
            state=ActiveEventState.DONE_CHECK,
            data=e,
        )

    @property
    def are_active_futures(self) -> bool:
        if not self.futures:
            return False

        for future in self.futures:
            # future.running()
            with cast(Any, future)._condition:
                if cast(Any, future)._state in ['RUNNING', 'PENDING']:
                    return True

        return False

    def handle_task_error(self,
                          task_error: TaskError) -> None:
        handling_event: ActiveEvent = task_error.failed_event

        if not isinstance(handling_event.task, ProcessTask):
            handling_event = self.get_parent(handling_event.token_id)

        while not cast(ProcessTask, handling_event.task).error_task and \
                handling_event != self.root_event:
            handling_event = self.get_parent(handling_event.token_id)

        if handling_event == self.root_event:
            self.root_error_handling(task_error)
            return

        self.task_error_handling(handling_event, task_error)

    def root_error_handling(self,
                            task_error: TaskError) -> None:
        """
        Error handling that happens when no other task had error handling
        configured, and the error event bubbled to the top.
        """
        self.cancel_subtree(self.root_event,
                            CancelTaskFinishModeException(
                                root_node=True,
                                task_error=task_error))
        raise_unhandled_exception(task_error)

    def task_error_handling(self,
                            event: ActiveEvent,
                            task_error: TaskError) -> None:
        """
        Error handling that happens on a task that has at least one associated
        boundary event.
        """
        if not isinstance(event.task, ProcessTask):
            raise Exception(f"Adhesive BUG: error in {event} handling. Called on a wrong task type.")

        process_task = cast(ProcessTask, event.task)

        if not process_task.error_task:
            raise Exception(f"Adhesive BUG: error in {event} handling. Called on a process task "
                            f"without an associated error boundary event.")

        new_event = self.clone_event(event, process_task.error_task)
        new_event.context.data._error = task_error.error

        self.cancel_subtree(event, CancelTaskFinishModeException(root_node=True, task_error=task_error))

    def process_event(self, event: ActiveEvent, data: Any) -> None:
        # if there is no processing needed, we skip to routing
        if isinstance(event.task, Event) or \
                isinstance(event.task, NonWaitingGateway):
            self.events.transition(
                event=event,
                state=ActiveEventState.ROUTING,
                data=event.context,
            )
            return

        # if we need to wait, we wait.
        if isinstance(event.task, WaitingGateway):
            self.events.transition(
                event=event,
                state=ActiveEventState.WAITING
            )
            return

        # normally we shouldn't wait for tasks, since it's counter BPMN, so
        # we allow configuring waiting for it.
        if self.config.wait_tasks and (
                isinstance(event.task, ProcessTask) or
                isinstance(event.task, Process)
        ):
            self.events.transition(
                event=event,
                state=ActiveEventState.WAITING
            )
            return

        if isinstance(event.task, ProcessTask) and \
                cast(ProcessTask, event.task).deduplicate is not None:
            self.events.transition(
                event=event,
                state=ActiveEventState.WAITING
            )

            return

        self.events.transition(
            event=event,
            state=ActiveEventState.RUNNING
        )

    def get_process(self,
                    event: ActiveEvent) -> Process:
        if not event.parent_id:
            return self.adhesive_process.process

        try:
            process = cast(Process, self.events[event.parent_id].task)
        except Exception:
            LOG.error("Unable to find parent process for {}", event)

        return process

    def wait_task(self, event: ActiveEvent, data: Any) -> None:
        # is another waiting task already present?
        other_waiting, tasks_waiting_count = self.events.get_other_task_waiting(event)

        potential_predecessors = list(map(
            lambda e: e.task,
            filter(lambda e: is_potential_predecessor(self, event, e),
                   self.events.iterate(ACTIVE_STATES))))

        # if we have a deduplication event, and there are other events in flight
        # for the same deduplication id, this event will stay in WAIT.
        if other_waiting and \
                other_waiting is event and \
                other_waiting.deduplication_id is not None:
            return

        if other_waiting:
            new_data = ExecutionData.merge(other_waiting.context.data, event.context.data)
            other_waiting.context.data = new_data

            self.events.transition(
                event=event,
                state=ActiveEventState.DONE
            )

        # this should return for initial loops
        process = self.get_process(event)

        # if we have predecessors, we stay in waiting
        predecessor_id = process.are_predecessors(event.task, potential_predecessors)

        if predecessor_id:
            LOG.debug(f"Predecessor found for {event}. Waiting for {predecessor_id}.")
            return None

        if not other_waiting:
            self.events.transition(event=event,
                                   state=ActiveEventState.RUNNING)
            return

        if other_waiting.state == ActiveEventState.WAITING and \
                tasks_waiting_count == 1:
            self.events.transition(event=other_waiting,
                                   state=ActiveEventState.RUNNING)
            return

        LOG.debug("Waiting for none, yet staying in WAITING?")
        return None

    def run_task(self, event: ActiveEvent, data: Any) -> None:
        if event.loop_type == ActiveLoopType.INITIAL:
            loop_controller.evaluate_initial_loop(event, self.clone_event)

            if event.loop_type == ActiveLoopType.INITIAL_EMPTY:
                self.events.transition(event=event,
                                       state=ActiveEventState.ROUTING,
                                       data=event.context)
            else:
                self.events.transition(event=event,
                                       state=ActiveEventState.DONE)

            return

        self.events.clear_waiting_deduplication(event=event)

        # FIXME: probably this try/except should be longer than just the LOG
        try:
            LOG.info(yellow("Run  ") + yellow(event.context.task_name, bold=True))
        except Exception as e:
            raise Exception(f"Failure on {event.context.task_name}", e)

        # When we start running, we must register now timer events against the
        # schedule
        if isinstance(event.task, ProcessTask) and event.task.timer_events:
            timers: Set[ActiveTimer] = set()
            self.active_timers[event.token_id] = timers

            for timer_event in event.task.timer_events:
                timers.add(create_active_timer(
                    fire_timer=self.fire_timer,
                    parent_token=event,
                    boundary_event_definition=timer_event))

        if isinstance(event.task, Process):
            for start_task in event.task.start_events.values():
                if isinstance(start_task, ProcessTask) and start_task.loop:
                    # we start a loop by firing the loop events, and consume this event.
                    loop_controller.create_loop(event,
                                                self.clone_event,
                                                start_task,
                                                parent_id=event.token_id)
                else:
                    self.clone_event(event, start_task, parent_id=event.token_id)

            return None

        if isinstance(event.task, Task):
            if event.task.id not in self.tasks_impl:
                error_message = f"BUG: Task id {event.task.id} ({event.task.name}) " \
                                f"not found in implementations {self.tasks_impl}"

                LOG.fatal(red(error_message, bold=True))
                raise Exception(error_message)

            future: Future[ExecutionToken] = ProcessExecutor.pool.schedule(
                self.tasks_impl[event.task.id].invoke,
                args=(copy_event(event),))
            self.futures[future] = event.token_id
            event.future = future
            return None

        if isinstance(event.task, ScriptTask):
            future = ProcessExecutor.pool.schedule(
                call_script_task,
                args=(copy_event(event),))
            self.futures[future] = event.token_id
            event.future = future
            return None

        if isinstance(event.task, UserTask):
            future = Future()
            self.futures[future] = event.token_id
            event.future = future

            assert self.ut_provider

            self.ut_provider.register_event(self, event)

            return None

        self.events.transition(
            event=event,
            state=ActiveEventState.ROUTING,
            data=event.context,
        )

    def route_task(self,
                   event: ActiveEvent,
                   data: Any) -> None:

        try:
            # Since we're in routing, we passed the actual running, so we need to update the
            # context with the new execution token.
            event.context = data

            # we don't route, since we have live events created from the
            # INITIAL loop type
            if event.loop_type == ActiveLoopType.INITIAL:
                self.events.transition(event=event,
                                       state=ActiveEventState.DONE)
                return

            if loop_controller.next_conditional_loop_iteration(event, self.clone_event):
                # obviously the done checks are not needed, since we're
                # still in the loop
                self.events.transition(event=event,
                                       state=ActiveEventState.DONE)

                return

            process = self.get_process(event)

            outgoing_edges = GatewayController.compute_outgoing_edges(process, event)

            for outgoing_edge in outgoing_edges:
                target_task = process.tasks[outgoing_edge.target_id]
                if isinstance(target_task, ProcessTask) and target_task.loop:
                    # we start a loop by firing the loop events, and consume this event.
                    loop_controller.create_loop(event, self.clone_event, target_task)
                else:
                    self.clone_event(event, target_task)

            self.events.transition(
                event=event,
                state=ActiveEventState.DONE_CHECK,
                data=OutgoingEdgesFinishMode(outgoing_edges)
            )
        except Exception as e:
            self.handle_task_error(
                TaskError(
                    error=traceback.format_exc(),
                    exception=e,
                    failed_event=event
                ))

    def done_check(self,
                   event: ActiveEvent,
                   finish_mode: TaskFinishMode) -> None:
        """
        Runs the handling for an event that is considered an end
        event in its parent.
        :param _event:
        :return:
        """
        if isinstance(finish_mode, OutgoingEdgesFinishMode) and finish_mode.outgoing_edges or \
           isinstance(finish_mode, CancelTaskFinishModeException) and not finish_mode.root_node:
            self.events.transition(
                event=event,
                state=ActiveEventState.DONE,
            )
            return None

        # we should check all the WAITING processes if they finished.
        event_count: Dict[ExecutableNode, int] = dict()
        waiting_events: List[ActiveEvent] = list()

        process = self.get_process(event)

        for id, self_event in self.events.events.items():
            if self_event.state in DONE_STATES:
                continue

            if self_event.task.process_id != process.id:
                continue

            event_count[self_event.task] = event_count.get(self_event.task, 0) + 1

            if self_event.state == ActiveEventState.WAITING:
                waiting_events.append(self_event)

        for waiting_event in waiting_events:
            if event_count[waiting_event.task] > 1:
                continue

            if waiting_event.task.process_id != process.id:
                continue

            potential_predecessors = list(map(
                lambda e: e.task,
                filter(lambda e: is_potential_predecessor(self, waiting_event, e), self.events.events.values())))

            if not process.are_predecessors(waiting_event.task, potential_predecessors):
                self.events.transition(
                    event=waiting_event,
                    state=ActiveEventState.RUNNING,
                )

        # check sub-process termination
        found = False
        for ev in self.events.excluding(ActiveEventState.DONE):
            if ev.parent_id == event.parent_id and ev != event:
                found = True
                break

        # we merge into the parent event if it's an end state.
        if event.parent_id is not None and \
                not isinstance(finish_mode, CancelTaskFinishModeException):
            self.events[event.parent_id].context.data = ExecutionData.merge(
                self.events[event.parent_id].context.data,
                event.context.data
            )

            if not found and \
                    event.parent_id == self.root_event.token_id and \
                    self.are_active_futures:
                self.events.transition(
                    event=event,
                    state=ActiveEventState.DONE
                )
                return None  # ==> if we still have running futures, we don't kill the main process

            if not found:
                parent_event = self.events[event.parent_id]
                self.events.transition(
                    event=parent_event,
                    state=ActiveEventState.ROUTING,
                    data=parent_event.context
                )

        self.events.transition(
            event=event,
            state=ActiveEventState.DONE
        )

    def done_task(self, event: ActiveEvent, data: Any) -> None:
        # we keep track how many deduplication events are in flight
        if event.deduplication_id:
            self.events.unregister_deduplication_event(event)

        self.unregister_event(event)

    def clone_event(self,
                    old_event: ActiveEvent,
                    task: ExecutableNode,
                    parent_id: Optional[str] = None) -> ActiveEvent:

        if parent_id is None:
            parent_id = old_event.parent_id

        event = old_event.clone(task, parent_id)

        if isinstance(task, ProcessTask):
            event.deduplication_id = get_deduplication_id(event)

        self.register_event(event)

        return event


from adhesive.model.process_validator import _validate_tasks
