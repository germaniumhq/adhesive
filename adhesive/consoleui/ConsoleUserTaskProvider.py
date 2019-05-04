from typing import Optional, List, Dict, Any, cast, Tuple, Union, Iterable

import npyscreen as npyscreen

from adhesive.model.UiBuilderApi import UiBuilderApi
from adhesive.steps.AdhesiveUserTask import AdhesiveUserTask
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor

from adhesive.steps.WorkflowData import WorkflowData


class UIBuilder(UiBuilderApi):
    def __init__(self,
                 event: ActiveEvent):
        self.context = event.context
        self.ui_controls: Dict[str, Any] = dict()

        self.labels: Dict[str, List[str]] = dict()
        self.values: Dict[str, List[str]] = dict()

        self.form = npyscreen.Form(
            name=event.task.name)

    @property
    def data(self) -> WorkflowData:
        result_dict = dict()

        for name, ui_control in self.ui_controls.items():
            if isinstance(self.ui_controls[name], npyscreen.TitleMultiSelect):
                result = {self.values[name][it] for it in ui_control.value}
                result_dict[name] = result
                continue

            if isinstance(self.ui_controls[name], npyscreen.TitleCombo):
                result = self.values[name][ui_control.value] if ui_control.value >= 0 else None
                result_dict[name] = result
                continue

            if isinstance(self.ui_controls[name], npyscreen.TitleSelectOne):
                result = self.values[name][ui_control.value[0]] if len(ui_control.value) > 0 else None
                result_dict[name] = result
                continue

            result_dict[name] = ui_control.value

        return WorkflowData(result_dict)

    def add_input_text(self,
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

    def add_input_password(self,
                       name: str,
                       title: Optional[str] = None,
                       value: str = '') -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitlePassword,
            name=title,
            value=value)

    def add_combobox(
            self,
            name: str,
            title: Optional[str] = None,
            value: Optional[str]=None,
            values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        self.values[name] = UIBuilder._get_values(values)
        self.labels[name] = UIBuilder._get_labels(values)

        _value = self.values[name].index(UIBuilder._get_value(value)) if value else -1

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitleCombo,
            name=title,
            value=_value,
            values=self.labels[name])

    def add_checkbox_group(
            self,
            name: str,
            title: Optional[str]=None,
            value: Optional[Iterable[str]]=None,
            values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not values:
            raise Exception("You need to pass in some values to display in the group.")

        if not title:
            title = name

        self.values[name] = UIBuilder._get_values(values)
        self.labels[name] = UIBuilder._get_labels(values)

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitleMultiSelect,
            name=title,
            value=[self.values[name].index(UIBuilder._get_value(v)) for v in value],
            max_height=max(len(values) + 1, 2),
            scroll_exit=True,
            values=self.labels[name])

    def add_radio_group(self,
                        name: str,
                        title: Optional[str]=None,
                        value: Optional[str]=None,
                        values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        self.values[name] = UIBuilder._get_values(values)
        self.labels[name] = UIBuilder._get_labels(values)

        _value = self.values[name].index(UIBuilder._get_value(value)) if value else -1

        self.ui_controls[name] = self.form.add_widget(
            npyscreen.TitleSelectOne,
            name=title,
            max_height=max(len(values), 2),
            scroll_exit=True,
            value=_value,
            values=self.labels[name])

    def add_default_button(self,
                           name: str,
                           title: Optional[str]=None) -> None:
        self.context.data[name] = name

    @staticmethod
    def _get_values(values) -> List[str]:
        result = []

        for value in values:
            if isinstance(value, str):
                result.append(value)
                continue

            result.append(value[0])

        return result

    @staticmethod
    def _get_value(value) -> str:
        if isinstance(value, str):
            return value

        return value[0]

    @staticmethod
    def _get_labels(values) -> List[str]:
        result = []

        for value in values:
            if isinstance(value, str):
                result.append(value)
                continue

            result.append(value[1])

        return result


class ConsoleUserTaskProvider(UserTaskProvider):
    def __init__(self):
        super(ConsoleUserTaskProvider, self).__init__()

    def register_event(self,
                       executor: WorkflowExecutor,
                       event: ActiveEvent) -> None:
        def run_on_curses(x):
            try:
                ui = UIBuilder(event)

                adhesive_task = cast(AdhesiveUserTask, executor.tasks_impl[event.task.id])
                context = adhesive_task.invoke_user_task(event.context, ui)

                # call the actual UI
                ui.form.edit()

                # put the values in the data.
                context.data = WorkflowData.merge(context.data, ui.data)

                event.future.set_result(context)
            except Exception as e:
                event.future.set_exception(e)

        npyscreen.wrapper_basic(run_on_curses)
