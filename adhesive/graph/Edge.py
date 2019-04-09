from typing import Optional


class Edge():
    """
    An edge between two tasks in a Workflow.
    """
    def __init__(self, condition: Optional[str]) -> None:
        self.condition = condition

