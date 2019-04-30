import re
from concurrent.futures import Future
from typing import Set, Optional, Dict, TypeVar, cast, Any

from adhesive.graph.BoundaryEvent import BoundaryEvent
from adhesive.graph.Gateway import Gateway, NonWaitingGateway, WaitingGateway
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.model.ActiveEventStateMachine import ActiveEventState
from adhesive.model.GatewayController import GatewayController
from adhesive.model.WorkflowExecutorConfig import WorkflowExecutorConfig
from adhesive.steps.WorkflowData import WorkflowData

T = TypeVar('T')

import concurrent.futures

from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Workflow import Workflow
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.graph.ExclusiveGateway import ExclusiveGateway

from .ActiveEvent import ActiveEvent
from .AdhesiveProcess import AdhesiveProcess

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


class WorkflowExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool = concurrent.futures.ProcessPoolExecutor()

    def __init__(self,
                 process: AdhesiveProcess,
                 ut_provider: Optional['UserTaskProvider'] = None,
                 wait_tasks: bool = True) -> None:
        self.process = process
        self.tasks_impl: Dict[str, AdhesiveTask] = dict()

        # A dictionary of events that are currently active. This is just to find out
        # the parent of an event, since from it we can also derive the current parent
        # workflow.
        self.events: Dict[str, ActiveEvent] = dict()
        self.futures: Dict[Any, str] = dict()
        self.ut_provider = ut_provider

        self.config = WorkflowExecutorConfig(wait_tasks=wait_tasks)

    async def execute(self) -> WorkflowData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        workflow = self.process.workflow
        self.tasks_impl: Dict[str, AdhesiveTask] = dict()

        self._validate_tasks(workflow)

        fake_event = ActiveEvent(parent_id=None, task=workflow)
        fake_event.id = None

        root_event = self.clone_event(fake_event, workflow)

        def raise_exception(_ev):
            raise _ev.data

        root_event.state.after_enter(ActiveEventState.ERROR, raise_exception)

        await self.execute_workflow()

        return root_event.context.data

    async def execute_workflow(self) -> None:
        """
        Process the events in a workflow until no more events are available.
        For example an event is the start of the workflow. The events are
        then creating futures (i.e. actual stuff that's being processed)
        that in turn might generate new events.
        :return:
        """
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

            for future in done_futures:
                event_id = self.futures[future]
                try:
                    context = future.result()
                    self.events[event_id].state.route(context)
                except Exception as e:
                    self.events[event_id].state.error(e)
                finally:
                    del self.futures[future]

    def register_event(self,
                       event: ActiveEvent) -> ActiveEvent:
        """
        Register the event into a big map for finding, so we can access it later
        for parents and what not, without serializing the event graph to
        the subprocesses.

        :param event:
        :return:
        """
        if event.id in self.events:
            raise Exception(f"Event {event.id} is already registered as "
                            f"{self.events[event.id]}. Got a new request to register "
                            f"it as {event}.")

        print(f"Register {event}")

        self.events[event.id] = event

        return event

    def unregister_event(self,
                         event: ActiveEvent) -> None:
        if event.id not in self.events:
            raise Exception(f"{event} not found in events. Either the event was "
                            f"already terminated, either it was not registered.")

        print(f"Unregister {event}")

        del self.events[event.id]

    def get_parent(self,
                   event_id: str) -> ActiveEvent:
        """
        Find the parent of an event by looking at the event ids.
        :param event_id:
        :return:
        """
        event = self.events[event_id]
        parent = self.events[event.parent_id]

        return parent

    def _validate_tasks(self,
                        workflow: Workflow) -> None:
        """
        Recursively traverse the graph, and print to the user if it needs to implement
        some tasks.

        :param workflow:
        :return:
        """
        unmatched_tasks: Set[BaseTask] = set()

        for task_id, task in workflow.tasks.items():
            if isinstance(task, SubProcess):
                self._validate_tasks(task)
                continue

            # gateways don't have associated tasks with them.
            if isinstance(task, StartEvent) or \
                    isinstance(task, EndEvent) or \
                    isinstance(task, Gateway) or \
                    isinstance(task, BoundaryEvent):
                continue

            adhesive_step = self._match_task(task)

            self.tasks_impl[task_id] = adhesive_step

            if not adhesive_step:
                unmatched_tasks.add(task)

        if unmatched_tasks:
            print("Missing tasks implementations. Generate with:\n")
            for unmatched_task in unmatched_tasks:
                print(f"@adhesive.task('{re.escape(unmatched_task.name)}')")
                print("def task_impl(context):")
                print("    pass\n\n")

            raise Exception("Missing tasks implementations")

    def _match_task(self, task: BaseTask) -> Optional[AdhesiveTask]:
        for step in self.process.steps:
            if step.matches(task.name) is not None:
                return step

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
            workflow = self.process.workflow
        else:
            workflow = self.events[parent_id].task

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
                    isinstance(event.task, Task) or
                    isinstance(event.task, Workflow)
            ):
                return event.state.wait_check()

            return event.state.run()

        def get_other_task_waiting(source: ActiveEvent) -> Optional[ActiveEvent]:
            for ev in self.events.values():
                if ev == source:
                    continue

                if ev.task == source.task and ev.state.state in ACTIVE_STATES:
                    return ev

            return None

        def wait_task(_event) -> Optional[ActiveEventState]:
            # is another waiting task already present?
            other_waiting = get_other_task_waiting(event)

            potential_predecessors = list(map(
                lambda e: e.task,
                filter(
                    lambda e: e.state.state in ACTIVE_STATES and e.task != event.task,
                    self.events.values()
                )))

            if other_waiting:
                new_data = WorkflowData.merge(other_waiting.context.data, event.context.data)
                other_waiting.context.data = new_data

                event.state.done()

            # if we have predecessors, we stay in waiting
            if workflow.are_predecessors(event.task, potential_predecessors):
                return None

            if other_waiting:
                other_waiting.state.run()
                return None

            return event.state.run()

        def run_task(_event) -> None:
            if isinstance(event.task, Workflow):
                for start_task in event.task.start_tasks.values():
                    # this automatically registers our events for execution
                    self.clone_event(event, start_task, parent_id=event.id)
                return

            if isinstance(event.task, Task):
                future = WorkflowExecutor.pool.submit(
                    self.tasks_impl[event.task.id].invoke,
                    event.context)
                self.futures[future] = event.id
                event.future = future
                return

            if isinstance(event.task, UserTask):
                future = Future()
                self.futures[future] = event.id
                event.future = future

                self.ut_provider.register_event(self, event)

                return

            return event.state.route(event.context)

        def error_task(_event) -> None:
            # if we have a boundary error task, we use that one for processing.
            if event.task.error_task:
                self.clone_event(event, event.task.error_task)

                if event.task.error_task.cancel_activity:
                    event.state.done_check(None)
                else:
                    event.state.route()

                return

            if event.parent_id in self.events:
                parent_event = self.get_parent(event.id)

                # we move the parent into error
                parent_event.state.error(_event.data)

                # FIXME: not sure if this is enough.
                for potential_child in list(self.events.values()):
                    if potential_child.parent_id != event.id:
                        continue

                    potential_child.state.error(_event.data)

            event.state.done_check(None)  # we kill the current event

        def route_task(_event) -> None:
            event.context = _event.data

            if isinstance(event.task, ExclusiveGateway):
                gateway = cast(Gateway, event.task)
                outgoing_edges = GatewayController.route_single_output(
                    workflow, gateway, event)
            else:
                outgoing_edges = GatewayController.route_all_outputs(
                    workflow, event.task, event)

            for outgoing_edge in outgoing_edges:
                target_task = workflow.tasks[outgoing_edge.target_id]
                self.clone_event(event, target_task)

            event.state.done_check(outgoing_edges)

        def done_check(_event) -> None:
            outgoing_edges = _event.data

            if not outgoing_edges:
                return event.state.done_end_task()

            return event.state.done()

        def done_end_task(_event) -> None:
            # we should check all the WAITING processes if they finished.
            waiting_events = list(filter(
                lambda e: e.state.state == ActiveEventState.WAITING and e.task != event.task,
                self.events.values()
            ))

            for waiting_event in waiting_events:
                potential_predecessors = list(map(
                    lambda e: e.task,
                    filter(
                        lambda e: e.state.state in DONE_STATES and e.task != waiting_event.task,
                        self.events.values()
                    )))

                if not workflow.are_predecessors(waiting_event.task, potential_predecessors):
                    waiting_event.state.run()

            # check sub-process termination
            found = False
            for ev in self.events.values():
                if ev.parent_id == event.parent_id and ev != event:
                    found = True
                    break

            # we merge into the parent event if it's an end state.
            if parent_id is not None:
                self.events[parent_id].context.data = WorkflowData.merge(
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
        event.state.after_enter(ActiveEventState.ERROR, error_task)
        event.state.after_enter(ActiveEventState.ROUTING, route_task)
        event.state.after_enter(ActiveEventState.DONE_CHECK, done_check)
        event.state.after_enter(ActiveEventState.DONE_END_TASK, done_end_task)
        event.state.after_enter(ActiveEventState.DONE, done_task)

        return event
