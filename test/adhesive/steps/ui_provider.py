from typing import Optional, List

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.steps.WorkflowContext import WorkflowContext


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

