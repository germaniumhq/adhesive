import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from test.adhesive.steps.ui_provider import TestUserTaskProvider
from .test_tasks import adhesive, _async


class TestUserTaskBasic(unittest.TestCase):
    def test_link_back_execution(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/user-task.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process,
                                             ut_provider=TestUserTaskProvider())
        data = _async(workflow_executor.execute())

        self.assertEqual("OK", data.OK)
        self.assertEqual("Cancel", data.Cancel)
        self.assertEqual("branch", data.branch)
        self.assertEqual("12.0", data.version)
        self.assertEqual("password", data.password)
        self.assertEqual(('integration',), data.run_tests)

        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
