import unittest

from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.process_read.bpmn import read_bpmn_file

from test.adhesive.execution.test_tasks import adhesive, _async
from test.adhesive.execution.check_equals import assert_equal_execution


class TestLane(unittest.TestCase):
    """
    Test if the process executor can process parallel gateways.
    """
    def test_lane(self):
        """
        Load a process with a gateway and test it..
        """
        adhesive.process.process = read_bpmn_file("test/adhesive/xml/lane.bpmn")

        process_executor = ProcessExecutor(adhesive.process)
        data = _async(process_executor.execute())

        assert_equal_execution({
            "Test Chrome": 3,
            "Build Germanium Image": 3,
        }, data.executions)
        self.assertFalse(process_executor.events)

    def test_lane_non_wait(self):
        """
        Load a process with a gateway and test it..
        """
        adhesive.process.process = read_bpmn_file("test/adhesive/xml/lane.bpmn")

        process_executor = ProcessExecutor(adhesive.process)
        data = _async(process_executor.execute())

        assert_equal_execution({
            "Test Chrome": 3,
            "Build Germanium Image": 3,
        }, data.executions)
        self.assertFalse(process_executor.events)


if __name__ == '__main__':
    unittest.main()
