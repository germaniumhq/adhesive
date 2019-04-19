from typing import Set, Optional, Dict, List, TypeVar, cast
import re

from adhesive.steps.WorkflowData import WorkflowData

T = TypeVar('T')

import concurrent.futures
from concurrent.futures import Future

from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.Task import Task
from adhesive.graph.Workflow import Workflow
from adhesive.steps.AdhesiveTask import AdhesiveTask
from .ActiveEvent import ActiveEvent
from .AdhesiveProcess import AdhesiveProcess


def resolved_future(item: T) -> Future:
    result = Future()
    result.set_result(item)

    return result


global_events: Dict[str, ActiveEvent] = dict()


class WorkflowExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool = concurrent.futures.ProcessPoolExecutor()

    def __init__(self,
                 process: AdhesiveProcess) -> None:
        self.process = process
        self.active_futures = set()
        self.pending_events: List[ActiveEvent] = []

    def execute(self) -> WorkflowData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        workflow = self.process.workflow
        tasks_impl: Dict[str, AdhesiveTask] = dict()

        self._validate_tasks(workflow, tasks_impl)

        root_event = self.register_event(ActiveEvent(None, workflow))
        self.pending_events = [self.register_event(ActiveEvent(root_event.id, task))
                               for task in workflow.start_tasks.values()]

        self.execute_workflow(tasks_impl)

        return root_event.context.data

    def execute_workflow(self,
                         tasks_impl: Dict[str, AdhesiveTask]) -> None:
        """
        Process the events in a workflow until no more events are available.
        :param tasks_impl:
        :param pending_events:
        :return:
        """
        while self.pending_events or self.active_futures:
            while self.pending_events:
                event = self.pending_events.pop()
                self.process_event(tasks_impl, event)

            done_futures, not_done_futures = concurrent.futures.wait(self.active_futures,
                                                                     return_when=concurrent.futures.FIRST_COMPLETED,
                                                                     timeout=5)

            for future in done_futures:
                processed_event = future.result()
                self.process_event_result(processed_event)

            self.active_futures -= done_futures

        return

    def process_event_result(self,
                             processed_event: ActiveEvent) -> None:
        """
        When one of the futures returns, we traverse the graph further.
        """
        workflow = self.get_parent(processed_event.id).task
        outgoing_edges = workflow.get_outgoing_edges(processed_event.task.id)

        # If there are no more outgoing edges, the current event is
        # done. We merge its data into the parent event.
        parent_event = self.get_parent(processed_event.id)

        # FIXME: this looks way too complicated.
        if not outgoing_edges:
            parent_event.close_child(processed_event)
        elif processed_event.id in parent_event.active_children:
            parent_event.active_children.remove(processed_event.id)

        for outgoing_edge in outgoing_edges:
            task = workflow.tasks[outgoing_edge.target_id]
            parent = self.get_parent(processed_event.id)
            self.pending_events.append(self.register_event(processed_event.clone(task, parent)))

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
        workflow = self.get_parent(event.id).task
        task = workflow.tasks[event.task.id]

        # nothing to do on events
        if isinstance(task, StartEvent) or isinstance(task, EndEvent):
            self.active_futures.add(resolved_future(event))
            return

        # if this is a subprocess, we're going to create events that point
        # to the current event.
        if isinstance(task, SubProcess):
            for start_task in task.start_tasks.values():
                start_event = self.register_event(event.clone(start_task, event))
                self.process_event(tasks_impl, start_event)

            event.future = Future()
            self.active_futures.add(event.future)
            return

        # if this is an unknown type of task, we're just jumping over it in the
        # graph.
        if event.task.id not in tasks_impl:
            self.active_futures.add(resolved_future(event))
            return

        # we submit the user task to the parallel pool, and feed the future
        # into the active futures that are still to be waited.
        f = WorkflowExecutor.pool.submit(tasks_impl[event.task.id].invoke, event)
        self.active_futures.add(f)

    def register_event(self,
                       event: ActiveEvent) -> ActiveEvent:
        """
        Register the event into a big map for finding, so we can access it later
        for parents and what not, without serializing the event graph to
        the subprocesses.

        :param event:
        :return:
        """
        global_events[event.id] = event
        return event

    def get_parent(self,
                   event_id: str) -> ActiveEvent:
        """
        Find the parent of an event by looking at the event ids.
        :param event_id:
        :return:
        """
        event = global_events[event_id]
        parent = global_events[event.parent_id]

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
        unmatched_tasks: Set[Task] = set()

        for task_id, task in workflow.tasks.items():
            if isinstance(task, SubProcess):
                self._validate_tasks(task, tasks_impl)
                continue

            if isinstance(task, StartEvent) or isinstance(task, EndEvent):
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

    def _match_task(self, task: Task) -> Optional[AdhesiveTask]:
        for step in self.process.steps:
            if step.matches(task.name) is not None:
                return step

        return None
