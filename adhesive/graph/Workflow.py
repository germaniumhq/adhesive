from typing import Dict
from .Task import Task


class Workflow:
    """
    A workflow for the build
    """
    def __init__(self) -> None:
        self._start_events: Dict[str, StartEvent] = dict()
        self._tasks: Dict[str, Task] = dict()
        self._edges: Dect[str, Edge] = dict()
        self._end_events: Dict[str, EndEvent] = dict()

