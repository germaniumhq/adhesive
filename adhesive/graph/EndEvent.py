from .Task import Task

class EndEvent(Task):
    """
    EndEvent
    """
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super().__init__(_id, name)

