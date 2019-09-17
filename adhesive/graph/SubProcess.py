
from .Process import Process
from .Lane import Lane


class SubProcess(Process):
    def __init__(self,
                 parent_process: Process,
                 id: str,
                 name: str):
        assert parent_process is not None

        super(SubProcess, self).__init__(parent_process=parent_process, id=id)
        self.name = name

        self.parent_process = parent_process

    def get_lane_definition(self, task_id: str) -> Lane:
        return self.parent_process.get_lane_definition(self.id)
