from typing import List, Dict

from adhesive.execution.ExecutionMessageCallbackEvent import ExecutionMessageCallbackEvent
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask
from adhesive.execution.ExecutionLane import ExecutionLane
from adhesive.execution.ExecutionMessageEvent import ExecutionMessageEvent
from adhesive.graph.Process import Process
from .AdhesiveLane import AdhesiveLane


class AdhesiveProcess:
    """
    An Adhesive process. Holds the linkage between
    the graph, and the steps.
    """
    def __init__(self, id: str) -> None:
        self.lane_definitions: List[ExecutionLane] = []
        self.task_definitions: List[ExecutionBaseTask] = []
        self.message_definitions: List[ExecutionMessageEvent] = []
        self.message_callback_definitions: List[ExecutionMessageCallbackEvent] = []

        self.process: Process = Process(id=id)

        # map from lane key, to actual lane
        self.lanes: Dict[str, AdhesiveLane] = dict()
