from typing import cast
import unittest
import textwrap

from adhesive.graph.BoundaryEvent import ErrorBoundaryEvent
from adhesive.graph.ExclusiveGateway import ExclusiveGateway
from adhesive.graph.Loop import Loop
from adhesive.graph.ScriptTask import ScriptTask
from adhesive.graph.UserTask import UserTask
from adhesive.graph.ParallelGateway import ParallelGateway
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.Task import Task
from adhesive.xml.bpmn import read_bpmn_file


class TestReadingBpmn(unittest.TestCase):
    """
    Test if we can read a BPMN file correctly.
    """

    def test_reading_bpmn(self) -> None:
        """
        Try to see if reading a basic BPMN works.
        """
        workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        self.assertEqual(6, len(workflow.tasks))
        self.assertEqual(6, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        first_task = workflow.tasks["_3"]
        self.assertEqual("Build Germanium Image", first_task.name)

        self.assertTrue(workflow)

    def test_reading_subprocess_bpmn(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")

        self.assertEqual(5, len(workflow.tasks))
        self.assertEqual(4, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        subprocess = cast(SubProcess, workflow.tasks["_7"])
        self.assertEqual("Test Browsers", subprocess.name)

        self.assertEqual(3, len(subprocess.tasks))
        self.assertEqual(1, len(subprocess.edges))
        self.assertEqual(2, len(subprocess.start_tasks))
        self.assertEqual(2, len(subprocess.end_events))

    def test_reading_exclusive_gateway_bpmn(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/exclusive_gateway.bpmn")

        self.assertEqual(6, len(workflow.tasks))
        self.assertEqual(6, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        task_route = workflow.edges["_9"]
        self.assertEqual('data.route == "task"', task_route.condition)

        task_route = workflow.edges["_10"]
        self.assertEqual('', task_route.condition)

    def test_reading_parallel_gateway_bpmn(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/gateway-parallel.bpmn")

        self.assertEqual(9, len(workflow.tasks))
        self.assertEqual(12, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(workflow.tasks["_9"], ParallelGateway))

    def test_reading_gateway_exclusive_sign_bpmn(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/gateway-exclusive-sign.bpmn")

        self.assertEqual(7, len(workflow.tasks))
        self.assertEqual(8, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(workflow.tasks["_3"], ExclusiveGateway))

    def test_reading_gateway_inclusive_sign_bpmn(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/gateway-inclusive.bpmn")

        self.assertEqual(8, len(workflow.tasks))
        self.assertEqual(10, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(workflow.tasks["_3"], ParallelGateway))

    def test_reading_error_event_interrupting(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/error-event-interrupting.bpmn")

        self.assertEqual(6, len(workflow.tasks))
        self.assertEqual(5, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        boundary_event: ErrorBoundaryEvent = workflow.tasks["_6"]
        self.assertTrue(isinstance(
            workflow.tasks["_6"],
            ErrorBoundaryEvent
        ))

        self.assertTrue(boundary_event.cancel_activity)
        self.assertFalse(boundary_event.parallel_multiple)

        parent_event: Task = workflow.tasks['_3']
        self.assertEqual(parent_event.error_task, boundary_event)

    def test_reading_human_task(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/user-task.bpmn")

        self.assertEqual(3, len(workflow.tasks))
        self.assertEqual(2, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(
            workflow.tasks["_3"],
            UserTask
        ))

    def test_reading_script_task(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/script.bpmn")

        self.assertEqual(4, len(workflow.tasks))
        self.assertEqual(3, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(
            workflow.tasks["_3"],
            ScriptTask
        ))

        script_task: ScriptTask = workflow.tasks["_3"]
        self.assertEqual("text/python", script_task.language)
        self.assertEqual(textwrap.dedent("""\
            import uuid
            
            if not context.data.steps:
                context.data.steps = dict()
            
            if context.task.name not in context.data.steps:
                context.data.steps[context.task.name] = set()
            
            context.data.steps[context.task.name].add(str(uuid.uuid4()))"""), script_task.script)

    def test_reading_loop(self) -> None:
        workflow = read_bpmn_file("test/adhesive/xml/loop.bpmn")

        self.assertEqual(5, len(workflow.tasks))
        self.assertEqual(5, len(workflow.edges))
        self.assertEqual(1, len(workflow.start_tasks))
        self.assertEqual(1, len(workflow.end_events))

        self.assertTrue(isinstance(
            workflow.tasks["_5"],
            Task
        ))

        loop: Loop = workflow.tasks["_5"].loop
        self.assertEqual("data.test_platforms", loop.loop_expression)

    def test_reading_unsupported_elements_fails(self) -> None:
        with self.assertRaises(Exception):
            read_bpmn_file("test/adhesive/xml/unsupported-call-activity.bpmn")


if __name__ == '__main__':
    unittest.main()
