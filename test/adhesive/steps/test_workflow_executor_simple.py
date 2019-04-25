import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive, _async
from .check_equals import assert_equal_steps


class TestWorkflowExecutorSimple(unittest.TestCase):
    """
    Test if the workflow executor can execute simple workflows.
    """
    def test_simple_execution(self):
        """
        Load a simple workflow and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Ensure Docker Tooling": 1,
            "Build Germanium Image": 1,
            "Test Chrome": 1,
            "Test Firefox": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    """
    Test if the workflow executor can execute simple without waiting tasks.
    """
    def test_simple_execution_non_wait(self):
        """
        Load a simple workflow and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process, wait_tasks=False)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Ensure Docker Tooling": 1,
            "Build Germanium Image": 1,
            "Test Chrome": 1,
            "Test Firefox": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
