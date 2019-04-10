from typing import Dict, Iterable, List

from .Task import Task
from .StartEvent import StartEvent
from .EndEvent import EndEvent
from .Edge import Edge


class Workflow:
    """
    A workflow for the build
    """
    def __init__(self) -> None:
        self._start_events: Dict[str, StartEvent] = dict()
        self._tasks: Dict[str, Task] = dict()
        self._edges: Dict[str, Edge] = dict()
        self._end_events: Dict[str, EndEvent] = dict()

    @property
    def start_events(self) -> Dict[str, StartEvent]:
        return self._start_events

    @property
    def tasks(self) -> Dict[str, Task]:
        return self._tasks

    @property
    def edges(self) -> Dict[str, Edge]:
        return self._edges

    @property
    def end_events(self) -> Dict[str, EndEvent]:
        return self._end_events

    def add_task(self, task: Task) -> None:
        """ Add a task into the graph. """
        self._tasks[task.id] = task

    def add_edge(self, edge: Edge) -> None:
        """ Add an edge into the graph. """
        self._edges[edge._id] = edge

    def add_start_event(self, event: StartEvent) -> None:
        self._start_events[event._id] = event

    def add_end_event(self, event: EndEvent) -> None:
        self._end_events[event._id] = event

    def get_outgoing_edges(self, task_id: str) -> Iterable[Edge]:
        """ Get the outgoing edges. """
        result: List[Edge] = []

        for edge_id, edge in self._edges.items():
            if edge.source_id == task_id:
                result.append(edge)

        return result
