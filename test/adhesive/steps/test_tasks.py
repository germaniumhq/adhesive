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
    'Exclusive\ default\ branch',
    'Cleanup Broken Tasks'
)
def basic_task(context) -> None:
    add_current_task(context)


@adhesive.task(r'^Parallel \d+$')
def parallel_task(context) -> None:
    time.sleep(1)
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)


@adhesive.task(r'^Throw Some Exception$')
def throw_some_exception(context) -> None:
    add_current_task(context)

    raise Exception("broken")


@adhesive.task('Increment\ X\ by\ 1')
def increment_x_by_1(context):
    add_current_task(context)

    if not context.data.x:
        context.data.x = 1
        return

    context.data.x += 1


@adhesive.usertask('Read Data From User')
def read_data_from_user(context, ui) -> None:
    ui.add_text_input("branch", title="Branch")
    ui.add_combo_box("version", title="Version", values=["12.0", "12.1", "12.2", "12.3"])

    ui.add_default_button("OK")
    ui.add_default_button("Cancel")


def add_current_task(context):
    if not context.data.steps:
        context.data.steps = dict()

    if context.task.name not in context.data.steps:
        context.data.steps[context.task.name] = set()

    context.data.steps[context.task.name].add(str(uuid.uuid4()))
