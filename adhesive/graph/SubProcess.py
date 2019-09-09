
from .Process import Process


class SubProcess(Process):
    def __init__(self,
                 id: str,
                 name: str):
        super(SubProcess, self).__init__(id)
        self.name = name
