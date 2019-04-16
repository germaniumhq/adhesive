import time
import unittest

import adhesive
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file


@adhesive.task(r'^Parallel \d+$')
def task_impl(context) -> None:
    time.sleep(1)
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)


class TestWorkflowExecutor(unittest.TestCase):
    def test_parallel_tasks(self):
        """
        Load a bunch of tasks in parallel.
        :return:
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/parallel5.bpmn")

        start_time = time.time() * 1000.0
        WorkflowExecutor(adhesive.process).execute()
        end_time = time.time() * 1000.0

        # the whole thing should be faster than 2 secs
        self.assertTrue(end_time - start_time < 2000)
        self.assertTrue(end_time - start_time >= 1000)


if __name__ == '__main__':
    unittest.main()
