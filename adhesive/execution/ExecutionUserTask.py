from typing import Callable, Any, List, Optional, Tuple, Union

from adhesive.graph.ProcessTask import ProcessTask
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
                 *args,
                 code: Callable,
                 expressions: Union[List[str], Tuple[str,...]],
                 regex_expressions: Optional[Union[str, List[str]]],
                 loop: Optional[str] = None,
                 when: Optional[str] = None,
                 lane: Optional[str] = None) -> None:
        if args:
            raise Exception("You need to pass in the arguments by name")

        super(ExecutionUserTask, self).__init__(
            code=code,
            expressions=expressions,
            regex_expressions=regex_expressions)

        self.loop = loop
        self.when = when
        self.lane = lane

    def invoke_usertask(
            self,
            event: ActiveEvent,
            ui: Any) -> ExecutionToken:
        with redirect_stdout(event):
            params = token_utils.matches(
                    self.re_expressions,
                    event.context.task_name)

            self.code(event.context, ui, *params)  # type: ignore

            return event.context

    def __repr__(self) -> str:
        return f"@usertask(expressions={self.expressions}, code={self.code.__name__})"
