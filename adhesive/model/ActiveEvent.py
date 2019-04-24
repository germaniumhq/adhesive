import uuid
from typing import Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.model.ActiveEventStateMachine import ActiveEventStateMachine
from adhesive.steps.WorkflowContext import WorkflowContext


class ActiveEvent:
    """
    An event that passes through the system. It can fork
    in case there are multiple executions going down.
    """
    def __init__(self,
                 parent_id: Optional['str'],
                 task: BaseTask) -> None:
        self.id: str = str(uuid.uuid4())
        self.parent_id = parent_id

        if not isinstance(task, BaseTask):
            raise Exception(f"Not a task: {task}")

        self._task = task
        self.context = WorkflowContext(task)

        self.state = ActiveEventStateMachine()
        self.future = None

    def __getstate__(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "_task": self._task,
            "context": self.context
        }

    def clone(self,
              task: BaseTask,
              parent_id: str) -> 'ActiveEvent':
        """
        Clone the current event for another task id target.
        """
        result = ActiveEvent(parent_id, task)
        result.context = self.context.clone(task)

        return result

    @property
    def task(self) -> BaseTask:
        return self._task

    @task.setter
    def task(self, task: BaseTask) -> None:
        if not isinstance(task, BaseTask):
            raise Exception(f"Not a task: {task}")

        self.context.task = task
        self._task = task

    def __repr__(self) -> str:
        return f"ActiveEvent({self.id}, {self.state.state}): {self.task}"
