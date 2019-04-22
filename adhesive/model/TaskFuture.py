from typing import TypeVar

from concurrent.futures import Future

from adhesive.graph.BaseTask import BaseTask

T = TypeVar('T')


class TaskFuture:
    """
    A Future that is bound to a task. It allows retrieving what
    task the future is assigned to. The Future should regardless
    return the ActiveEvent.

    Some tasks / gateways consume multiple elements before firing
    their event.
    """
    def __init__(self,
                 task: BaseTask,
                 future: Future):
        self.task = task
        self.future = future

    @staticmethod
    def resolved(task: BaseTask, item: T) -> 'TaskFuture':
        future = Future()
        future.set_result(item)

        return TaskFuture(task, future)

    def __str__(self) -> str:
        return f"TaskFuture {self.task}"
