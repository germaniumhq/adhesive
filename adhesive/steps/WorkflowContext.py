from typing import Optional, Dict, Any
from adhesive.graph.BaseTask import BaseTask
from adhesive.steps.WorkflowData import WorkflowData


class WorkflowContext:
    """
    A context passed to an execution of a task. It holds the information
    about:
    - data that's being populated across tasks,
    """
    def __init__(self, task: BaseTask,
                 data: Optional[Dict] = None) -> None:
        self.task = task
        self.data = WorkflowData(data)

    def clone(self, task: BaseTask) -> 'WorkflowContext':
        return WorkflowContext(task, self.data.as_dict())

    def as_mapping(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "data": self.data
        }
