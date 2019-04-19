import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive


class TestWorkflowExecutor(unittest.TestCase):
    """
    Test if the workflow executor can execute simple workflows.
    """
    def test_simple_execution(self):
        """
        Load a simple workflow and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = workflow_executor.execute()

        self.assertEqual({
            "Ensure Docker Tooling",
            "Build Germanium Image",
            "Test Chrome",
            "Test Firefox",
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    def test_sub_process_execution(self):
        """
        Load a workflow that contains a sub process and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = workflow_executor.execute()

        self.assertEqual({
            'Ensure Docker Tooling',
            'Build Germanium Image',
            'Prepare Firefox',
            'Test Firefox',
            'Test Chrome',
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
