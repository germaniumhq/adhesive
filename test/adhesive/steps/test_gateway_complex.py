import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.process_read.bpmn import read_bpmn_file
from test.adhesive.steps.check_equals import assert_equal_steps
from test.adhesive.steps.test_tasks import adhesive, _async


class TestGatewayComplex(unittest.TestCase):
    """
    Test if the workflow executor can process complex gateways.
    """
    def test_complex_gateway(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/gateway-complex.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Test Firefox": 1,
            "Test Chrome": 1,
            "Test Browser chrome on linux": 1,
            "Test Browser firefox on linux": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    def test_exclusive_gateway_non_wait(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/gateway-complex.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process, wait_tasks=False)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Test Firefox": 1,
            "Test Chrome": 1,
            "Test Browser chrome on linux": 2,
            "Test Browser firefox on linux": 2,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
