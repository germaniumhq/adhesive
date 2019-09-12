from typing import Callable, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Task import Task
from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.execution import token_utils
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from .ExecutionToken import ExecutionToken


class ExecutionTask(ExecutionBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str,
                 loop: Optional[str] = None,
                 when: Optional[str] = None) -> None:
        """
        Create a new adhesive task. The `loop` and `when` are only
        available when doing a programmatic API.
        :param code:
        :param expressions:
        :param loop:
        :param when:
        """
        super(ExecutionTask, self).__init__(code, *expressions)

        self.loop = loop
        self.when = when

    def invoke(
            self,
            event: ActiveEvent) -> ExecutionToken:
        with redirect_stdout(event):
            params = token_utils.matches(self.re_expressions,
                                         event.context.task_name)

            self.code(event.context, *params)  # type: ignore

            return event.context

