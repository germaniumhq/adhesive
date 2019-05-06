from typing import Optional, Dict, Any
from adhesive.steps.WorkflowData import WorkflowData
from adhesive.graph.BaseTask import BaseTask
from adhesive.workspace.Workspace import Workspace
from adhesive.workspace.local.LocalLinuxWorkspace import LocalLinuxWorkspace


class WorkflowContext:
    """
    A context passed to an execution of a task. It holds the information
    about:
    - data that's being populated across tasks,
    """
    def __init__(self, task: 'BaseTask',
                 data: Optional[Dict]=None,
                 workspace: Optional[Workspace]=None) -> None:
        self.task = task
        self.data = WorkflowData(data)
        self.workspace: Workspace = LocalLinuxWorkspace() if not workspace else workspace

    def clone(self, task: 'BaseTask') -> 'WorkflowContext':
        return WorkflowContext(
            task,
            self.data.as_dict(),
            self.workspace,  # FIXME: this should be a clone
        )

    def as_mapping(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "data": self.data
        }
