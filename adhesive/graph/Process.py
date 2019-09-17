from typing import Dict, List, Iterator, Optional

import networkx as nx

from adhesive.graph.BoundaryEvent import BoundaryEvent, ErrorBoundaryEvent
from .BaseTask import BaseTask
from .StartEvent import StartEvent
from .EndEvent import EndEvent
from .Edge import Edge
from .Lane import Lane


class Process(BaseTask):
    """
    A process for the build
    """
    def __init__(self,
                 parent_process: Optional['Process'],
                 id: str,
                 name: str = '[root process]') -> None:
        super(Process, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name)

        self._start_events: Dict[str, StartEvent] = dict()
        self._tasks: Dict[str, BaseTask] = dict()
        self._edges: Dict[str, Edge] = dict()
        self._end_events: Dict[str, EndEvent] = dict()

        self._task_lane_map: Dict[str, Lane] = dict()
        self._default_lane = Lane("root", "default")

        self._lanes: Dict[str, Lane] = dict()

        self._graph = nx.MultiDiGraph()

    @property
    def start_tasks(self) -> Dict[str, StartEvent]:
        return self._start_events

    @property
    def tasks(self) -> Dict[str, BaseTask]:
        return self._tasks

    @property
    def lanes(self) -> Dict[str, Lane]:
        return self._lanes

    @property
    def edges(self) -> Dict[str, Edge]:
        return self._edges

    @property
    def end_events(self) -> Dict[str, EndEvent]:
        return self._end_events

    def add_task(self, task: BaseTask) -> None:
        """ Add a task into the graph. """
        self._tasks[task.id] = task
        self._graph.add_node(task.id)

        task.process_id = self.id

    def add_lane(self, lane: Lane) -> None:
        """
        Add a lane definition.
        """
        self._lanes[lane.name] = lane

    def add_task_to_lane(self, lane: Lane, task_id: str) -> None:
        """
        Assign a task to one of the lanes.
        """
        self._task_lane_map[task_id] = lane

    def get_lane_definition(self, task_id: str) -> Lane:
        """
        Fetches the lane definition that was associated with this
        task.
        """
        return self._task_lane_map.get(task_id, self._default_lane)

    def add_boundary_event(self, boundary_event: BoundaryEvent) -> None:
        self.add_task(boundary_event)
        self._graph.add_edge(
            boundary_event.attached_task_id,
            boundary_event.id,
            _edge=None)

        if isinstance(boundary_event, ErrorBoundaryEvent):
            self._tasks[boundary_event.attached_task_id].error_task = boundary_event

    def add_edge(self, edge: Edge) -> None:
        """Add an edge into the graph. """
        self._edges[edge.id] = edge
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            _edge=edge)

    def add_start_event(self, event: StartEvent) -> None:
        self._start_events[event.id] = event
        self.add_task(event)

    def add_end_event(self, event: EndEvent) -> None:
        self._end_events[event.id] = event
        self.add_task(event)

    def get_outgoing_edges(self, task_id: str) -> List[Edge]:
        """ Get the outgoing edges. """
        result: List[Edge] = []

        for from_node, to_node, data in self._graph.out_edges(task_id, data=True):
            if data["_edge"]:
                result.append(data["_edge"])

        return result

    def has_incoming_edges(self, task: BaseTask) -> bool:
        for from_node, to_node, data in self._graph.in_edges(task.id, data=True):
            if data["_edge"]:
                return True

        return False

    def has_outgoing_edges(self, task: BaseTask) -> bool:
        for from_node, to_node, data in self._graph.out_edges(task.id, data=True):
            if data["_edge"]:
                return True

        return False

    def are_predecessors(self,
                         task: BaseTask,
                         potential_predecessors: Iterator[BaseTask]) -> bool:
        predecessors = list(potential_predecessors)
        for potential_predecessor in predecessors:
            # FIXME: cross subprocess exceptions are handled as no predecessors
            try:
                if nx.algorithms.has_path(
                        self._graph,
                        potential_predecessor.id,
                        task.id):
                    return True
            except Exception as e:
                pass

        return False
