import asyncio
from typing import Callable, TypeVar, Optional

from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.consoleui.ConsoleUserTaskProvider import ConsoleUserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.steps.AdhesiveUserTask import AdhesiveUserTask
from adhesive.process_read.bpmn import read_bpmn_file
from adhesive.process_read.tasks import generate_from_tasks
from adhesive.process_read.programmatic import generate_from_calls

T = TypeVar('T')
process = AdhesiveProcess('_root')


def task(*task_names: str,
         loop: Optional[str] = None,
         when: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names, loop=loop, when=when))
        return f

    return wrapper_builder


def usertask(*task_names: str,
             loop: Optional[str] = None,
             when: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveUserTask(f, *task_names, loop=loop, when=when))
        return f

    return wrapper_builder


def build(ut_provider: Optional['UserTaskProvider'] = None,
          wait_tasks: bool = True,
          initial_data = None):
    process.workflow = generate_from_tasks(process)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks,
                  initial_data=initial_data)


def process_start():
    builder = generate_from_calls(_build)
    process.workflow = builder.workflow

    return builder


def bpmn_build(file_name: str,
               ut_provider: Optional['UserTaskProvider'] = None,
               wait_tasks: bool = True,
               initial_data = None):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks,
                  initial_data=initial_data)


def _build(ut_provider: Optional['UserTaskProvider'] = None,
           wait_tasks: bool = True,
           initial_data=None):

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    fn = WorkflowExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute(initial_data=initial_data)

    return asyncio.get_event_loop().run_until_complete(fn)


def bpmn_build_async(
        file_name: str,
        ut_provider: Optional['UserTaskProvider'] = None,
        wait_tasks: bool = True,
        initial_data = None):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    return WorkflowExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute(initial_data=initial_data)


from adhesive.model.UserTaskProvider import UserTaskProvider
