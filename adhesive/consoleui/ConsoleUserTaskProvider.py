from typing import Optional, List, Dict, Any, cast, Tuple, Union, Iterable

import npyscreen as npyscreen

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.UiBuilderApi import UiBuilderApi
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.AdhesiveUserTask import AdhesiveUserTask
from adhesive.steps.ExecutionData import ExecutionData


class UIBuilder(UiBuilderApi):
    def __init__(self,
                 event: ActiveEvent):
        self.context = event.context
        self.ui_controls: Dict[str, Any] = dict()

        self.labels: Dict[str, List[str]] = dict()
        self.values: Dict[str, List[str]] = dict()

        self.ncurses_calls = []

    @property
    def data(self) -> ExecutionData:
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

        return ExecutionData(result_dict)

    def add_input_text(self,
                       name: str,
                       title: Optional[str] = None,
                       value: str = '') -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        def ncurses_input_text_call():
            self.ui_controls[name] = self.form.add_widget(
                npyscreen.TitleText,
                name=title,
                value=value)

        self.ncurses_calls.append(ncurses_input_text_call)

    def add_input_password(self,
                       name: str,
                       title: Optional[str] = None,
                       value: str = '') -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        def ncurses_input_password_call():
            self.ui_controls[name] = self.form.add_widget(
                npyscreen.TitlePassword,
                name=title,
                value=value)

        self.ncurses_calls.append(ncurses_input_password_call)

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

        def ncurses_add_combobox_call():
            self.ui_controls[name] = self.form.add_widget(
                npyscreen.TitleCombo,
                name=title,
                value=_value,
                values=self.labels[name])

        self.ncurses_calls.append(ncurses_add_combobox_call)

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

        if value is None:
            value = []

        title_overflows = 0 if len(title) < 14 else 1

        self.values[name] = UIBuilder._get_values(values)
        self.labels[name] = UIBuilder._get_labels(values)

        def ncurses_add_checbox_group_call():
            self.ui_controls[name] = self.form.add_widget(
                npyscreen.TitleMultiSelect,
                name=title,
                value=[self.values[name].index(UIBuilder._get_value(v)) for v in value],
                max_height=max(len(values) + 1, 2) + title_overflows,
                scroll_exit=True,
                values=self.labels[name])

        self.ncurses_calls.append(ncurses_add_checbox_group_call)

    def add_radio_group(self,
                        name: str,
                        title: Optional[str]=None,
                        value: Optional[str]=None,
                        values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        if not name:
            raise Exception("You need to pass a name for the input.")

        if not title:
            title = name

        title_overflows = 0 if len(title) < 14 else 1

        self.values[name] = UIBuilder._get_values(values)
        self.labels[name] = UIBuilder._get_labels(values)

        _value = self.values[name].index(UIBuilder._get_value(value)) if value is not None else -1

        def ncurses_add_radio_group_call():
            self.ui_controls[name] = self.form.add_widget(
                npyscreen.TitleSelectOne,
                name=title,
                max_height=max(len(values), 2) + title_overflows,
                scroll_exit=True,
                value=_value,
                values=self.labels[name])

        self.ncurses_calls.append(ncurses_add_radio_group_call)

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

        ui = UIBuilder(event)

        adhesive_task = cast(AdhesiveUserTask, executor.tasks_impl[event.task.id])
        context = adhesive_task.invoke_user_task(event, ui)

        # redirecting logs, and initializing ncurses is prolly a bad idea
        # the code that generates the UI shouldn't be run in ncurses
        def run_on_curses(x):
            try:
                # build the UI components on ncurses:
                ui.form = npyscreen.Form(name=event.task.name)

                for ncurses_call in ui.ncurses_calls:
                    ncurses_call()

                # call the actual UI
                ui.form.edit()

                # put the values in the data.
                context.data = ExecutionData.merge(context.data, ui.data)

                event.future.set_result(context)
            except Exception as e:
                event.future.set_exception(e)

        npyscreen.wrapper_basic(run_on_curses)
