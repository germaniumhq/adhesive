from adhesive import AdhesiveTask, AdhesiveUserTask
from adhesive.graph.Workflow import Workflow
from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.process_read.programmatic import generate_from_calls


def generate_from_tasks(process: AdhesiveProcess) -> Workflow:
    if not process.steps:
        raise Exception("No task was defined. You need to create "
                        "tasks with @adhesive.task or @adhesive.usertask .")

    builder = generate_from_calls(None)

    for step in process.steps:
        if isinstance(step, AdhesiveTask):
            builder.task(step.expressions[0],
                         when=step.when,
                         loop=step.loop)
        elif isinstance(step, AdhesiveUserTask):
            builder.user_task(step.expressions[0],
                              when=step.when,
                              loop=step.loop)
        else:
            raise Exception(f"Unsupported task {step}")

    builder.process_end()

    return builder.workflow
