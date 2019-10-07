from typing import Optional

from adhesive.graph.Loop import Loop
from .Lane import Lane
from .Process import Process


class SubProcess(Process):
    def __init__(self,
                 *args,
                 parent_process: Process,
                 id: str,
                 name: str):
        if args:
            raise Exception("You need to pass arguments by name")

        super(SubProcess, self).__init__(
            id=id,
            name=name)

        self.parent_process = parent_process
        self.loop: Optional[Loop] = None
        self.error_task = None

    def get_lane_definition(self, task_id: str) -> Lane:
        return self.parent_process.get_lane_definition(self.id)
