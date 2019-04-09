from typing import Callable


class AdhesiveTask:
    """
    A task implementation.
    """
    def __init__(self,
                 expression: str,
                 code: Callable) -> None:
        self.expression = expression
        self.code = code
        pass

