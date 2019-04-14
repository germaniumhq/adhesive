from .Task import Task


class StartEvent(Task):
    """
    StartEvent documentation.
    """
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        self.id = _id
        self.name = name

