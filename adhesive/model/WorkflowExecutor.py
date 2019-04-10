from typing import Set, Optional, Dict, List

from adhesive.graph.Task import Task
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.steps.WorkflowContext import WorkflowContext

from .AdhesiveProcess import AdhesiveProcess


class WorkflowExecutor:
    """
    An executorof AdhesiveProcesses.
    """
    def __init__(self,
                 process: AdhesiveProcess) -> None:
        self.process = process

    def execute(self) -> None:
        tasks_impl: Dict[str, AdhesiveTask] = dict()
        self._validate_tasks(tasks_impl)

        workflow = self.process.workflow
        active_events: List[str] = [ _id for _id in workflow.start_events.keys() ]

        while active_events:
            event_id = active_events.pop()
            self.process_event(tasks_impl, event_id)

            for outgoing_edge in workflow.get_outgoing_edges(event_id):
                active_events.append(outgoing_edge.target_id)

    def process_event(self, tasks_impl: Dict[str, AdhesiveTask], task_id: str) -> None:
        if task_id not in tasks_impl:
            return

        task = self.process.workflow.tasks[task_id]
        context = WorkflowContext(task)
        params = [context]

        tasks_impl[task_id].invoke(context)


    def _validate_tasks(self, tasks_impl) -> None:
        unmatched_tasks: Set[Task] = set()

        for task_id, task in self.process.workflow.tasks.items():
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

