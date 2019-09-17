from typing import List, cast, Any

from adhesive.graph.Edge import Edge
from adhesive.graph.ExclusiveGateway import ExclusiveGateway
from adhesive.graph.Gateway import Gateway
from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Process import Process
from adhesive.model.ActiveEvent import ActiveEvent

from adhesive.execution import token_utils


class GatewayController:
    @staticmethod
    def compute_outgoing_edges(process, event) -> List[Edge]:
        if isinstance(event.task, ExclusiveGateway):
            gateway = cast(Gateway, event.task)
            outgoing_edges = GatewayController.route_single_output(
                process, gateway, event)
        else:
            outgoing_edges = GatewayController.route_all_outputs(
                process, event.task, event)

        return outgoing_edges

    @staticmethod
    def route_single_output(
            process: Process,
            gateway: Gateway,
            event: ActiveEvent) -> List[Edge]:

        default_edge = None
        result_edge = None

        edges = process.get_outgoing_edges(gateway.id)

        for edge in edges:
            if not edge.condition:
                if default_edge is not None:
                    raise Exception(f"Duplicate default edge for gateway {gateway.id}.")

                default_edge = edge
                continue

            if eval_edge(edge.condition, event):
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
            process: Process,
            task: BaseTask,
            event: ActiveEvent) -> List[Edge]:

        result_edges = []
        edges = process.get_outgoing_edges(task.id)

        for edge in edges:
            # if we have no condition on the edge, we create an event for it
            if edge.condition and not eval_edge(edge.condition, event):
                continue

            result_edges.append(edge)

        return result_edges


def eval_edge(condition: str,
              event: ActiveEvent) -> Any:
    eval_data = token_utils.get_eval_data(event.context)

    return eval(condition, globals(), eval_data)

