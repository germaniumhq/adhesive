from typing import Optional, Dict, Any
from adhesive.steps.ExecutionData import ExecutionData
from adhesive.graph.BaseTask import BaseTask
from adhesive.workspace.Workspace import Workspace
from adhesive.workspace.local.LocalLinuxWorkspace import LocalLinuxWorkspace


class ExecutionToken:
    """
    A context passed to an execution of a task. It holds the information
    about:
    - data that's attached to this token,
    - workspace where files can be created. This depends on the actual runtime
      (ie linux, windows, docker)

    A workflow context it's an execution token that's being passed around.
    """
    def __init__(self,
                 task: 'BaseTask',
                 data: Optional[Dict]=None,
                 workspace: Optional[Workspace]=None) -> None:
        self.task = task
        self.data = ExecutionData(data)
        self.workspace: Workspace = LocalLinuxWorkspace() if not workspace else workspace
        self.loop: Optional[WorkflowLoop] = None

        self.update_title()

    def update_title(self) -> None:
        # FIXME: this breaks the encapsulation of the data
        try:
            self.task_name = self.task.name.format(**{
                "context": self,
                "data": self.data,
                "loop": self.loop
            })
        except Exception as e:
            self.task_name = self.task.name

    def clone(self, task: 'BaseTask') -> 'ExecutionToken':
        result = ExecutionToken(
            task,
            self.data.as_dict(),
            self.workspace,  # FIXME: this should be a clone
        )

        return result

    def as_mapping(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "data": self.data,
            "loop": self.loop,
            "task_name": self.task_name,
        }


from adhesive.steps.WorkflowLoop import WorkflowLoop
