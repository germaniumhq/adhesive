import unittest
from typing import Optional, List

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.WorkflowContext import WorkflowContext
from adhesive.xml.bpmn import read_bpmn_file
from .test_tasks import adhesive, _async


class UIBuilder():
    def __init__(self,
                 context: WorkflowContext):
        self.context = context

    def add_text_input(self,
                       name: str,
                       title: Optional[str] = None,
                       value: Optional[str] = None) -> None:
        self.context.data[name] = name

    def add_combo_box(self,
                      name: str,
                      title: Optional[str] = None,
                      values: Optional[List[str]] = None):
        self.context.data[name] = values[0]

    def add_default_button(self,
                           name: str) -> None:
        self.context.data[name] = name


class TestUserTaskProvider(UserTaskProvider):
    def __init__(self):
        super(TestUserTaskProvider, self).__init__()

    def register_event(self,
                       executor: WorkflowExecutor,
                       event: ActiveEvent) -> None:
        try:
            ui = UIBuilder(event.context)

            adhesive_task = executor.tasks_impl[event.task.id]
            context = adhesive_task.invoke_user_task(event.context, ui)

            event.future.set_result(context)
        except Exception as e:
            event.future.set_exception(e)


class TestUserTaskBasic(unittest.TestCase):
    def test_link_back_execution(self):
        adhesive.process.workflow = read_bpmn_file("test/adhesive/xml/user-task.bpmn")

        workflow_executor = WorkflowExecutor(adhesive.process,
                                             ut_provider=TestUserTaskProvider())
        data = _async(workflow_executor.execute())

        self.assertEqual("OK", data.OK)
        self.assertEqual("Cancel", data.Cancel)
        self.assertEqual("branch", data.branch)
        self.assertEqual("12.0", data.version)

        self.assertFalse(workflow_executor.events)


if __name__ == '__main__':
    unittest.main()
