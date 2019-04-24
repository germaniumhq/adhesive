import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from .test_tasks import adhesive, _async


class TestGatewayParallel(unittest.TestCase):
    """
    Test if the workflow executor can process parallel gateways.
    """
    def test_parallel_gateway(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/gateway-parallel.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        self.assertEqual({
            "Test Chrome": [1, 1, 1, 1, 1, 1, 1, 1, 1],
            "Build Germanium Image": [1, 1, 1],
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
