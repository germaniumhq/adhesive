import re
from typing import Set, Optional, Dict, List, TypeVar, cast

from adhesive.graph.Gateway import Gateway, NonWaitingGateway, WaitingGateway
from adhesive.graph.Task import Task
from adhesive.model.GatewayController import GatewayController
from adhesive.model.TaskFuture import TaskFuture
from adhesive.steps.WorkflowData import WorkflowData

T = TypeVar('T')

import concurrent.futures
from concurrent.futures import Future

from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Workflow import Workflow
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.graph.ExclusiveGateway import ExclusiveGateway

from .ActiveEvent import ActiveEvent
from .AdhesiveProcess import AdhesiveProcess


class WorkflowExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool = concurrent.futures.ProcessPoolExecutor()

    def __init__(self,
                 process: AdhesiveProcess) -> None:
        self.process = process

        # holds a mapping from the ActiveEvent id that generated it, to the TaskFuture
        # holding both the node in the graph (Task), and the Future that is going
        # to resolve when the task is done. These are futures that are currently running.
        self.active_futures: Dict[str, TaskFuture] = dict()
        self.pending_events: List[ActiveEvent] = []

        # A dictionary of events that are currently active. This is just to find out
        # the parent of an event, since from it we can also derive the current parent
        # workflow.
        self.events: Dict[str, ActiveEvent] = dict()

        # A dictionary of events that are currently waiting on other active events,
        # or executing futures ahead in the execution graph.
        self.waiting_events: Dict[str, ActiveEvent] = dict()

    async def execute(self) -> WorkflowData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        workflow = self.process.workflow
        tasks_impl: Dict[str, AdhesiveTask] = dict()

        self._validate_tasks(workflow, tasks_impl)

        root_event = self.register_event(ActiveEvent(None, workflow))
        self.pending_events = [self.register_event(root_event.clone(task, root_event))
                               for task in workflow.start_tasks.values()]

        await self.execute_workflow(tasks_impl)
        self.unregister_event(root_event)

        return root_event.context.data

    async def execute_workflow(self,
                               tasks_impl: Dict[str, AdhesiveTask]) -> None:
        """
        Process the events in a workflow until no more events are available.
        For example an event is the start of the workflow. The events are
        then creating futures (i.e. actual stuff that's being processed)
        that in turn might generate new events.
        :param tasks_impl:
        :param pending_events:
        :return:
        """
        while self.pending_events or self.active_futures:
            while self.pending_events:
                event = self.pending_events.pop()
                self.process_event(tasks_impl, event)

            active_futures = list(map(lambda it: it.future, self.active_futures.values()))
            done_futures, not_done_futures = concurrent.futures.wait(
                active_futures,
                return_when=concurrent.futures.FIRST_COMPLETED,
                timeout=5)

            for future in done_futures:
                processed_event: ActiveEvent = future.result()
                self.process_event_result(processed_event)
                self.active_futures.pop(processed_event.id)

        if self.waiting_events:
            raise Exception(f"Execution of the workflow finished, but some "
                            f"events were still waiting: {self.waiting_events}")

    def process_event_result(self,
                             processed_event: ActiveEvent) -> None:
        """
        When one of the futures returns, we traverse the graph further.
        """
        workflow = cast(Workflow, self.get_parent(processed_event.id).task)

        # we're going to process first the edges, to be able to remove
        # the edges if they have conditions that don't match.

        # if the processed event was on a gateway, we need to do
        # the routing to the next events, depending on the gateway
        # type. For this, the routing will select only the edges that
        # activate, and create events for each.
        if isinstance(processed_event.task, ExclusiveGateway):
            gateway = cast(Gateway, processed_event.task)
            outgoing_edges = GatewayController.route_single_output(
                workflow, gateway, processed_event)
        else:
            outgoing_edges = GatewayController.route_all_outputs(
                workflow, processed_event.task, processed_event)

        # If there are no more outgoing edges, the current event is
        # done. We merge its data into the parent event.
        parent_event = self.get_parent(processed_event.id)
        parent_event.close_child(processed_event,
                                 merge_data=not outgoing_edges)

        # publish the remaining edges as events to be processed.
        for outgoing_edge in outgoing_edges:
            task = workflow.tasks[outgoing_edge.target_id]
            parent = self.get_parent(processed_event.id)
            self.pending_events.append(self.register_event(processed_event.clone(task, parent)))

        # this needs to happen after the publishing of the remaining edges,
        # so we catch eventual pending events for the finished task in a
        # subprocess.
        if not parent_event.active_children and \
                isinstance(parent_event.task, SubProcess) and \
                parent_event.task not in map(lambda it: it.task, self.pending_events):
            self.active_futures[parent_event.id].future.set_result(parent_event)

        self.unregister_event(processed_event)

    def process_event(self,
                      tasks_impl: Dict[str, AdhesiveTask],
                      event: ActiveEvent) -> None:
        """
        Process a single event transition in the workflow. This will use a multiprocess
        pool.
        :param tasks_impl:
        :param event:
        :return:
        """
        workflow = cast(Workflow, self.get_parent(event.id).task)
        task = workflow.tasks[event.task.id]

        # nothing to do on events
        if isinstance(task, StartEvent) or isinstance(task, EndEvent):
            self.active_futures[event.id] = TaskFuture.resolved(task, event)
            return

        # if this is an exclusive gateway, the current event is immediately passed
        # through.
        if isinstance(task, NonWaitingGateway):
            self.active_futures[event.id] = TaskFuture.resolved(task, event)
            return

        # If this is a parallel gateway, or task, it needs to wait for all
        # the incoming messages, before we can release the event. We also need
        # to create an event that gathers all the data from the incoming edges.
        # This means a single instance can exist at a time that's not yet fired,
        # and is still pending.
        if isinstance(task, Task) or isinstance(task, WaitingGateway):
            active_tasks = [ev.task for ev in self.pending_events]
            active_tasks.extend(map(lambda it: it.task, self.active_futures.values()))

            waiting_event = self.waiting_event(event)

            # If we have predecessors, we need to wait until they are done. This also
            # means that the current event is actually defacto consumed.
            if self.process.workflow.are_predecessors(task, active_tasks):
                return

            self.waiting_events.pop(waiting_event.task.id)

            # We can now invoke the actual method if that's the case. If it's
            # only a gateway we just need to mark it as done, since they don't have
            # associated tasks.
            if isinstance(task, WaitingGateway):
                self.active_futures[event.id] = TaskFuture.resolved(task, waiting_event)
                return

            event = waiting_event

        # if this is a subprocess, we're going to create events that point
        # to the current event.
        if isinstance(task, SubProcess):
            for start_task in task.start_tasks.values():
                start_event = self.register_event(event.clone(start_task, event))
                self.process_event(tasks_impl, start_event)

            # This event will finish only when the child sub events will finish.
            event.future = Future()
            self.active_futures[event.id] = TaskFuture(task, event.future)
            return

        # we submit the user task to the parallel pool, and feed the future
        # into the active futures that are still to be waited.
        future = WorkflowExecutor.pool.submit(tasks_impl[event.task.id].invoke, event)
        self.active_futures[event.id] = TaskFuture(task, future)

    def waiting_event(self,
                      event: ActiveEvent) -> ActiveEvent:
        """
        Ensures a waiting event is registered for the target task from the
        source event. If it's already registered it merges the data
        into the already waiting event.
        :param event:
        :return:
        """
        waiting_event = self.waiting_events.get(event.task.id, None)

        if waiting_event:
            waiting_event.context.data = WorkflowData.merge(
                waiting_event.context.data,
                event.context.data)
            result = waiting_event
            self.unregister_event(event)
        else:
            self.waiting_events[event.task.id] = event
            result = event

        return result

    def register_event(self,
                       event: ActiveEvent) -> ActiveEvent:
        """
        Register the event into a big map for finding, so we can access it later
        for parents and what not, without serializing the event graph to
        the subprocesses.

        :param event:
        :return:
        """
        self.events[event.id] = event
        return event

    def unregister_event(self,
                         event: ActiveEvent) -> None:
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
                        workflow: Workflow,
                        tasks_impl: Dict[str, AdhesiveTask]) -> None:
        """
        Recursively traverse the graph, and print to the user if it needs to implement
        some tasks.

        :param workflow:
        :param tasks_impl:
        :return:
        """
        unmatched_tasks: Set[BaseTask] = set()

        for task_id, task in workflow.tasks.items():
            if isinstance(task, SubProcess):
                self._validate_tasks(task, tasks_impl)
                continue

            # gateways don't have associated tasks with them.
            if isinstance(task, StartEvent) or \
                    isinstance(task, EndEvent) or \
                    isinstance(task, Gateway):
                continue

            adhesive_step = self._match_task(task)

            tasks_impl[task_id] = adhesive_step

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
