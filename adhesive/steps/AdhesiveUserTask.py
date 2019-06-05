from typing import Callable, Any, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.UserTask import UserTask
from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.steps.AdhesiveBaseTask import AdhesiveBaseTask
from adhesive.steps.ExecutionToken import ExecutionToken


class AdhesiveUserTask(AdhesiveBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str,
                 loop: Optional[str] = None,
                 when: Optional[str] = None) -> None:
        super(AdhesiveUserTask, self).__init__(code, *expressions)

        self.loop = loop
        self.when = when

    def matches(self,
                task: BaseTask,
                resolved_name: str) -> Optional[List[str]]:
        if not isinstance(task, UserTask):
            return None

        return super(AdhesiveUserTask, self).matches(task, resolved_name)

    def invoke_user_task(
            self,
            event: ActiveEvent,
            ui: Any) -> ExecutionToken:
        with redirect_stdout(event):
            context = event.context

            params = self.matches(context.task, context.task_name)

            self.code(context, ui, *params)  # type: ignore

            return context
