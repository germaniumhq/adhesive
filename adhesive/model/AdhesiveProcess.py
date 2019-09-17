from typing import List, Dict

from adhesive.graph.Process import Process
from adhesive.execution.ExecutionLane import ExecutionLane
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from .AdhesiveLane import AdhesiveLane


class AdhesiveProcess:
    """
    An Adhesive process. Holds the linkage between
    the graph, and the steps.
    """
    def __init__(self, id: str) -> None:
        self.lane_definitions: List[ExecutionLane] = []
        self.task_definitions: List[ExecutionBaseTask] = []

        self.process: Process = Process(parent_process=None, id=id)

        # map from lane key, to actual lane
        self.lanes: Dict[str, AdhesiveLane] = dict()
