import unittest
from adhesive.xml.bpmn import read_bpmn_file
from adhesive.graph.Workflow import Workflow


class TestReadingBpmn(unittest.TestCase):
    """
    Test if we can read a BPMN file correctly.
    """

    def test_reading_bpmn(self) -> None:
        """
        Try to see if reading a basic BPMN works.
        """
        workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        self.assertEqual(4, len(workflow.tasks))
        self.assertEqual(6, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_events))
        self.assertEqual(1, len(workflow.end_events))

        first_task = workflow.tasks["_3"]
        self.assertEqual("Build Germanium Image", first_task.name)

        self.assertTrue(workflow)


if __name__ == '__main__':
    unittest.main()
