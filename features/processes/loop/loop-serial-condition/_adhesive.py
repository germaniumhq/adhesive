import adhesive
import unittest

test = unittest.TestCase()


@adhesive.task("Task")
def task(token):
    token.data.execution_count += 1
    token.data.parallel_check += token.loop.index
    print(token.loop.index)

    if token.loop.index >= 2:
        token.data.loop_condition = False


data = adhesive.bpmn_build(
    "loop-serial-condition.bpmn",
    initial_data={
        "loop_condition": "True",
        "execution_count": 0,
        "parallel_check": 1,
    },
)

test.assertEqual(3, data.execution_count)
test.assertEqual(5, data.parallel_check, "The loop probably didn't executed serially")
