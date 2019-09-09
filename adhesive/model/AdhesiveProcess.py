from typing import List

from adhesive.graph.Process import Process
from adhesive.steps.AdhesiveBaseTask import AdhesiveBaseTask


class AdhesiveProcess:
    """
    An Adhesive process. Holds the linkage between
    the graph, and the steps.
    """
    def __init__(self, id: str) -> None:
        self.steps: List[AdhesiveBaseTask] = []
        self.process: Process = Process(id)
