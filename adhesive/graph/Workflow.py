from typing import Dict, List

import networkx as nx

from .BaseTask import BaseTask
from .StartEvent import StartEvent
from .EndEvent import EndEvent
from .Edge import Edge


class Workflow(BaseTask):
    """
    A workflow for the build
    """
    def __init__(self,
                 id: str,
                 name: str = '[root process]') -> None:
        super(Workflow, self).__init__(id, name)

        self._start_events: Dict[str, StartEvent] = dict()
        self._tasks: Dict[str, BaseTask] = dict()
        self._edges: Dict[str, Edge] = dict()
        self._end_events: Dict[str, EndEvent] = dict()

        self._graph = nx.MultiDiGraph()

    @property
    def start_tasks(self) -> Dict[str, StartEvent]:
        return self._start_events

    @property
    def tasks(self) -> Dict[str, BaseTask]:
        return self._tasks

    @property
    def edges(self) -> Dict[str, Edge]:
        return self._edges

    @property
    def end_events(self) -> Dict[str, EndEvent]:
        return self._end_events

    def add_task(self, task: BaseTask) -> None:
        """ Add a task into the graph. """
        self._tasks[task.id] = task

        if isinstance(task, Workflow):
            self._graph.add_nodes_from(task._graph.nodes)
            self._graph.add_edges_from(task._graph.edges)
            self._graph.add_node(f"{task.id}:start")
            self._graph.add_node(f"{task.id}:end")

            for start_task in task.start_tasks:
                self._graph.add_edge(f"{task.id}:start", start_task)
            for end_task in task.end_events:
                self._graph.add_edge(end_task, f"{task.id}:end")
        else:
            self._graph.add_node(task.id)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge into the graph. """
        self._edges[edge.id] = edge
        self._graph.add_edge(
            edge.source_id,
            edge.target_id)

    def add_start_event(self, event: StartEvent) -> None:
        self._start_events[event.id] = event
        self._tasks[event.id] = event

    def add_end_event(self, event: EndEvent) -> None:
        self._end_events[event.id] = event
        self._tasks[event.id] = event

    def get_outgoing_edges(self, task_id: str) -> List[Edge]:
        """ Get the outgoing edges. """
        result: List[Edge] = []

        for edge_id, edge in self._edges.items():
            if edge.source_id == task_id:
                result.append(edge)

        return result

    def has_incoming_edges(self, task: BaseTask) -> bool:
        for edge_id, edge in self._edges.items():
            if edge.target_id == task.id:
                return True

        return False

    def has_outgoing_edges(self, task: BaseTask) -> bool:
        for edge_id, edge in self._edges.items():
            if edge.source_id == task.id:
                return True

        return False

    def are_predecessors(self,
                         task: BaseTask,
                         potential_predecessors: List[BaseTask]) -> bool:
        for potential_predecessor in potential_predecessors:
            if nx.algorithms.has_path(
                    self._graph,
                    potential_predecessor.id,
                    task.id):
                return True
        return False
