from typing import Any, Optional

from adhesive.workspace import Workspace
from adhesive.execution.ExecutionLaneId import ExecutionLaneId


class AdhesiveLane:
    """
    An active lane used in a process.
    """
    def __init__(
            self,
            lane_id: ExecutionLaneId,
            workspace: Workspace,
            generator: Any,
            parent_lane: Optional['AdhesiveLane']=None) -> None:
        self.lane_id: str = lane_id
        self.workspace = workspace
        self.generator = generator
        self.references = 0
        self.parent_lane = parent_lane

    def deallocate_lane(self) -> None:
        type(self.generator).__exit__(self.generator, None, None, None)

    def increment_references(self) -> None:
        self.references += 1

        if self.parent_lane:
            self.parent_lane.increment_references()

    def decrement_references(self) -> None:
        self.references -= 1

        if self.parent_lane:
            self.parent_lane.decrement_references()

