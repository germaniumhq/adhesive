from typing import Callable, TypeVar

from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.model.AdhesiveProcess import AdhesiveProcess
from adhesive.model.WorkflowExecutor import WorkflowExecutor

from adhesive.xml.bpmn import read_bpmn_file

T = TypeVar('T')
process = AdhesiveProcess('_root')


def task(*task_names: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(f, *task_names))
        return f

    return wrapper_builder


def bpmn_build(file_name: str):
    """ Start a build that was described in BPMN """
    process.workflow = read_bpmn_file(file_name)
    return WorkflowExecutor(process).execute()
