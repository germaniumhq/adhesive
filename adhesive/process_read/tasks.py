from adhesive import ExecutionTask, ExecutionUserTask
from adhesive.graph.Process import Process
from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.process_read.programmatic import generate_from_calls


def generate_from_tasks(process: AdhesiveProcess) -> Process:
    if not process.execution:
        raise Exception("No task was defined. You need to create "
                        "tasks with @adhesive.task or @adhesive.usertask .")

    builder = generate_from_calls(None)

    for step in process.execution:
        if isinstance(step, ExecutionTask):
            builder.task(step.expressions[0],
                         when=step.when,
                         loop=step.loop)
        elif isinstance(step, ExecutionUserTask):
            builder.user_task(step.expressions[0],
                              when=step.when,
                              loop=step.loop)
        else:
            raise Exception(f"Unsupported task {step}")

    builder.process_end()

    return builder.process
