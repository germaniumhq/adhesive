from typing import Callable, Optional, List
import re

from .WorkflowContext import WorkflowContext


class AdhesiveTask:
    """
    A task implementation.
    """
    def __init__(self,
                 expression: str,
                 code: Callable) -> None:
        self.re_expression = re.compile(expression)
        self.code = code
        pass

    def matches(self, name: str) -> Optional[List[str]]:
        m = self.re_expression.match(name)

        if not m:
            return None

        return list(m.groups())

    def invoke(self,
        context: WorkflowContext) -> None:
        step_name = context.task.name
        params = self.matches(step_name)

        self.code(context, *params)  # type: ignore

