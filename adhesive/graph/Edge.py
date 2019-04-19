from typing import Optional


class Edge():
    """
    An edge between two tasks in a Workflow.
    """
    def __init__(self,
                 _id: str,
                 source_id: str,
                 target_id: str,
                 condition: Optional[str] = None) -> None:
        self.id = _id
        self.source_id = source_id
        self.target_id = target_id
        self.condition = condition if condition else ''

