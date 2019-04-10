from typing import Tuple

from xml.etree import ElementTree
import re

from adhesive.graph.Workflow import Workflow
from adhesive.graph.Task import Task
from adhesive.graph.Edge import Edge
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.EndEvent import EndEvent

TAG_NAME = re.compile(r'^(\{.+\})?(.+)$')
SPACE = re.compile(r"\s+", re.IGNORECASE)


def read_bpmn_file(file_name: str) -> Workflow:
    """ Read a BPMN file as a build workflow. """
    result = Workflow()

    root_node = ElementTree.parse(file_name).getroot()
    process = find_node(root_node, 'process')

    for node in process.getchildren():
        process_node(result, node)

    return result


def find_node(parent_node, name: str):
    for node in parent_node.getchildren():
        _, node_name = parse_tag(name)
        if node_name == name:
            return node

    return None


def process_node(result: Workflow,
                 node) -> None:
    node_ns, node_name = parse_tag(node.tag)

    if "task" == node_name:
        process_node_task(result, node)
    elif "sequenceFlow" == node_name:
        process_node_sequence_flow(result, node)
    elif "startEvent" == node_name:
        process_node_start_event(result, node)
    elif "endEvent" == node_name:
        process_node_end_event(result, node)
    else:
        print(f"{node_name} node ignored")


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


def process_node_sequence_flow(w: Workflow, xml_node) -> None:
    edge = Edge(xml_node.get("id"),
                xml_node.get("sourceRef"),
                xml_node.get("targetRef"))
    w.add_edge(edge)


def normalize_name(name: str) -> str:
    return SPACE.sub(' ', name)


def parse_tag(name: str) -> Tuple[str, str]:
    m = TAG_NAME.match(name)

    if not m:
        raise Exception(f"Unable to parse tag name `{name}`")

    return m[1], m[2]

