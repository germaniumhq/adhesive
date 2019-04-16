import unittest

import adhesive
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.WorkflowData import WorkflowData
from adhesive.xml.bpmn import read_bpmn_file


@adhesive.task('.*')
def task_impl(context) -> None:
    if not context.data.steps:
        context.data.steps = set()

    context.data.steps.add(context.task.name)


class TestWorkflowExecutor(unittest.TestCase):
    """
    Test if the workflow executor can execute simple workflows.
    """
    def test_simple_execution(self):
        """
        Load a simple workflow and execute it.
        """
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive.bpmn")

        data = WorkflowExecutor(adhesive.process).execute()

        self.assertEqual(data.steps, {
            "Ensure Docker Tooling",
            "Build Germanium Image",
            "Test Chrome",
            "Test Firefox",
        })

    # def test_sub_process_execution(self):
    #     """
    #     Load a workflow that contains a sub process and execute it.
    #     """
    #     adhesive.process = AdhesiveProcess("x")
    #     executed_steps: Set[str] = set()
    #
    #     adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/adhesive_subprocess.bpmn")
    #
    #     WorkflowExecutor(adhesive.process).execute()
    #     self.assertEqual(executed_steps, {
    #         'Ensure Docker Tooling',
    #         'Build Germanium Image',
    #         'Prepare Firefox',
    #         'Test Firefox',
    #         'Test Chrome',
    #     })


if __name__ == '__main__':
    unittest.main()
