import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from test.adhesive.steps.check_equals import assert_equal_steps

from .test_tasks import adhesive, _async


class TestWorkflowExecutor(unittest.TestCase):
    """
    Test if the workflow executor can process exclusive gateways.
    """
    def test_exclusive_gateway(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/exclusive_gateway.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Populate task data": 1,
            "Exclusive default branch": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    def test_exclusive_gateway_non_wait(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/exclusive_gateway.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process, wait_tasks=False)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Populate task data": 1,
            "Exclusive default branch": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

if __name__ == '__main__':
    unittest.main()
