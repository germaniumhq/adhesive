from typing import Set, Optional, Dict, List

from adhesive.graph.Task import Task
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.steps.WorkflowContext import WorkflowContext

from .AdhesiveProcess import AdhesiveProcess
from .ActiveEvent import ActiveEvent


class WorkflowExecutor:
    """
    An executorof AdhesiveProcesses.
    """
    def __init__(self,
                 process: AdhesiveProcess) -> None:
        self.process = process

    def execute(self) -> None:
        """
        Execute the current events. This will ensure new events are
        generating for forked events.
        """
        tasks_impl: Dict[str, AdhesiveTask] = dict()
        self._validate_tasks(tasks_impl)

        workflow = self.process.workflow
        active_events: List[ActiveEvent] = [ ActiveEvent(ev) for ev in workflow.start_events.values() ]

        while active_events:
            event = active_events.pop()
            self.process_event(tasks_impl, event)

            outgoing_edges = workflow.get_outgoing_edges(event.task.id)

            if len(outgoing_edges) == 0:
                continue

            event.task = workflow.tasks[outgoing_edges.pop().target_id]
            active_events.append(event)

            for outgoing_edge in outgoing_edges:
                task = workflow.tasks[outgoing_edge.target_id]
                active_events.append(event.clone(task))

    def process_event(self, tasks_impl: Dict[str, AdhesiveTask], event: ActiveEvent) -> None:
        if event.task.id not in tasks_impl:
            return

        task = self.process.workflow.tasks[event.task.id]
        tasks_impl[event.task.id].invoke(event.context)


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

