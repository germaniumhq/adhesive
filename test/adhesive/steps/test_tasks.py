import adhesive
import time
import asyncio
import uuid


def _async(fn):
    data = asyncio.get_event_loop().run_until_complete(fn)
    return data

@adhesive.task(
    'Ensure Docker Tooling',
    'Test Chrome',
    'Test Firefox',
    'Build Germanium Image',
    'Prepare Firefox',
    # exclusive gateway
    'Exclusive\ Task\ Branch',
    'Populate\ task\ data',
    'Exclusive\ default\ branch'
)
def basic_task(context) -> None:
    if not context.data.steps:
        context.data.steps = dict()

    if context.task.name not in context.data.steps:
        context.data.steps[context.task.name] = set()

    context.data.steps[context.task.name].add(str(uuid.uuid4()))


@adhesive.task(r'^Parallel \d+$')
def parallel_task(context) -> None:
    time.sleep(1)
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)
