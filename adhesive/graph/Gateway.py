from typing import List, cast

from adhesive.graph.Edge import Edge
from adhesive.graph.Task import Task
from adhesive.graph.Workflow import Workflow
from adhesive.model.ActiveEvent import ActiveEvent


class Gateway(Task):
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super(Gateway, self).__init__(_id, name)

