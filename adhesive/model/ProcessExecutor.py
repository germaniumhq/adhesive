import logging
import copy
import os
import sys
import traceback
import uuid

from concurrent.futures import Future
from typing import Set, Optional, Dict, TypeVar, Any, List, Tuple, Union

from adhesive import logredirect
from adhesive.consoleui.color_print import green, red, yellow, white
from adhesive.graph.BoundaryEvent import BoundaryEvent
from adhesive.graph.Gateway import Gateway, NonWaitingGateway, WaitingGateway
from adhesive.graph.ScriptTask import ScriptTask
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.model.GatewayController import GatewayController
from adhesive.model.ProcessExecutorConfig import ProcessExecutorConfig
from adhesive.model.generate_methods import display_unmatched_items
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from adhesive.execution.ExecutionLane import ExecutionLane
from adhesive.execution.ExecutionToken import ExecutionToken
from adhesive.execution.ExecutionData import ExecutionData
from adhesive.execution.ExecutionLoop import ExecutionLoop, parent_loop_id, loop_id
from adhesive.execution.call_script_task import call_script_task
from adhesive.execution import token_utils
from adhesive.storage.ensure_folder import get_folder

T = TypeVar('T')

import concurrent.futures

from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Process import Process
from adhesive.graph.Lane import Lane
from adhesive.execution.ExecutionTask import ExecutionTask
from adhesive import config

from adhesive.model import lane_controller
from adhesive.model import loop_controller

from adhesive.model.ActiveEventStateMachine import ActiveEventState
from adhesive.model.ActiveLoopType import ActiveLoopType
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.AdhesiveProcess import AdhesiveProcess

LOG = logging.getLogger(__name__)

DONE_STATES = {
    ActiveEventState.DONE_CHECK,
    ActiveEventState.DONE_END_TASK,
    ActiveEventState.DONE,
}

ACTIVE_STATES = {
    ActiveEventState.NEW,
    ActiveEventState.PROCESSING,
    ActiveEventState.WAITING,
    ActiveEventState.RUNNING,
    ActiveEventState.ERROR,
    ActiveEventState.ROUTING,
}

# When waiting for predecessors it only makes sense to collapse events
# into ActiveEvents only when the event is not already running.
PRE_RUN_STATES = {
    ActiveEventState.NEW,
    ActiveEventState.PROCESSING,
    ActiveEventState.WAITING,
}


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


def is_predecessor(event, e) -> bool:
    if e.state.state not in ACTIVE_STATES:
        return False

    if e.task == event.task:
        return False

    if event.context.loop:
        # if we are in a loop and the other predecessor is inside
        # a loop of its own, we need to check if it's in the same
        # loop as ours
        if e.task.loop:
            return parent_loop_id(e) == loop_id(event)

        # we check if we are in the same loop. each iteration
        # will have its own loop id.
        if loop_id(e) != loop_id(event):
            return False

    return True


def deep_copy_event(e: ActiveEvent) -> ActiveEvent:
    """
    We deepcopy everything except the workspace.
    :param e:
    :return:
    """
    workspace = e.context.workspace
    e.context.workspace = None
    result = copy.deepcopy(e)

    result.context.workspace = workspace

    return result


def noop_copy_event(e: ActiveEvent) -> ActiveEvent:
    return e


