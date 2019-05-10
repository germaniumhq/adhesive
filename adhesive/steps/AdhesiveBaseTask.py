import re
from typing import Callable, Optional, List

from adhesive.graph.BaseTask import BaseTask


class AdhesiveBaseTask:
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str) -> None:
        self.re_expressions = list(map(re.compile, expressions))
        self.code = code

    def matches(self,
                task: BaseTask,
                resolved_name: str) -> Optional[List[str]]:
        """
        Checks if this implementation matches any of the expressions
        bounded to this task. If yes, it returns the potential variables
        extracted from the expression.
        :param context:
        :return:
        """
        for re_expression in self.re_expressions:
            m = re_expression.match(resolved_name)

            if m:
                return list(m.groups())

        return None
