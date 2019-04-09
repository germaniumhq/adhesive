from typing import Callable, TypeVar, List
from adhesive.steps.AdhesiveTask import AdhesiveTask
import functools
import re

T = TypeVar('T')
steps: List[AdhesiveTask] = []


def task(name: str) -> Callable[..., Callable[..., T]]:
    def wrapper_builder(f: Callable[..., T]) -> Callable[..., T]:
        steps.append(AdhesiveTask(name , f))
        return f
    return wrapper_builder


def bpmn_build(file_name: str):
    """ Start a build that was described in BPMN """
    print("build passed")
