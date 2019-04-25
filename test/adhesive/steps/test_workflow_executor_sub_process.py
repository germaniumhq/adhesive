import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from test.adhesive.steps.check_equals import assert_equal_steps
from .test_tasks import adhesive, _async


class TestWorkflowExecutorSubProcess(unittest.TestCase):
    def test_sub_process_execution(self):
        """
        Load a workflow that contains a sub process and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            'Ensure Docker Tooling': 1,
            'Build Germanium Image': 1,
            'Prepare Firefox': 1,
            'Test Firefox': 1,
            'Test Chrome': 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events.keys())

    def test_sub_process_execution_non_wait(self):
        """
        Load a workflow that contains a sub process and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process, wait_tasks=True)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            'Ensure Docker Tooling': 1,
            'Build Germanium Image': 1,
            'Prepare Firefox': 1,
            'Test Firefox': 1,
            'Test Chrome': 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events.keys())

if __name__ == '__main__':
    unittest.main()
