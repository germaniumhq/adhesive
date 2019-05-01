import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file

from .test_tasks import adhesive, _async
from .check_equals import assert_equal_steps


class TestErrorEventPropagatesUp(unittest.TestCase):
    """
    Test if the workflow executor can process parallel gateways.
    """
    def test_error_propagates_up(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/error-event-subprocess-propagates-up.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "Error Was Caught": 1,
        }, data.steps)

        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
