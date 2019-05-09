from typing import List, cast

from adhesive.graph.Edge import Edge
from adhesive.graph.ExclusiveGateway import ExclusiveGateway
from adhesive.graph.Gateway import Gateway
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Workflow import Workflow
from adhesive.model.ActiveEvent import ActiveEvent


class GatewayController:
    @staticmethod
    def compute_outgoing_edges(workflow, event) -> List[Edge]:
        if isinstance(event.task, ExclusiveGateway):
            gateway = cast(Gateway, event.task)
            outgoing_edges = GatewayController.route_single_output(
                workflow, gateway, event)
        else:
            outgoing_edges = GatewayController.route_all_outputs(
                workflow, event.task, event)

        return outgoing_edges

    @staticmethod
    def route_single_output(
            workflow: Workflow,
            gateway: Gateway,
            event: ActiveEvent) -> List[Edge]:

        default_edge = None
        result_edge = None

        edges = workflow.get_outgoing_edges(gateway.id)

        for edge in edges:
            if not edge.condition:
                if default_edge is not None:
                    raise Exception(f"Duplicate default edge for gateway {gateway.id}.")

                default_edge = edge
                continue

            if eval(edge.condition, globals(), event.context.as_mapping()):
                if result_edge is not None:
                    raise Exception(f"Duplicate output edge for gateway {gateway.id}")

                result_edge = edge
                continue

        if result_edge is None and default_edge is not None:
            result_edge = default_edge

        if not result_edge:
            raise Exception(f"No branch matches on gateway {gateway.id}")

        return [result_edge]

    @staticmethod
    def route_all_outputs(
            workflow: Workflow,
            task: BaseTask,
            event: ActiveEvent) -> List[Edge]:

        result_edges = []
        edges = workflow.get_outgoing_edges(task.id)

        for edge in edges:
            # if we have no condition on the edge, we create an event for it
            if edge.condition and not eval(edge.condition, globals(), event.context.as_mapping()):
                continue

            result_edges.append(edge)

        return result_edges
