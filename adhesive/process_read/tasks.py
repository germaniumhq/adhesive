import re

from adhesive import ExecutionTask, ExecutionUserTask
from adhesive.execution.ExecutionBaseTask import ExecutionBaseTask

from adhesive.graph.Process import Process
from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.model.generate_methods import generate_matching_re
from adhesive.process_read.programmatic import generate_from_calls


def generate_from_tasks(process: AdhesiveProcess) -> Process:
    if not process.task_definitions:
        raise Exception("No task was defined. You need to create "
                        "tasks with @adhesive.task or @adhesive.usertask .")

    builder = generate_from_calls(None)

    for task in process.task_definitions:
        expression = _escape_execution_task_expression(task)

        if isinstance(task, ExecutionTask):
            builder.task(expression,
                         when=task.when,
                         loop=task.loop,
                         lane=task.lane)
        elif isinstance(task, ExecutionUserTask):
            builder.user_task(expression,
                              when=task.when,
                              loop=task.loop,
                              lane=task.lane)
        else:
            raise Exception(f"Unsupported task {task}")

    builder.process_end()

    return builder.process


def _escape_execution_task_expression(task: ExecutionBaseTask) -> str:
    """
    When using just the adhesive.build() the user wants to use the names from
    the @task expression as simple names, not regex.
    :param task:
    :return:
    """
    expression = task.expressions[0]
    re_expression = generate_matching_re(expression)

    task.expressions = (re_expression,)
    task.re_expressions = (re.compile(re_expression),)

    return expression
