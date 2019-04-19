import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive


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
        data = workflow_executor.execute()

        self.assertEqual({
            "Ensure Docker Tooling",
            "Build Germanium Image",
            "Test Chrome",
            "Test Firefox",
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
