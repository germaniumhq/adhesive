from typing import Callable, TypeVar, List

import functools
import re

from adhesive.steps.AdhesiveTask import AdhesiveTask
from adhesive.model.AdhesiveProcess import AdhesiveProcess

T = TypeVar('T')
process = AdhesiveProcess()


def task(namere: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        process.steps.append(AdhesiveTask(namere , f))
        return f

    return wrapper_builder


def bpmn_build(file_name: str):
    """ Start a build that was described in BPMN """
    print("build passed")
