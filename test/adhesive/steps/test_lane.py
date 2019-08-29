import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.process_read.bpmn import read_bpmn_file

from test.adhesive.steps.test_tasks import adhesive, _async
from test.adhesive.steps.check_equals import assert_equal_steps


class TestLane(unittest.TestCase):
    """
    Test if the workflow executor can process parallel gateways.
    """
    def test_lane(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/lane.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Test Chrome": 3,
            "Build Germanium Image": 3,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

    def test_lane_non_wait(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/lane.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Test Chrome": 3,
            "Build Germanium Image": 3,
        }, data.steps)
        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
