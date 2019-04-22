from typing import List, cast

from adhesive.graph.Edge import Edge
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Workflow import Workflow
from adhesive.model.ActiveEvent import ActiveEvent


class Gateway(BaseTask):
    pass


class NonWaitingGateway(Gateway):
    pass


class WaitingGateway(Gateway):
    pass
