import unittest

from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.process_read.bpmn import read_bpmn_file

from .test_tasks import adhesive, _async
from .check_equals import assert_equal_steps


class TestScriptTask(unittest.TestCase):
    """
    Test if the process executor can process script tasks.
    """
    def test_script_task_execution(self):
        adhesive.process.process = read_bpmn_file("test/adhesive/xml/script.bpmn")

        process_executor = ProcessExecutor(adhesive.process)
        data = _async(process_executor.execute())

        assert_equal_steps({
            'Script Task': 1,
            'Build Germanium Image': 1,
        }, data.steps)

        self.assertFalse(process_executor.events,
                         "Some events were not unregistered and/or executed.")
