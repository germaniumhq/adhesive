import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.process_read.bpmn import read_bpmn_file

from test.adhesive.steps.test_tasks import adhesive, _async
from test.adhesive.steps.check_equals import assert_equal_steps


class TestErrorEventInterrupting(unittest.TestCase):
    """
    Test if the workflow executor can process parallel gateways.
    """
    def test_error_interrupting(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/error-event-interrupting.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        print(data._error)

        assert_equal_steps({
            "Cleanup Broken Tasks": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
