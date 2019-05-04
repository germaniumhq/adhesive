from typing import Optional, List, Iterable, Union, Tuple, Any

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.UiBuilderApi import UiBuilderApi
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.model.UserTaskProvider import UserTaskProvider
from adhesive.steps.WorkflowContext import WorkflowContext


class UIBuilder(UiBuilderApi):
    def __init__(self,
                 context: WorkflowContext):
        self.context = context

    def add_input_text(self,
                       name: str,
                       title: Optional[str] = None,
                       value: str = '') -> None:
        self.context.data[name] = name

    def add_input_password(self,
                           name: str,
                           title: Optional[str] = None,
                           value: str = '') -> None:
        self.context.data[name] = name

    def add_combobox(self,
                     name: str,
                     title: Optional[str] = None,
                     value: Optional[str]=None,
                     values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        self.context.data[name] = values[0]

    def add_checkbox_group(
            self,
            name: str,
            title: Optional[str]=None,
            value: Optional[Iterable[str]]=None,
            values: Optional[Iterable[Union[Tuple[str, str], str]]]=None) -> None:
        self.context.data[name] = value

    def add_radio_group(self,
                        name: str,
                        title: Optional[str]=None,
                        value: Optional[str]=None,
                        values: Optional[List[Any]]=None) -> None:
        pass

    def add_default_button(self,
                           name: str,
                           title: Optional[str]=None) -> None:
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

