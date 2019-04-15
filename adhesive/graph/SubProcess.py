
from .Workflow import Workflow


class SubProcess(Workflow):
    def __init__(self,
                 id: str,
                 name: str):
        super(SubProcess, self).__init__(id)
        self.name = name
