
class BaseTask:
    """
    Create a task. A task must have a name.
    Later this will be bounded to an actual implementation
    to be executed.
    """
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        self.id = _id
        self.name = name

    def __str__(self) -> str:
        return f"Task({self.id}): {self.name}"
