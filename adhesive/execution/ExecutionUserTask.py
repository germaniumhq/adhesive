from typing import Callable, Any, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.UserTask import UserTask
from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from adhesive.execution.ExecutionToken import ExecutionToken
from adhesive.execution import token_utils


class ExecutionUserTask(ExecutionBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str,
                 loop: Optional[str] = None,
                 when: Optional[str] = None,
                 lane: Optional[str] = None) -> None:
        super(ExecutionUserTask, self).__init__(code, *expressions)

        self.loop = loop
        self.when = when
        self.lane = lane

    def invoke_user_task(
            self,
            event: ActiveEvent,
            ui: Any) -> ExecutionToken:
        with redirect_stdout(event):
            params = token_utils.matches(
                    self.re_expressions,
                    event.context.task_name)

            self.code(event.context, ui, *params)  # type: ignore

            return event.context

