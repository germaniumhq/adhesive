from typing import TypeVar

from concurrent.futures import Future

from adhesive.graph.Task import Task

T = TypeVar('T')


class TaskFuture:
    """
    A Future that is bound to a task. It allows retrieving what
    task the future is assigned to. The Future should regardless
    return the ActiveEvent.
    """
    def __init__(self,
                 task: Task,
                 future: Future):
        self.task = task
        self.future = future

    @staticmethod
    def resolved(task: Task, item: T) -> 'TaskFuture':
        future = Future()
        future.set_result(item)

        return TaskFuture(task, future)
