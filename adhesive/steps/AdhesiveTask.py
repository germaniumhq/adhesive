import re
from typing import Callable, Optional, List, Tuple

from .WorkflowContext import WorkflowContext


class AdhesiveTask:
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str) -> None:
        self.re_expressions = list(map(re.compile, expressions))
        self.code = code

    def matches(self, name: str) -> Optional[List[str]]:
        """
        Checks if this implementation matches any of the expressions
        bounded to this task. If yes, it returns the potential variables
        extracted from the expression.
        :param name:
        :return:
        """
        for re_expression in self.re_expressions:
            m = re_expression.match(name)

            if m:
                return list(m.groups())

        return None

    def invoke(self,
               event_id: str,
               context: WorkflowContext) -> Tuple[str, WorkflowContext]:
        step_name = context.task.name
        params = self.matches(step_name)

        self.code(context, *params)  # type: ignore

        return event_id, context
