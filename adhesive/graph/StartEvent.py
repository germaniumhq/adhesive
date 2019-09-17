from typing import Optional

from .BaseTask import BaseTask


class StartEvent(BaseTask):
    """
    StartEvent documentation.
    """
    def __init__(self,
                 *args,
                 parent_process: Optional['Process'],
                 id: str,
                 name: str) -> None:
        if args:
            raise Exception("You need to use named args")

        super(StartEvent, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name)

