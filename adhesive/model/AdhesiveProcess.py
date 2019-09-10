from typing import List

from adhesive.graph.Process import Process
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask


class AdhesiveProcess:
    """
    An Adhesive process. Holds the linkage between
    the graph, and the steps.
    """
    def __init__(self, id: str) -> None:
        self.steps: List[ExecutionBaseTask] = []
        self.process: Process = Process(id)
