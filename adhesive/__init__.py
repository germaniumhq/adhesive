from contextlib import contextmanager, _GeneratorContextManager
from typing import Callable, TypeVar, Optional, Union, List, Tuple, Any, Generator, Sequence, Generic

from adhesive.graph.ProcessTask import ProcessTask

from adhesive import config
from adhesive.consoleui.ConsoleUserTaskProvider import ConsoleUserTaskProvider
from adhesive.execution.ExecutionLane import ExecutionLane
from adhesive.execution.ExecutionMessageCallbackEvent import ExecutionMessageCallbackEvent
from adhesive.execution.ExecutionMessageEvent import ExecutionMessageEvent
from adhesive.execution.ExecutionTask import ExecutionTask
from adhesive.execution.ExecutionToken import ExecutionToken
from adhesive.execution.ExecutionUserTask import ExecutionUserTask
from adhesive.logging import configure_logging
from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.process_read.bpmn import read_bpmn_file
from adhesive.process_read.programmatic import generate_from_calls
from adhesive.process_read.tasks import generate_from_tasks
from adhesive.workspace.Workspace import Workspace
from adhesive.model.UiBuilderApi import UiBuilderApi

T = TypeVar('T')
process = AdhesiveProcess('_root')


class Token(ExecutionToken, Generic[T]):
    workspace: Workspace
    task: ProcessTask
    data: T  # type: ignore


_DecoratedFunction = Union[  # FIXME: this is terrible
    Callable[[Token], T],
    Callable[[Token, str], T],
    Callable[[Token, str, str], T],
    Callable[[Token, str, str, str], T],
    Callable[[Token, str, str, str, str], T],
]

WorkspaceGenerator = Generator[Workspace, Workspace, None]
LaneFunction = _DecoratedFunction[WorkspaceGenerator]
UI = UiBuilderApi

#FIXME: move decorators into their own place

def task(*task_names: str,
         re: Optional[Union[str, List[str]]] = None,
         loop: Optional[str] = None,
         when: Optional[str] = None,
         lane: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.task_definitions.append(
            ExecutionTask(code=f,
                          expressions=task_names,
                          regex_expressions=re,
                          loop=loop,
                          when=when,
                          lane=lane))
        return f

    return wrapper_builder


gateway = task


def usertask(*task_names: str,
             re: Optional[Union[str, List[str]]] = None,
             loop: Optional[str] = None,
             when: Optional[str] = None,
             lane: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        usertask = ExecutionUserTask(
            code=f,
            expressions=task_names,
            regex_expressions=re,
            loop=loop,
            when=when,
            lane=lane)
        process.user_task_definitions.append(usertask)
        return f

    return wrapper_builder

def lane(*lane_names:str,
         re: Optional[Union[str, List[str]]] = None,
         ) -> Callable[[LaneFunction], WorkspaceGenerator]:
    """
    Allow defining a lane where a custom workspace will be created. This
    function needs to yield a workspace that will be used. It's a
    contextmanager. When all the execution tokens exit the lane, the code after
    the yield will be executed.
    """
    def wrapper_builder(f: LaneFunction) -> WorkspaceGenerator:
        newf = contextmanager(f)  # type: ignore
        process.lane_definitions.append(ExecutionLane(
            code=newf,
            expressions=lane_names,
            regex_expressions=re))
        return newf  # type: ignore

    return wrapper_builder


def message(*message_names: str,
             re: Optional[Union[str, List[str]]] = None):
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        message_definition = ExecutionMessageEvent(
            code=f,
            expressions=message_names,
            regex_expressions=re)

        process.message_definitions.append(message_definition)

        return f

    return wrapper_builder


def message_callback(*message_names: str,
                     re: Optional[Union[str, List[str]]] = None):
    """
    Obtain a message callback, that can push the
    :param message_names:
    :param re:
    :return:
    """
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        message_definition = ExecutionMessageCallbackEvent(
            code=f,
            expressions=message_names,
            regex_expressions=re)

        process.message_callback_definitions.append(message_definition)

        return f

    return wrapper_builder


# FIXME: move builders into their own place

def build(ut_provider: Optional['UserTaskProvider'] = None,
          wait_tasks: bool = True,
          initial_data = None):
    process.process = generate_from_tasks(process)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks,
                  initial_data=initial_data)


def process_start():
    builder = generate_from_calls(_build)
    process.process = builder.process

    return builder


def bpmn_build(file_name: str,
               ut_provider: Optional['UserTaskProvider'] = None,
               wait_tasks: bool = True,
               initial_data = None):
    """ Start a build that was described in BPMN """
    process.process = read_bpmn_file(file_name)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks,
                  initial_data=initial_data)


def _build(ut_provider: Optional['UserTaskProvider'] = None,
           wait_tasks: bool = True,
           initial_data=None):

    configure_logging(config.current)

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    return ProcessExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute(initial_data=initial_data)


from adhesive.model.UserTaskProvider import UserTaskProvider
