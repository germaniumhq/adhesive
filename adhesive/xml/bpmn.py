import re
from typing import Tuple
from xml.etree import ElementTree

from adhesive.graph.Edge import Edge
from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.ExclusiveGateway import ExclusiveGateway
from adhesive.graph.ParallelGateway import ParallelGateway
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.Task import Task
from adhesive.graph.Workflow import Workflow

TAG_NAME = re.compile(r'^(\{.+\})?(.+)$')
SPACE = re.compile(r"\s+", re.IGNORECASE)

ignored_elements = {
    # we obviously ignore extensions.
    "extensionElements",
    # we ignore the incoming and outgoing from inside the subprocesses
    # because we use the sequenceFlow elements to trace the connections.
    "incoming",
    "outgoing",
}


def read_bpmn_file(file_name: str) -> Workflow:
    """ Read a BPMN file as a build workflow. """
    root_node = ElementTree.parse(file_name).getroot()
    process = find_node(root_node, 'process')

    return read_process(process)


def find_node(parent_node, name: str):
    for node in parent_node.getchildren():
        _, node_name = parse_tag(node)
        if node_name == name:
            return node

    return None


def read_process(process) -> Workflow:
    node_ns, node_name = parse_tag(process)

    if "process" == node_name:
        result = Workflow(process.get('id'))
    elif "subProcess" == node_name:
        result = SubProcess(process.get('id'), normalize_name(process.get('name')))
    else:
        raise Exception(f"Unknown process node: {process.tag}")

    # we read first the nodes, then the edges so they are findable
    # when adding the edges by id.
    for node in process.getchildren():
        process_node(result, node)

    for node in process.getchildren():
        process_edge(result, node)

    for task_id, task in result.tasks.items():
        if not result.has_incoming_edges(task):
            result.start_tasks[task.id] = task

    for task_id, task in result.tasks.items():
        if not result.has_outgoing_edges(task):
            result.end_events[task.id] = task

    return result


def process_node(result: Workflow,
                 node) -> None:
    node_ns, node_name = parse_tag(node)

    if "task" == node_name:
        process_node_task(result, node)
    elif "sequenceFlow" == node_name:
        pass
    elif "startEvent" == node_name:
        process_node_start_event(result, node)
    elif "endEvent" == node_name:
        process_node_end_event(result, node)
    elif "subProcess" == node_name:
        process_node_sub_process(result, node)
    elif "exclusiveGateway" == node_name:
        process_exclusive_gateway(result, node)
    elif "parallelGateway" == node_name:
        process_parallel_gateway(result, node)
    elif node_name not in ignored_elements:
        raise Exception(f"Unknown process node: {node.tag}")


def process_edge(result: Workflow,
                 node) -> None:
    node_ns, node_name = parse_tag(node)

    if "sequenceFlow" == node_name:
        process_node_sequence_flow(result, node)


def process_node_task(w: Workflow, xml_node) -> None:
    """ Create a Task element from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = Task(xml_node.get("id"), node_name)
    w.add_task(task)


def process_node_start_event(w: Workflow, xml_node) -> None:
    """ Create a start event from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = StartEvent(xml_node.get("id"), node_name)
    w.add_start_event(task)


def process_node_end_event(w: Workflow, xml_node) -> None:
    """ Create an end event from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = EndEvent(xml_node.get("id"), node_name)
    w.add_end_event(task)


def process_node_sub_process(w: Workflow, xml_node) -> None:
    task = read_process(xml_node)
    w.add_task(task)


def process_node_sequence_flow(w: Workflow, xml_node) -> None:
    edge = Edge(xml_node.get("id"),
                xml_node.get("sourceRef"),
                xml_node.get("targetRef"))

    condition_node = find_node(xml_node, "conditionExpression")

    if condition_node is not None:
        edge.condition = condition_node.text

    w.add_edge(edge)


def process_exclusive_gateway(w: Workflow, xml_node) -> None:
    """ Create an exclusive gateway from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = ExclusiveGateway(xml_node.get("id"), node_name)
    w.add_task(task)


def process_parallel_gateway(w: Workflow, xml_node) -> None:
    """ Create an end event from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = ParallelGateway(xml_node.get("id"), node_name)
    w.add_task(task)


def normalize_name(name: str) -> str:
    return SPACE.sub(' ', name)


def parse_tag(node) -> Tuple[str, str]:
    m = TAG_NAME.match(node.tag)

    if not m:
        raise Exception(f"Unable to parse tag name `{node}`")

    return m[1], m[2]

