import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from .test_tasks import adhesive, _async


class TestWorkflowExecutorSubProcess(unittest.TestCase):
    def test_sub_process_execution(self):
        """
        Load a workflow that contains a sub process and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        self.assertEqual({
            'Ensure Docker Tooling',
            'Build Germanium Image',
            'Prepare Firefox',
            'Test Firefox',
            'Test Chrome',
        }, data.steps.keys())
        self.assertFalse(workflow_executor.events.keys())


if __name__ == '__main__':
    unittest.main()
