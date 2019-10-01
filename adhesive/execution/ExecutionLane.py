from typing import Callable
import re


class ExecutionLane:
    """
    Has the programmatic definition of a lane.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str) -> None:
        self.re_expressions = list(map(re.compile, expressions))
        self.code = code
        self.expressions = expressions
        self.used = False

    def __repr__(self) -> str:
        return f"@lane(expressions={self.expressions}, code={self.code.__name__})"
