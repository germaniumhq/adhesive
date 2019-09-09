import unittest

from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.process_read.bpmn import read_bpmn_file

from test.adhesive.steps.test_tasks import adhesive, _async
from test.adhesive.steps.check_equals import assert_equal_steps


class TestErrorEventInterrupting(unittest.TestCase):
    """
    Test if the process executor can process parallel gateways.
    """
    def test_error_interrupting(self):
        """
        Load a process with a gateway and test it..
        """
        adhesive.process.process = read_bpmn_file("test/adhesive/xml/error-event-interrupting.bpmn")

        process_executor = ProcessExecutor(adhesive.process)
        data = _async(process_executor.execute())

        print(data._error)

        assert_equal_steps({
            "Cleanup Broken Tasks": 1,
        }, data.steps)
        self.assertFalse(process_executor.events)


if __name__ == '__main__':
    unittest.main()
