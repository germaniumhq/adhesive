from typing import Optional, Dict, Any

from adhesive.graph.BaseTask import BaseTask
from adhesive.steps.ExecutionData import ExecutionData
from adhesive.workspace.Workspace import Workspace


class ExecutionToken:
    """
    A context passed to an execution of a task. It holds the information
    about:
    - data that's attached to this token,
    - workspace where files can be created. This depends on the actual runtime
      (ie linux, windows, docker)
    - loop information (when in a loop).

    A workflow context it's an execution token that's being passed around.
    """
    def __init__(self,
                 *args,
                 task: 'BaseTask',
                 execution_id: str,
                 token_id: str,
                 data: Optional[Dict],
                 workspace: Workspace) -> None:
        if args:
            raise Exception("You need to pass the parameters by name")

        self.task = task
        self.data = ExecutionData(data)
        self.execution_id = execution_id
        self.token_id = token_id
        self.workspace = workspace
        self.task_name: Optional[str] = None

        self.loop: Optional[WorkflowLoop] = None

        self.update_title()

    def update_title(self) -> None:
        # FIXME: this breaks the encapsulation of the data
        try:
            # FIXME: this is a lot like eval_edge from the gateway controller
            evaldata = dict(self.data._data)
            context = self.as_mapping()

            evaldata.update(context)

            self.task_name = self.task.name.format(**evaldata)
        except Exception as e:
            self.task_name = self.task.name

    def clone(self, task: 'BaseTask') -> 'ExecutionToken':
        result = ExecutionToken(
            task=task,
            execution_id=self.execution_id,
            token_id=self.token_id,   # FIXME: probably a new token?
            data=self.data.as_dict(),
            workspace=self.workspace.clone(),
        )

        return result

    def as_mapping(self) -> Dict[str, Any]:
        """
        This mapping is for evaluating routing conditions.
        :return:
        """
        return {
            "task": self.task,
            "execution_id": self.execution_id,
            "token_id": self.token_id,
            "data": self.data,
            "loop": self.loop,
            "task_name": self.task_name,
            "context": self,
        }


from adhesive.steps.WorkflowLoop import WorkflowLoop