copy_event = noop_copy_event \
        if config.current.parallel_processing == "process" else \
        deep_copy_event


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
        self.process = process
        self.tasks_impl: Dict[str, ExecutionTask] = dict()

        # A dictionary of events that are currently active. This is just to find out
        # the parent of an event, since from it we can also derive the current parent
        # process.
        self.events: Dict[str, ActiveEvent] = dict()
        self.futures: Dict[Any, str] = dict()
        self.ut_provider = ut_provider

        self.config = ProcessExecutorConfig(wait_tasks=wait_tasks)
        self.execution_id = str(uuid.uuid4())

    # FIXME: remove async. async is's not possible since it would thread switch
    # and completely screw up log redirection.
    def execute(self,
                      initial_data=None) -> ExecutionData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        process = self.process.process
        self.tasks_impl: Dict[str, ExecutionTask] = dict()

        self._validate_tasks(process)

        # since the workspaces are allocated by lanes, we need to ensure
        # our default lane is existing.
        lane_controller.ensure_default_lane(self.process)

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
        root_event.state.after_enter(ActiveEventState.ERROR, raise_unhandled_exception)

        self.execute_process_event_loop()

        return root_event.context.data

    def execute_process_event_loop(self) -> None:
        """
        Main event loop. Processes the events from a process until no more
        events are available.  For example an event is the start of the
        process. The events are then creating futures (i.e. actual stuff that's
        being processed) that in turn might generate new events.
        :return: data from the last execution token.
        """
        old_done_futures = set()
        #old_pending_events = set(self.events.keys())

        while self.events:
            pending_events = filter(lambda e: e.state.state == ActiveEventState.NEW,
                                    self.events.values())

            # except for new processes, and processes that are running with futures
            # the states should transition automatically.
            processed_events = list(pending_events)
            for pending_event in processed_events:
                pending_event.state.process()

            done_futures, not_done_futures = concurrent.futures.wait(
                self.futures.keys(),
                return_when=concurrent.futures.FIRST_COMPLETED,
                timeout=5)

            #if old_done_futures - done_futures:
            #    broken_futures = old_done_futures - done_futures
            #    LOG.warn(f"Some of the old futures are still present: {broken_futures}")
            #
            #old_done_futures = set(done_futures)

            for future in done_futures:
                token_id = self.futures[future]
                try:
                    context = future.result()
                    self.events[token_id].state.route(context)
                except Exception as e:
                    self.events[token_id].state.error({
                        "error": traceback.format_exc(),
                        "failed_event": self.events[token_id]
                    })

            old_pending_events = set(self.events.keys())

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

        lane_controller.allocate_workspace(self.process, event)

        self.events[event.token_id] = event

        return event

    def unregister_event(self,
                         event: ActiveEvent) -> None:
        if event.token_id not in self.events:
            raise Exception(f"{event} not found in events. Either the event was "
                            f"already terminated, either it was not registered.")

        lane_controller.deallocate_workspace(self.process, event)

        LOG.debug(f"Unregister {event}")

        del self.events[event.token_id]

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
                        missing_dict: Optional[Dict[str, Union[BaseTask, Lane]]]=None) -> None:
        """
        Recursively traverse the graph, and print to the user if it needs to implement
        some tasks.

        :param process:
        :return:
        """
        if missing_dict:
            unmatched_items = missing_dict
        else:
            unmatched_items: Dict[str, Union[BaseTask, Lane]] = dict()

        for task_id, task in process.tasks.items():
            if isinstance(task, SubProcess):
                self._validate_tasks(task, unmatched_items)
                continue

            # gateways don't have associated tasks with them.
            if isinstance(task, StartEvent) or \
                    isinstance(task, EndEvent) or \
                    isinstance(task, Gateway) or \
                    isinstance(task, BoundaryEvent):
                continue

            if isinstance(task, ScriptTask):
                if task.language in ("python", "text/python"):
                    continue

                raise Exception(f"Unknown script task language: {task.language}. Only python and "
                                f"text/python are supported.")

            adhesive_task = self._match_task(task)

            if not adhesive_task:
                unmatched_items[f"task:{task.name}"] = task
                continue

            self.tasks_impl[task_id] = adhesive_task

        for lane_id, lane in process.lanes.items():
            lane_definition = self._match_lane(lane)

            if not lane_definition:
                unmatched_items[f"lane:{lane.name}"] = lane

        if unmatched_items and missing_dict is None:  # we're the root call
            display_unmatched_items(unmatched_items.values())
            sys.exit(1)

    def _match_task(self, task: BaseTask) -> Optional[ExecutionBaseTask]:
        for task_definition in self.process.task_definitions:
            if token_utils.matches(task_definition.re_expressions, task.name) is not None:
                return task_definition

        return None

    def _match_lane(self, lane: Lane) -> Optional[ExecutionLane]:
        for lane_definition in self.process.lane_definitions:
            if token_utils.matches(lane_definition.re_expressions, lane.name) is not None:
                return lane_definition

        return None

    def clone_event(self,
                    old_event: ActiveEvent,
                    task: BaseTask,
                    parent_id: Optional[str] = None) -> ActiveEvent:

        if parent_id is None:
            parent_id = old_event.parent_id

        event = old_event.clone(task, parent_id)
        self.register_event(event)

        if parent_id is None:
            process = self.process.process
        else:
            process = self.events[parent_id].task

        def process_event(_event) -> ActiveEventState:
            # if there is no processing needed, we skip to routing
            if isinstance(event.task, StartEvent) or isinstance(event.task, EndEvent):
                return event.state.route(event.context)

            if isinstance(event.task, NonWaitingGateway):
                return event.state.route(event.context)

            # if we need to wait, we wait.
            if isinstance(event.task, WaitingGateway):
                return event.state.wait_check()

            # normally we shouldn't wait for tasks, since it's counter BPMN, so
            # we allow configuring waiting for it.
            if self.config.wait_tasks and (
                    isinstance(event.task, ScriptTask) or
                    isinstance(event.task, UserTask) or
                    isinstance(event.task, Task) or
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
                filter(lambda e: is_predecessor(event, e), self.events.values())))

            if other_waiting:
                new_data = ExecutionData.merge(other_waiting.context.data, event.context.data)
                other_waiting.context.data = new_data

                event.state.done()

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

            try:
                LOG.info(yellow("Run  ") + yellow(event.context.task_name, bold=True))
            except Exception as e:
                raise Exception(f"Failure on {event.context.task_name}", e)

            if isinstance(event.task, Process):
                for start_task in event.task.start_tasks.values():
                    # this automatically registers our events for execution
                    self.clone_event(event, start_task, parent_id=event.token_id)
                return

            if isinstance(event.task, Task):
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
                    if target_task.loop:
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
            event_count: Dict[BaseTask, int] = dict()
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
                    filter(lambda e: is_predecessor(waiting_event, e), self.events.values())))

                if not process.are_predecessors(waiting_event.task, potential_predecessors):
                    waiting_event.state.run()

            # check sub-process termination
            found = False
            for ev in self.events.values():
                if ev.parent_id == event.parent_id and ev != event:
                    found = True
                    break

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
            # if the task is done, but the future is still registered, we need to
            # remove the future.
            if event.future in self.futures:
                del self.futures[event.future]

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
