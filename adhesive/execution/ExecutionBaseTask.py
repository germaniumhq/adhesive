import re
from typing import Callable, Optional, List, Union

from adhesive.model.generate_methods import generate_matching_re


class ExecutionBaseTask:
    """
    A task implementation.
    """
    def __init__(self,
                 *args,
                 code: Callable,
                 expressions: Optional[List[str]],
                 regex_expressions: Optional[Union[str, List[str]]]) -> None:
        if args:
            raise Exception("You need to pass in the arguments by name")

        if not expressions and not regex_expressions:
            raise Exception("You need to pass in at least an expression, or a "
                            "regex expression to define this task.")

        if regex_expressions and not isinstance(regex_expressions, list):
            regex_expressions = [regex_expressions]

        self.regex_expressions = regex_expressions
        self.expressions = expressions
        self.re_expressions = []  # these one are actually checked
        self.code = code
        self.used = False  # this is set by the process executor task validation

        if expressions:
            for expression in expressions:
                self.re_expressions.append(
                    re.compile(generate_matching_re(expression))
                )

        if regex_expressions:
            for regex_expression in regex_expressions:
                self.re_expressions.append(
                    re.compile(regex_expression)
                )
