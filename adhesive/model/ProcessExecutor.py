import collections
import logging
import os
import sys
import time
import traceback
import uuid
from concurrent.futures import Future
from threading import Lock
from typing import Optional, Dict, TypeVar, Any, List, Tuple, Union

import adhesive
from adhesive import logredirect, ExecutionMessageEvent, ExecutionMessageCallbackEvent
from adhesive.consoleui.color_print import green, red, yellow, white
from adhesive.execution import token_utils
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from adhesive.execution.ExecutionData import ExecutionData
from adhesive.execution.ExecutionLane import ExecutionLane
from adhesive.execution.ExecutionLoop import loop_id
from adhesive.execution.ExecutionToken import ExecutionToken
from adhesive.execution.call_script_task import call_script_task
from adhesive.graph.Event import Event
from adhesive.graph.Gateway import Gateway
from adhesive.graph.MessageEvent import MessageEvent
from adhesive.graph.NonWaitingGateway import NonWaitingGateway
from adhesive.graph.ProcessNode import ProcessNode
from adhesive.graph.ScriptTask import ScriptTask
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.graph.WaitingGateway import WaitingGateway
from adhesive.model.GatewayController import GatewayController
from adhesive.model.MessageEventExecutor import MessageEventExecutor
from adhesive.model.ProcessExecutorConfig import ProcessExecutorConfig
from adhesive.model.generate_methods import display_unmatched_items
from adhesive.storage.ensure_folder import get_folder

T = TypeVar('T')

import concurrent.futures

from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.ProcessTask import ProcessTask
from adhesive.graph.Process import Process
from adhesive.graph.Lane import Lane
from adhesive.execution.ExecutionTask import ExecutionTask
from adhesive import config

from adhesive.model import lane_controller
from adhesive.model import loop_controller

from adhesive.model.ActiveEventStateMachine import ActiveEventState
from adhesive.model.ActiveLoopType import ActiveLoopType
from adhesive.model.ActiveEvent import ActiveEvent, PRE_RUN_STATES, is_potential_predecessor, copy_event, DONE_STATES
from adhesive.model.AdhesiveProcess import AdhesiveProcess

import signal


LOG = logging.getLogger(__name__)


def raise_unhandled_exception(_ev):
    log_path = get_folder(_ev.data['failed_event'])

    LOG.error(red("Process execution failed. Unhandled error."))

    if logredirect.is_enabled:
        stdout_file = os.path.join(log_path, "stdout")
        if os.path.isfile(stdout_file):
            with open(stdout_file) as f:
                print(white("STDOUT:", bold=True))
                print(white(f.read()))
        else:
            print(white("STDOUT:", bold=True) + white(" not found"))

        stderr_file = os.path.join(log_path, "stderr")
        if os.path.isfile(stderr_file):
            with open(stderr_file) as f:
                print(red("STDERR:", bold=True))
                print(red(f.read()), file=sys.stderr)
        else:
            print(red("STDERR:", bold=True) + red(" not found"))

    print(red("Exception:", bold=True))
    print(red(_ev.data['error']), file=sys.stderr)

    sys.exit(1)


class ProcessExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool_size = int(config.current.pool_size) if config.current.pool_size else None
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=pool_size) \
            if config.current.parallel_processing == "process" \
            else concurrent.futures.ThreadPoolExecutor(max_workers=pool_size)

    def __init__(self,
                 process: AdhesiveProcess,
                 ut_provider: Optional['UserTaskProvider'] = None,
                 wait_tasks: bool = True) -> None:
        self.adhesive_process = process
        self.tasks_impl: Dict[str, ExecutionTask] = dict()
        self.mevent_impl: Dict[str, ExecutionMessageEvent] = dict()
        self.mevent_callback_impl: Dict[str, ExecutionMessageCallbackEvent] = dict()

        # A dictionary of events that are currently active. This is just to find out
        # the parent of an event, since from it we can also derive the current parent
        # process.
        self.events: Dict[str, ActiveEvent] = dict()
        self.futures: Dict[Any, str] = dict()
        self.ut_provider = ut_provider

        self.enqueued_events: List[Tuple[Event, Any]] = list()
        self.enqueued_events_lock = Lock()

        self.config = ProcessExecutorConfig(wait_tasks=wait_tasks)
        self.execution_id = str(uuid.uuid4())

    # FIXME: reintroduce async? Since the tasks are executing on the
    # thread pool without async, they shouldn't impact log redirection.
    def execute(self,
                initial_data=None) -> ExecutionData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        process = self.adhesive_process.process
        self.tasks_impl: Dict[str, ExecutionTask] = dict()

        self._validate_tasks(process)

        if adhesive.config.current.verify_mode:
            return ExecutionData(initial_data)

        signal.signal(signal.SIGUSR1, self.print_state)

        # since the workspaces are allocated by lanes, we need to ensure
        # our default lane is existing.
        lane_controller.ensure_default_lane(self.adhesive_process)

        # FIXME: it's getting pretty crowded
        token_id = str(uuid.uuid4())
        process_context = ExecutionToken(
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
        fake_event.token_id = None  # FIXME: why

        root_event = self.clone_event(fake_event, process)
        self.root_event = root_event

        root_event.state.after_enter(ActiveEventState.ERROR, raise_unhandled_exception)

        self.start_message_event_listeners(root_event=root_event)
        self.execute_process_event_loop()

        return root_event.context.data

    def print_state(self, x, y) -> None:
        print("Events:")
        for event in self.events.values():
            print(event)

        print("Futures:")
        for f in self.futures:
            print(f)

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

        for mevent_id, mevent in self.mevent_impl.items():
            executor = MessageEventExecutor(
                root_event=root_event,
                message_event=self.adhesive_process.process.message_events[mevent_id],
                execution_message_event=mevent,
                enqueue_event=self.enqueue_event)

            self.futures[executor.future] = "__message_executor"

    def execute_process_event_loop(self) -> None:
        """
        Main event loop. Processes the events from a process until no more
        events are available.  For example an event is the start of the
        process. The events are then creating futures (i.e. actual stuff that's
        being processed) that in turn might generate new events.
        :return: data from the last execution token.
        """
        while self.events or self.futures:
            pending_events = list(filter(lambda e: e.state.state == ActiveEventState.NEW,
                                         self.events.values()))

            # we ensure we have only events to be processed
            while pending_events:
                # except for new processes, and processes that are running with futures
                # the states should transition automatically.
                processed_events = list(pending_events)
                for pending_event in processed_events:
                    pending_event.state.process()

                pending_events = list(filter(lambda e: e.state.state == ActiveEventState.NEW,
                                             self.events.values()))

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
                    for ev in self.events.values():
                        if ev.parent_id == self.root_event.token_id and ev != self.root_event:
                            found = True
                            break

                    if not found:
                        self.root_event.state.route(self.root_event.context)

                    continue

                try:
                    context = future.result()
                    self.events[token_id].state.route(context)
                except Exception as e:
                    self.events[token_id].state.error({
                        "error": traceback.format_exc(),
                        "failed_event": self.events[token_id]
                    })

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
        parent = self.events[event.parent_id]

        return parent

    def _validate_tasks(self,
                        process: Process,
                        missing_dict: Optional[Dict[str, Union[ProcessTask, Lane]]]=None) -> None:
        """
        Recursively traverse the graph, and print to the user if it needs to implement
        some tasks.

        :param process:
        :return:
        """
        if missing_dict is not None:
            unmatched_items = missing_dict
        else:
            unmatched_items: Dict[str, Union[ProcessTask, Lane, MessageEvent]] = dict()

        for task_id, task in process.tasks.items():
            if isinstance(task, SubProcess):
                self._validate_tasks(task, unmatched_items)
                continue

            # gateways don't have associated tasks with them.
            if isinstance(task, Event) or \
                    isinstance(task, Gateway):
                continue

            if isinstance(task, ScriptTask):
                if task.language in ("python", "text/python", "python3", "text/python3"):
                    continue

                raise Exception(f"Unknown script task language: {task.language}. Only python and "
                                f"text/python are supported.")

            adhesive_task = self._match_task(task)

            if not adhesive_task:
                unmatched_items[f"task:{task.name}"] = task
                continue

            self.tasks_impl[task_id] = adhesive_task
            adhesive_task.used = True

        for lane_id, lane in process.lanes.items():
            lane_definition = self._match_lane(lane.name)

            if not lane_definition:
                unmatched_items[f"lane:{lane.name}"] = lane
                continue

            lane_definition.used = True

        for mevent_id, message_event in process.message_events.items():
            message_event_definition = self._match_message_event(message_event.name)

            if not message_event_definition:
                unmatched_items[f"message_event:{message_event.name}"] = message_event
                continue

            if isinstance(message_event_definition, ExecutionMessageEvent):
                self.mevent_impl[mevent_id] = message_event_definition
            else:
                self.mevent_callback_impl[mevent_id] = message_event_definition

            message_event_definition.used = True

        if missing_dict is not None:  # we're not the root call, we're done
            return

        # The default lane is not explicitly present in the process. If we have
        # an implementation, we don't want to see it as an unused warning.
        lane_definition = self._match_lane("default")
        # if we don't have a definition, the lane_controller will dynamically add
        # it.
        # FIXME: probably it's better if the lane definition would be here.
        if lane_definition:
            lane_definition.used = True

        for task_definition in self.adhesive_process.task_definitions:
            if not task_definition.used:
                LOG.warning(f"Unused task: {task_definition}")

        for lane_definition in self.adhesive_process.lane_definitions:
            if not lane_definition.used:
                LOG.warning(f"Unused lane: {lane_definition}")

        for message_event in self.adhesive_process.message_definitions:
            if not message_event.used:
                LOG.warning(f"Unused message: {message_event}")

        for message_event_callback in self.adhesive_process.message_callback_definitions:
            if not message_event_callback.used:
                LOG.warning(f"Unused message: {message_event_callback}")

        if unmatched_items:
            display_unmatched_items(unmatched_items.values())
            sys.exit(1)

    def _match_task(self, task: ProcessTask) -> Optional[ExecutionBaseTask]:
        for task_definition in self.adhesive_process.task_definitions:
            if token_utils.matches(task_definition.re_expressions, task.name) is not None:
                return task_definition

        return None

    def _match_lane(self, lane_name: str) -> Optional[ExecutionLane]:
        for lane_definition in self.adhesive_process.lane_definitions:
            if token_utils.matches(lane_definition.re_expressions, lane_name) is not None:
                return lane_definition

        return None

    def _match_message_event(self, message_event_name: str) -> Optional[Union[ExecutionMessageEvent, ExecutionMessageCallbackEvent]]:
        for message_definition in self.adhesive_process.message_definitions:
            if token_utils.matches(message_definition.re_expressions, message_event_name) is not None:
                return message_definition

        for message_definition in self.adhesive_process.message_callback_definitions:
            if token_utils.matches(message_definition.re_expressions, message_event_name) is not None:
                return message_definition

        return None

    def clone_event(self,
                    old_event: ActiveEvent,
                    task: ProcessTask,
                    parent_id: Optional[str] = None) -> ActiveEvent:

        if parent_id is None:
            parent_id = old_event.parent_id

        event = old_event.clone(task, parent_id)
        self.register_event(event)

        if parent_id is None:
            process = self.adhesive_process.process
        else:
            process = self.events[parent_id].task

        def process_event(_event) -> ActiveEventState:
            # if there is no processing needed, we skip to routing
            if isinstance(event.task, Event) or \
                    isinstance(event.task, NonWaitingGateway):
                return event.state.route(event.context)

            # if we need to wait, we wait.
            if isinstance(event.task, WaitingGateway):
                return event.state.wait_check()

            # normally we shouldn't wait for tasks, since it's counter BPMN, so
            # we allow configuring waiting for it.
            if self.config.wait_tasks and (
                    isinstance(event.task, ProcessTask) or
                    isinstance(event.task, Process)
            ):
                return event.state.wait_check()

            return event.state.run()

        def get_other_task_waiting(source: ActiveEvent) -> \
                Tuple[Optional[ActiveEvent], int]:
            """
            Get any other task that is waiting to be executed on the
            same task that's waiting.
            :param source:
            :return:
            """
            result = None
            count = 0

            if source.context.loop and \
                    source.context.loop.task.id == source.task.id and \
                    source.context.loop.index >= 0:
                return result, count

            for ev in self.events.values():
                if ev == source:
                    continue

                if ev.task == source.task and \
                        ev.state.state in PRE_RUN_STATES and \
                        loop_id(ev) == loop_id(source):
                    if not result:
                        result = ev

                    count += 1

            return result, count

        def wait_task(_event) -> Optional[ActiveEventState]:
            # is another waiting task already present?
            other_waiting, tasks_waiting_count = get_other_task_waiting(event)

            potential_predecessors = list(map(
                lambda e: e.task,
                filter(lambda e: is_potential_predecessor(self, event, e), self.events.values())))

            if other_waiting:
                new_data = ExecutionData.merge(other_waiting.context.data, event.context.data)
                other_waiting.context.data = new_data

                event.state.done()

            # this should return for initial loops

            # if we have predecessors, we stay in waiting
            if process.are_predecessors(event.task, potential_predecessors):
                return None

            if not other_waiting:
                return event.state.run()

            if other_waiting.state.state == ActiveEventState.WAITING and \
                    tasks_waiting_count == 1:
                other_waiting.state.run()

            return None

        def run_task(_event) -> None:
            if event.loop_type == ActiveLoopType.INITIAL:
                loop_controller.evaluate_initial_loop(event, self.clone_event)

                if event.loop_type == ActiveLoopType.INITIAL_EMPTY:
                    event.state.route(event.context)
                else:
                    event.state.done()

                return

            # FIXME: probably this try/except should be longer than just the LOG
            try:
                LOG.info(yellow("Run  ") + yellow(event.context.task_name, bold=True))
            except Exception as e:
                raise Exception(f"Failure on {event.context.task_name}", e)

            if isinstance(event.task, Process):
                for start_task in event.task.start_events.values():
                    # this automatically registers our events for execution
                    self.clone_event(event, start_task, parent_id=event.token_id)
                return

            if isinstance(event.task, Task):
                if event.task.id not in self.tasks_impl:
                    error_message = f"BUG: Task id {event.task.id} ({event.task.name}) " \
                                    f"not found in implementations {self.tasks_impl}"

                    LOG.fatal(red(error_message, bold=True))
                    raise Exception(error_message)

                future = ProcessExecutor.pool.submit(
                    self.tasks_impl[event.task.id].invoke,
                    copy_event(event))
                self.futures[future] = event.token_id
                event.future = future
                return

            if isinstance(event.task, ScriptTask):
                future = ProcessExecutor.pool.submit(
                    call_script_task,
                    copy_event(event))
                self.futures[future] = event.token_id
                event.future = future
                return

            if isinstance(event.task, UserTask):
                future = Future()
                self.futures[future] = event.token_id
                event.future = future

                self.ut_provider.register_event(self, event)

                return

            return event.state.route(event.context)

        def log_running_done(_event):
            if _event.target_state == ActiveEventState.ERROR:
                LOG.info(red("Failed ") + red(event.context.task_name, bold=True))
                return

            if event.loop_type in (ActiveLoopType.INITIAL, ActiveLoopType.INITIAL_EMPTY):
                return

            LOG.info(green("Done ") + green(event.context.task_name, bold=True))

        def error_parent_task(event, e):
            if event.parent_id in self.events:
                parent_event = self.get_parent(event.token_id)

                # we move the parent into error
                parent_event.state.error(e)

                # FIXME: not sure if this is enough.
                for potential_child in list(self.events.values()):
                    if potential_child.parent_id != event.parent_id:
                        continue

                    # potential_child.state.error(_event.data)
                    potential_child.state.done()

        def error_task(_event) -> None:
            # if we have a boundary error task, we use that one for processing.
            if event.task.error_task:
                new_event = self.clone_event(event, event.task.error_task)
                new_event.context.data._error = _event.data['error']

                if event.task.error_task.cancel_activity:
                    event.state.done_check(None)
                else:
                    event.state.route()

                return

            error_parent_task(event, _event.data)
            # event.state.done_check(None)  # we kill the current event

        def route_task(_event) -> None:
            try:
                # Since we're in routing, we passed the actual running, so we need to update the
                # context with the new execution token.
                event.context = _event.data

                # we don't route, since we have live events created from the
                # INITIAL loop type
                if event.loop_type == ActiveLoopType.INITIAL:
                    event.state.done()
                    return

                if loop_controller.next_conditional_loop_iteration(event, self.clone_event):
                    # obviously the done checks are not needed, since we're
                    # still in the loop
                    event.state.done()

                    return

                outgoing_edges = GatewayController.compute_outgoing_edges(process, event)

                for outgoing_edge in outgoing_edges:
                    target_task = process.tasks[outgoing_edge.target_id]
                    if hasattr(target_task, "loop") and target_task.loop:
                        # we start a loop by firing the loop events, and consume this event.
                        loop_controller.create_loop(event, self.clone_event, target_task)
                    else:
                        self.clone_event(event, target_task)

                event.state.done_check(outgoing_edges)
            except Exception as e:
                error_parent_task(event, {
                    "error": traceback.format_exc(),
                    "failed_event": self.events[event.token_id]
                })

        def done_check(_event) -> None:
            outgoing_edges = _event.data

            if not outgoing_edges:
                return event.state.done_end_task()

            return event.state.done()

        def done_end_task(_event) -> None:
            # we should check all the WAITING processes if they finished.
            event_count: Dict[ProcessTask, int] = dict()
            waiting_events: List[ActiveEvent] = list()

            for id, self_event in self.events.items():
                if self_event.state.state in DONE_STATES:
                    continue

                if self_event.task.process_id != process.id:
                    continue

                event_count[self_event.task] = event_count.get(self_event.task, 0) + 1

                if self_event.state.state == ActiveEventState.WAITING:
                    waiting_events.append(self_event)

            for waiting_event in waiting_events:
                if event_count[waiting_event.task] > 1:
                    continue

                if waiting_event.task.process_id != process.id:
                    continue

                potential_predecessors = list(map(
                    lambda e: e.task,
                    filter(lambda e: is_potential_predecessor(self, waiting_event, e), self.events.values())))

                if not process.are_predecessors(waiting_event.task, potential_predecessors):
                    waiting_event.state.run()

            # check sub-process termination
            found = False
            for ev in self.events.values():
                if ev.parent_id == event.parent_id and ev != event:
                    found = True
                    break

            if not found and parent_id == self.root_event.token_id and self.futures:
                event.state.done()
                return  # ==> if we still have running futures, we don't kill the main process

            # we merge into the parent event if it's an end state.
            if parent_id is not None:
                self.events[parent_id].context.data = ExecutionData.merge(
                    self.events[parent_id].context.data,
                    event.context.data
                )

                if not found:
                    parent_event = self.events[parent_id]
                    parent_event.state.route(parent_event.context)

            event.state.done()

        def done_task(_event) -> None:
            self.unregister_event(event)

        event.state.after_enter(ActiveEventState.PROCESSING, process_event)
        event.state.after_enter(ActiveEventState.WAITING, wait_task)
        event.state.after_enter(ActiveEventState.RUNNING, run_task)
        event.state.after_leave(ActiveEventState.RUNNING, log_running_done)
        event.state.after_enter(ActiveEventState.ERROR, error_task)
        event.state.after_enter(ActiveEventState.ROUTING, route_task)
        event.state.after_enter(ActiveEventState.DONE_CHECK, done_check)
        event.state.after_enter(ActiveEventState.DONE_END_TASK, done_end_task)
        event.state.after_enter(ActiveEventState.DONE, done_task)

        return event
