from typing import Optional

from .BaseTask import BaseTask


class EndEvent(BaseTask):
    """
    EndEvent
    """
    def __init__(self,
                 parent_process: Optional['Process'],
                 id: str,
                 name: str) -> None:
        super().__init__(
            parent_process=parent_process,
            id=id,
            name=name)


