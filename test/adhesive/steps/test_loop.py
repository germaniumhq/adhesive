import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from test.adhesive.steps.check_equals import assert_equal_steps
from test.adhesive.steps.test_tasks import adhesive, _async


class TestLoopExecution(unittest.TestCase):

    def test_loop_execution(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/loop.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            'Build Germanium Image on mac': 1,
            'Build Germanium Image on windows': 1,
            'Build Germanium Image on linux': 1,
            'Test Browser ie on linux': 1,
            'Cleanup Platform linux': 1,
            'Cleanup Platform windows': 1,
            'Cleanup Platform mac': 1,
            'Test Browser chrome on linux': 1,
            'Test Browser edge on linux': 1,
            'Test Browser edge on windows': 1,
            'Test Browser chrome on windows': 1,
            'Test Browser ie on windows': 1,
            'Test Browser chrome on mac': 1,
            'Test Browser edge on mac': 1,
            'Test Browser ie on mac': 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    def test_loop_execution_no_wait(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/loop.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process, wait_tasks=False)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            'Build Germanium Image on mac': 1,
            'Build Germanium Image on windows': 1,
            'Build Germanium Image on linux': 1,
            'Test Browser ie on linux': 1,
            'Cleanup Platform linux': 3,
            'Cleanup Platform windows': 3,
            'Cleanup Platform mac': 3,
            'Test Browser chrome on linux': 1,
            'Test Browser edge on linux': 1,
            'Test Browser edge on windows': 1,
            'Test Browser chrome on windows': 1,
            'Test Browser ie on windows': 1,
            'Test Browser chrome on mac': 1,
            'Test Browser edge on mac': 1,
            'Test Browser ie on mac': 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
