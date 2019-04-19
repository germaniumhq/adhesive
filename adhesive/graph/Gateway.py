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

    def route_single_output(
            self,
            event: ActiveEvent,
            parent: ActiveEvent,
            edges: List[Edge]) -> ActiveEvent:

        workflow = cast(Workflow, parent.task)

        default_edge = None
        task = None

        for edge in edges:
            if not edge.condition:
                if default_edge is not None:
                    raise Exception("Duplicate default edge.")

                default_edge = edge
                continue

            if eval(edge.condition, globals(), event.context.as_mapping()):
                if task is not None:
                    raise Exception("Duplicate output edge 2")

                task = workflow.tasks[edge.target_id]
                continue

        if task is None and default_edge is not None:
            task = workflow.tasks[default_edge.target_id]

        if not task:
            raise Exception("No branch matches")

        return event.clone(self, parent)
