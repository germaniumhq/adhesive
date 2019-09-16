import uuid
from typing import Optional

from adhesive.execution import token_utils
from adhesive.graph.BaseTask import BaseTask
from adhesive.model.ActiveEventStateMachine import ActiveEventStateMachine
from adhesive.model.ActiveLoopType import ActiveLoopType


class ActiveEvent:
    """
    An event that passes through the system. It can fork
    in case there are multiple executions going down.
    """
    def __init__(self,
                 execution_id: str,
                 parent_id: Optional['str'],
                 context: 'ExecutionToken') -> None:
        self.execution_id = execution_id
        self.token_id: str = str(uuid.uuid4())
        self.parent_id = parent_id

        if not isinstance(context, ExecutionToken):
            raise Exception(f"Not an execution token: {context}")

        self._task = context.task
        self.context = context

        self.state = ActiveEventStateMachine()
        self.state.active_event = self

        self.future = None

        self.loop_type: Optional[AciveLoopType] = None

    def __getstate__(self):
        return {
            "execution_id": self.execution_id,
            "token_id": self.token_id,
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
        result = ActiveEvent(
            execution_id=self.execution_id,
            parent_id=parent_id,  # FIXME: why, if this is a clone
            context=self.context.clone(task)
        )
        result.context.token_id = result.token_id

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

        result.context.task_name = token_utils.parse_name(
                result.context,
                result.context.task.name)

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
        # the task.token_id should be the same as the self.texecutionoken_id
        return f"ActiveEvent({self.token_id}, {self.state.state}): " \
               f"({self.task.id}):{self.context.task_name}"


from adhesive.execution.ExecutionToken import ExecutionToken
