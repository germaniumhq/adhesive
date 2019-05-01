from typing import Callable, Any, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.UserTask import UserTask
from adhesive.steps.AdhesiveBaseTask import AdhesiveBaseTask
from .WorkflowContext import WorkflowContext


class AdhesiveUserTask(AdhesiveBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str) -> None:
        super(AdhesiveUserTask, self).__init__(code, *expressions)

    def matches(self, task: BaseTask) -> Optional[List[str]]:
        if not isinstance(task, UserTask):
            return None

        return super(AdhesiveUserTask, self).matches(task)

    def invoke_user_task(
            self,
            context: WorkflowContext,
            ui: Any) -> WorkflowContext:
        params = self.matches(context.task)

        self.code(context, ui, *params)  # type: ignore

        return context
