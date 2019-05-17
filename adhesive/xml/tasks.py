from adhesive import AdhesiveTask, AdhesiveUserTask
from adhesive.graph.Edge import Edge
from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.graph.Workflow import Workflow
from adhesive.model.AdhesiveProcess import AdhesiveProcess


current_id = 0


def next_id():
    global current_id

    current_id += 1
    return f"_{current_id}"


def generate_from_tasks(process: AdhesiveProcess) -> Workflow:
    workflow = Workflow(next_id())

    if not process.steps:
        raise Exception("No task was defined. You need to create "
                        "tasks with @adhesive.task or @adhesive.usertask .")

    last_task = StartEvent(next_id(), "start event")
    workflow.add_start_event(last_task)

    for step in process.steps:
        if isinstance(step, AdhesiveTask):
            task = Task(next_id(), step.expressions[0])
            workflow.add_task(task)
        elif isinstance(step, AdhesiveUserTask):
            task = UserTask(next_id(), step.expressions[0])
            workflow.add_task(task)
        else:
            raise Exception(f"Unsupported task {step}")

        edge = Edge(next_id(), last_task.id, task.id)
        workflow.add_edge(edge)
        last_task = task

    task = EndEvent(next_id(), "end event")
    workflow.add_end_event(task)

    edge = Edge(next_id(), last_task.id, task.id)
    workflow.add_edge(edge)

    return workflow
