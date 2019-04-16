from typing import Optional, Dict, List
from adhesive.graph.Task import Task
from adhesive.steps.WorkflowData import WorkflowData


class WorkflowContext:
    """
    A context passed to an execution of a task.
    """
    def __init__(self, task: Task, data: Optional[Dict] = None) -> None:
        self.task = task
        self.data = WorkflowData(data)

    def clone(self, task: Task) -> 'WorkflowContext':
        return WorkflowContext(task, self.data.as_dict())
