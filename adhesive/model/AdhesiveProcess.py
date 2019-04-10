from typing import List

from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.graph.Workflow import Workflow


class AdhesiveProcess:
    """
    An Adhesive process. Holds the linkage between
    the graph, and the steps.
    """
    def __init__(self) -> None:
        self.steps: List[AdhesiveTask] = []
        self.workflow: Workflow = Workflow()
