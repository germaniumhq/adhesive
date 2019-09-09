import unittest

from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.process_read.bpmn import read_bpmn_file
from .check_equals import assert_equal_steps
from .test_tasks import adhesive, _async


class TestProcessExecutorBasic(unittest.TestCase):
    """
    Run a process with a single task.
    """
    def test_basic_execution(self):
        """
        Load a simple process and execute it.
        """
        adhesive.process.process = read_bpmn_file("test/adhesive/xml/adhesive-basic.bpmn")

        process_executor = ProcessExecutor(adhesive.process)
        data = _async(process_executor.execute())

        assert_equal_steps({
            "Build Germanium Image": 1,
        }, data.steps)
        self.assertFalse(process_executor.events)


if __name__ == '__main__':
    unittest.main()
