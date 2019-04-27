import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from .check_equals import assert_equal_steps
from .test_tasks import adhesive, _async


class TestWorkflowExecutorBasic(unittest.TestCase):
    def test_link_back_execution(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/link-back.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Increment X by 1": 5,
            "Build Germanium Image": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
