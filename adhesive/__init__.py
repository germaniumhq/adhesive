import asyncio
from typing import Callable, TypeVar, Optional

from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.consoleui.ConsoleUserTaskProvider import ConsoleUserTaskProvider
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.steps.AdhesiveUserTask import AdhesiveUserTask
from adhesive.xml.bpmn import read_bpmn_file
from adhesive.xml.tasks import generate_from_tasks

T = TypeVar('T')
process = AdhesiveProcess('_root')


def task(*task_names: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names))
        return f

    return wrapper_builder


def usertask(*task_names: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveUserTask(f, *task_names))
        return f

    return wrapper_builder


def build(ut_provider: Optional['UserTaskProvider'] = None,
          wait_tasks: bool=True):
    process.workflow = generate_from_tasks(process)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks)


def bpmn_build(file_name: str,
               ut_provider: Optional['UserTaskProvider'] = None,
               wait_tasks: bool=True):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)

    return _build(ut_provider=ut_provider,
                  wait_tasks=wait_tasks)


def _build(ut_provider: Optional['UserTaskProvider'] = None,
           wait_tasks: bool=True):

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    fn = WorkflowExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute()

    return asyncio.get_event_loop().run_until_complete(fn)


def bpmn_build_async(
        file_name: str,
        ut_provider: Optional['UserTaskProvider'] = None,
        wait_tasks: bool=True):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    return WorkflowExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute()


from adhesive.model.UserTaskProvider import UserTaskProvider
