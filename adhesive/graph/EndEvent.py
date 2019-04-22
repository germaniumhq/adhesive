from .BaseTask import BaseTask


class EndEvent(BaseTask):
    """
    EndEvent
    """
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super().__init__(_id, name)

