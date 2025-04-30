import adhesive
import unittest

test = unittest.TestCase()


@adhesive.task("Task")
def task(token):
    print(f"token loop index: {token.loop.index}")

    token.data.execution_count += 1
    token.data.parallel_check += token.loop.index

    token.data.loop_condition = True

    if token.loop.index >= 2:
        token.data.loop_condition = "False"


data = adhesive.bpmn_build(
    "loop-serial-condition.bpmn",
    initial_data={
        "loop_condition": "True",  # this should be converted to a boolean if it's a str/int
        "execution_count": 0,
        "parallel_check": 1,
    },
)

test.assertEqual(3, data.execution_count)
test.assertEqual(4, data.parallel_check, "The loop probably didn't executed serially")
