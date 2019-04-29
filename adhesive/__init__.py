import asyncio
from typing import Callable, TypeVar

from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.model.WorkflowExecutor import WorkflowExecutor
from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.xml.bpmn import read_bpmn_file

T = TypeVar('T')
process = AdhesiveProcess('_root')


def task(*task_names: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names))
        return f

    return wrapper_builder


# FIXME: they seem different types. Create base, and different implementations?
# Doesn't seem right using the regular AdhesiveTask here.
def usertask(*task_names: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names))
        return f

    return wrapper_builder


def bpmn_build(file_name: str,
               wait_tasks: bool=True):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)
    fn = WorkflowExecutor(process, wait_tasks=wait_tasks).execute()
    asyncio.get_event_loop().run_until_complete(fn)


def bpmn_build_async(
        file_name: str,
        wait_tasks: bool=True):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)
    return WorkflowExecutor(process, wait_tasks=wait_tasks).execute()
