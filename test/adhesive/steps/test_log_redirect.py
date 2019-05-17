import glob
import os
import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.xml.bpmn import read_bpmn_file
from test.adhesive.steps.check_equals import assert_equal_steps
from test.adhesive.steps.test_tasks import adhesive, _async


class TestIfLogRedirectionWorks(unittest.TestCase):
    """
    Test if the workflow executor can process inclusive gateways.
    """
    def test_log_redirection(self):
        """
        Load a workflow with a gateway and test it..
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/redirect-logs.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process)
        data = _async(workflow_executor.execute())

        assert_equal_steps({
            "sh: echo hello world": 1,
            "Store current execution id": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

        adhesive_temp_folder = os.environ.get("ADHESIVE_TEMP_FOLDER", "/tmp/adhesive")
        log_path = glob.glob(os.path.join(
            adhesive_temp_folder,
            data.execution_id,
            "logs",
            "_4",
            "*",
            "stdout"))

        with open(log_path[0], "rt") as f:
            self.assertEqual(f.read(), "sh: echo hello world\nhello world\n")
