import unittest
from adhesive.xml.bpmn import read_bpmn_file
from adhesive.graph import Workflow


class TestReadingBpmn(unittest.TestCase):
    """
    Test if we can read a BPMN file correctly.
    """

    def test_reading_bpmn(self) -> Workflow:
        """
        Try to see if reading a basic BPMN works.
        """
        workflow = read_bpmn_file("test/simple.bpmn")

        self.assertTrue(workflow)


if __name__ == '__main__':
    unittest.main()
