from typing import Optional

from adhesive.graph.Loop import Loop


class BaseTask:
    """
    Create a task. A task must have a name.
    Later this will be bounded to an actual implementation
    to be executed.
    """
    def __init__(self,
                 *args,
                 parent_process: Optional['Process'],
                 id: str,
                 name: str) -> None:
        if args:
            raise Exception("You need to use named parameters")

        if isinstance(parent_process, tuple):
            raise Exception("what")

        self.parent_process=parent_process
        self.id = id
        self.name = name
        self.error_task: Optional['ErrorBoundaryEvent'] = None
        self.loop: Optional[Loop] = None
        self.process_id: Optional[str] = None

    def __str__(self) -> str:
        return f"Task({self.id}): {self.name}"


# FIXME: this import should be done, for mypy
# from adhesive.graph.BoundaryEvent import ErrorBoundaryEvent
