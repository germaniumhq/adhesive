from typing import Any

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
            generator: Any) -> None:
        self.lane_id: str = lane_id
        self.workspace = workspace
        self.generator = generator
        self.references = 0

    def deallocate_lane(self):
        type(self.generator).__exit__(self.generator, None, None, None)

