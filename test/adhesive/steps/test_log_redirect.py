import glob
import os
import unittest

from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.process_read.bpmn import read_bpmn_file
import adhesive.config as config
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
            "sh: echo hello world && echo bad world >&2 && echo good world": 1,
            "Store current execution id": 1,
        }, data.steps)
        self.assertFalse(workflow_executor.events)

        adhesive_temp_folder = config.current.temp_folder
        path_to_glob = os.path.join(adhesive_temp_folder, data.execution_id, "logs", "_4", "*", "stdout")

        log_path = glob.glob(path_to_glob)

        with open(log_path[0], "rt") as f:
            self.assertEqual(f.read(), "sh: echo hello world && "
                                       "echo bad world >&2 && "
                                       "echo good world\nhello world\ngood world\n")

        log_path = glob.glob(os.path.join(
            adhesive_temp_folder,
            data.execution_id,
            "logs",
            "_4",
            "*",
            "stderr"))

        with open(log_path[0], "rt") as f:
            self.assertEqual(f.read(), "bad world\n")
