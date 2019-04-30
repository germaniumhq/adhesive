from typing import Optional, List, Dict, Any

import npyscreen as npyscreen

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor


# FIXME: Not sure if this is the best place
# FIXME: UIBuilder should be probably a common class with the tests
from adhesive.steps.WorkflowData import WorkflowData


class UIBuilder:
    def __init__(self,
                 event: ActiveEvent):
        self.context = event.context
        self.ui_controls: Dict[str, Any] = dict()

        self.form = npyscreen.Form(name=event.task.name)

    @property
    def data(self) -> WorkflowData:
        result_dict = dict()

        for name, ui_control in self.ui_controls.items():
            result_dict[name] = ui_control.value

        return WorkflowData(result_dict)

    def add_text_input(self,
                       name: str,
                       title: Optional[str] = None,
                       value: str = '') -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitleText,
            name=title,
            value=value)

    def add_combo_box(self,
                      name: str,
                      title: Optional[str] = None,
                      values: Optional[List[Any]] = None):
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitleCombo,
            name=title,
            values=values)

    def add_default_button(self,
                           name: str) -> None:
        self.context.data[name] = name


class ConsoleUserTaskProvider(UserTaskProvider):
    def __init__(self):
        super(ConsoleUserTaskProvider, self).__init__()

    def register_event(self,
                       executor: WorkflowExecutor,
                       event: ActiveEvent) -> None:
        def run_on_curses(x):
            try:
                ui = UIBuilder(event)

                adhesive_task = executor.tasks_impl[event.task.id]
                context = adhesive_task.invoke_user_task(event.context, ui)

                # call the actual UI
                ui.form.edit()

                # put the values in the data.
                context.data = WorkflowData.merge(context.data, ui.data)

                event.future.set_result(context)
            except Exception as e:
                event.future.set_exception(e)

        npyscreen.wrapper_basic(run_on_curses)
