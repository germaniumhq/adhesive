import adhesive
import uuid
import unittest

test = unittest.TestCase()


@adhesive.task('Running (.*) on (.*)')
def run_simple_task(context, task_name, platform):
    print(f"Running {task_name} on {platform}")
    context.data.execution_count.add(str(uuid.uuid4()))


data = adhesive.process_start()\
    .sub_process_start("Run builds on {loop.value}", loop="platforms")\
        .task("Running {loop.value} on {loop.parent_loop.value}", loop="tasks")\
    .sub_process_end()\
    .build(initial_data={
        "execution_count": set(),
        "platforms": ["linux", "windows", "solaris"],
        "tasks": ["archive", "compute", "list"],
    })

test.assertEqual(9, len(data.execution_count))
