import re
from typing import Tuple
from xml.etree import ElementTree

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.BoundaryEvent import BoundaryEvent, ErrorBoundaryEvent
from adhesive.graph.Edge import Edge
from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.ExclusiveGateway import ExclusiveGateway
from adhesive.graph.Loop import Loop
from adhesive.graph.ScriptTask import ScriptTask
from adhesive.graph.UserTask import UserTask
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
    # we ignore text annotations, and associations
    "textAnnotation",
    "association"
}

boundary_ignored_elements = set(ignored_elements)
boundary_ignored_elements.add("outputSet")


def read_bpmn_file(file_name: str) -> Workflow:
    """ Read a BPMN file as a build workflow. """
    root_node = ElementTree.parse(file_name).getroot()
    process = find_node(root_node, 'process')

    return read_process(process)


def find_node(parent_node, name: str):
    for node in list(parent_node):
        _, node_name = parse_tag(node)
        if node_name == name:
            return node

    return None


def get_boolean(parent_node, attr: str, default_value: bool) -> bool:
    attr_value = parent_node.get(attr)

    if attr_value is None:
        return default_value

    if attr_value.upper() == "TRUE":
        return True
    elif attr_value.upper() == "FALSE":
        return False

    raise Exception(f"Not a boolean value for {attr}: {attr_value}")


def read_process(process) -> Workflow:
    node_ns, node_name = parse_tag(process)

    if "process" == node_name:
        result = Workflow(process.get('id'))
    elif "subProcess" == node_name:
        result = SubProcess(process.get('id'), normalize_name(process.get('name')))
    else:
        raise Exception(f"Unknown process node: {process.tag}")

    # we read first the nodes, then the boundary events,
    # then only the edges so they are findable
    # when adding the edges by id.
    for node in list(process):
        process_node(result, node)

    for node in list(process):
        process_boundary_event(result, node)

    for node in list(process):
        process_edge(result, node)

    for task_id, task in result.tasks.items():
        if isinstance(task, BoundaryEvent):
            continue

        if result.has_incoming_edges(task):
            continue

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
    elif "userTask" == node_name:
        process_user_task(result, node)
    elif "scriptTask" == node_name:
        process_script_task(result, node)
    elif "sequenceFlow" == node_name:
        pass
    elif "boundaryEvent" == node_name:
        pass
    elif "standardLoopCharacteristics" == node_name:
        pass
    elif "startEvent" == node_name:
        process_node_start_event(result, node)
    elif "endEvent" == node_name:
        process_node_end_event(result, node)
    elif "subProcess" == node_name:
        process_node_sub_process(result, node)
    elif "exclusiveGateway" == node_name:
        process_exclusive_gateway(result, node)
    elif "parallelGateway" == node_name or "inclusiveGateway" == node_name:
        process_parallel_gateway(result, node)
    elif node_name not in ignored_elements:
        raise Exception(f"Unknown process node: {node.tag}")


def process_boundary_event(result: Workflow,
                           node) -> None:
    node_ns, node_name = parse_tag(node)

    if "boundaryEvent" == node_name:
        process_boundary_task(result, node)


def process_edge(result: Workflow,
                 node) -> None:
    node_ns, node_name = parse_tag(node)

    if "sequenceFlow" == node_name:
        process_node_sequence_flow(result, node)


def process_node_task(w: Workflow, xml_node) -> None:
    """ Create a Task element from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = Task(xml_node.get("id"), node_name)

    task = process_potential_loop(task, xml_node)

    w.add_task(task)


def process_user_task(w: Workflow, xml_node) -> None:
    """ Create a HumanTask element from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    task = UserTask(xml_node.get("id"), node_name)

    task = process_potential_loop(task, xml_node)

    w.add_task(task)


def process_script_task(w: Workflow, xml_node) -> None:
    """ Create a ScriptTask element from the workflow """
    node_name = normalize_name(xml_node.get("name"))
    language = xml_node.get("scriptFormat")

    script_node = find_node(xml_node, "script")

    task = ScriptTask(
        xml_node.get("id"),
        node_name,
        language=language,
        script=script_node.text)

    task = process_potential_loop(task, xml_node)

    w.add_task(task)


def process_boundary_task(w: Workflow, xml_node) -> None:
    """ Create a Task element from the workflow """
    for node in list(xml_node):
        node_ns, node_name = parse_tag(node)

        if node_name in boundary_ignored_elements:
            continue

        # node is not ignored, we either found the type
        # or we die with exception.
        task_name = normalize_name(xml_node.get("name"))

        if node_name == "errorEventDefinition":
            boundary_task = ErrorBoundaryEvent(
                xml_node.get("id"),
                task_name)

            boundary_task.attached_task_id = xml_node.get(
                "attachedToRef", default="not attached")

            boundary_task.cancel_activity = get_boolean(
                xml_node, "cancelActivity", True)
            boundary_task.parallel_multiple = get_boolean(
                xml_node, "parallelMultiple", True)

            w.add_boundary_event(boundary_task)

            return

    raise Exception("Unable to find the type of the boundary event. Only "
                    "<errorEventDefinition> is supported.")


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
    task = process_potential_loop(task, xml_node)

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


def process_potential_loop(task: BaseTask, xml_node) -> BaseTask:
    loop_node = find_node(xml_node, "standardLoopCharacteristics")

    if not loop_node:
        return task

    loop_expression = find_node(loop_node, "loopCondition")
    task.loop = Loop(loop_expression=loop_expression.text)

    return task


def normalize_name(name: str) -> str:
    if not name:
        return "<noname>"

    return SPACE.sub(' ', name)


def parse_tag(node) -> Tuple[str, str]:
    m = TAG_NAME.match(node.tag)

    if not m:
        raise Exception(f"Unable to parse tag name `{node}`")

    return m[1], m[2]
