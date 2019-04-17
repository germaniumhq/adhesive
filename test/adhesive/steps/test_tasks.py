import adhesive
import time


@adhesive.task(
    'Ensure Docker Tooling',
    'Test Chrome',
    'Test Firefox',
    'Build Germanium Image',
    'Prepare Firefox')
def basic_task(context) -> None:
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)


@adhesive.task(r'^Parallel \d+$')
def parallel_task(context) -> None:
    time.sleep(1)
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)
