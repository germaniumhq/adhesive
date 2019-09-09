import asyncio
import functools
from typing import Callable, TypeVar, Optional

from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.consoleui.ConsoleUserTaskProvider import ConsoleUserTaskProvider
from adhesive.model.ProcessExecutor import ProcessExecutor
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.steps.AdhesiveUserTask import AdhesiveUserTask
from adhesive.process_read.bpmn import read_bpmn_file
from adhesive.process_read.tasks import generate_from_tasks
from adhesive.process_read.programmatic import generate_from_calls


T = TypeVar('T')
process = AdhesiveProcess('_root')


#FIXME: move decorators into their own place

def task(*task_names: str,
         loop: Optional[str] = None,
         when: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names, loop=loop, when=when))
        return f

    return wrapper_builder


gateway = task


def usertask(*task_names: str,
             loop: Optional[str] = None,
             when: Optional[str] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveUserTask(f, *task_names, loop=loop, when=when))
        return f

    return wrapper_builder


def lane(*lane_names:str,
         lazy: Optional[bool] = None) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(f)
        def wrapper(*args, **kw) -> T:
            return f(*args, **kw)

        return wrapper

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

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    fn = ProcessExecutor(
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
    process.process = read_bpmn_file(file_name)

    if ut_provider is None:
        ut_provider = ConsoleUserTaskProvider()

    return ProcessExecutor(
        process,
        ut_provider=ut_provider,
        wait_tasks=wait_tasks).execute(initial_data=initial_data)


from adhesive.model.UserTaskProvider import UserTaskProvider
