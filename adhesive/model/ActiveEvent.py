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
                 context: WorkflowContext) -> None:
        self.id: str = str(uuid.uuid4())
        self.parent_id = parent_id

        if not isinstance(context, WorkflowContext):
            raise Exception(f"Not a task: {task}")

        self._task = context.task
        self.context = context

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
        result = ActiveEvent(parent_id, self.context.clone(task))

        # if we are exiting the current loop, we need to switch to the
        # parent loop.
        # FIXME: this probably doesn't belong here
        # FIXME: the self.task != task is probably wrong, since we want to support
        # boolean looping expressions.
        if self.context.task.loop and self.context.loop \
                and self.context.loop.task == self.context.task \
                and self.context.task != task \
                and parent_id == self.parent_id:
            result.context.loop = self.context.loop.parent_loop
        else:
            result.context.loop = self.context.loop

        result.context.update_title()

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
        return f"ActiveEvent({self.id}, {self.state.state}): " \
               f"({self.task.id}):{self.context.task_name}"
