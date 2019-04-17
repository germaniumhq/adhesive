from typing import Set, Optional, Dict, List, TypeVar, cast

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


class WorkflowExecutor:
    """
    An executor of AdhesiveProcesses.
    """
    pool = concurrent.futures.ProcessPoolExecutor()

    def __init__(self,
                 process: AdhesiveProcess) -> None:
        self.process = process
        self.active_futures = set()

    def execute(self) -> WorkflowData:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        tasks_impl: Dict[str, AdhesiveTask] = dict()
        workflow = self.process.workflow

        self._validate_tasks(workflow, tasks_impl)
        return self.execute_workflow(
            workflow,
            tasks_impl,
            [ActiveEvent(ev) for ev in workflow.start_events.values()])

    def execute_workflow(self,
                         workflow: Workflow,
                         tasks_impl: Dict[str, AdhesiveTask],
                         active_events: List[ActiveEvent]) -> WorkflowData:
        """
        Process the events in a workflow until no more events are available.
        :param workflow:
        :param tasks_impl:
        :param active_events:
        :return:
        """
        processed_data = []

        while active_events or self.active_futures:
            while active_events:
                event = active_events.pop()
                self.process_event(workflow, tasks_impl, event)

            done_futures, not_done_futures = concurrent.futures.wait(self.active_futures,
                                                                     return_when=concurrent.futures.FIRST_COMPLETED)

            for future in done_futures:
                processed_event = future.result()
                self.process_event_result(
                    workflow,
                    active_events,
                    processed_data,
                    processed_event)

            self.active_futures -= done_futures

        return WorkflowData.merge(*processed_data)

    def process_event_result(self,
                             workflow: Workflow,
                             active_events: List[ActiveEvent],
                             finished_events: List[WorkflowData],
                             processed_event: ActiveEvent) -> None:
        """
        When one of the futures returns, we traverse the graph further.
        """
        outgoing_edges = workflow.get_outgoing_edges(processed_event.task.id)

        if not outgoing_edges:
            finished_events.append(processed_event.context.data)

        for outgoing_edge in outgoing_edges:
            task = workflow.tasks[outgoing_edge.target_id]
            active_events.append(processed_event.clone(task))

    def process_event(self,
                      workflow: Workflow,
                      tasks_impl: Dict[str, AdhesiveTask],
                      event: ActiveEvent) -> None:
        """
        Process a single event transition in the workflow. This will use a multiprocess
        pool.
        :param workflow:
        :param tasks_impl:
        :param event:
        :return:
        """
        task = workflow.tasks[event.task.id]

        # nothing to do on events
        if isinstance(task, StartEvent) or isinstance(task, EndEvent):
            self.active_futures.add(resolved_future(event))
            return

        if isinstance(task, SubProcess):
            new_data = self.execute_workflow(task, tasks_impl, [
                event.clone(start_event) for start_event in task.start_events.values()
            ])
            event.context.data = new_data
            self.active_futures.add(resolved_future(event))
            return

        if event.task.id not in tasks_impl:
            self.active_futures.add(resolved_future(event))
            return

        f = WorkflowExecutor.pool.submit(tasks_impl[event.task.id].invoke, event)
        self.active_futures.add(f)

    def _validate_tasks(self,
                        workflow: Workflow,
                        tasks_impl: Dict[str, AdhesiveTask]) -> None:
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
                print(f"@adhesive.task('{unmatched_task.name}')")
                print("def task_impl(context):")
                print("    pass\n\n")

            raise Exception("Missing tasks implementations")

    def _match_task(self, task: Task) -> Optional[AdhesiveTask]:
        for step in self.process.steps:
            if step.matches(task.name) is not None:
                return step

        return None
