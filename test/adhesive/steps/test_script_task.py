import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive, _async
from .check_equals import assert_equal_steps


class TestScriptTask(unittest.TestCase):
    """
    Test if the workflow executor can process script tasks.
    """
    def test_script_task_execution(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/script.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            'Script Task': 1,
            'Build Germanium Image': 1,
        }, data.steps)

        self.assertFalse(workflow_executor.events,
                         "Some events were not unregistered and/or executed.")
