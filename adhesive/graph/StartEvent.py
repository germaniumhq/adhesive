from .BaseTask import BaseTask


class StartEvent(BaseTask):
    """
    StartEvent documentation.
    """
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super(StartEvent, self).__init__(_id, name)

