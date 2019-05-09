from typing import Callable, Any, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.model.ActiveEvent import ActiveEvent


class WorkflowLoop:
    """
    Holds the current looping information.
    """
    def __init__(self,
                 parent_loop: Optional['WorkflowLoop'],
                 task: BaseTask,
                 item: Any,
                 index: int) -> None:
        self._task = task
        self._item = item
        self._index = index
        self.parent_loop = parent_loop

    @property
    def task(self) -> BaseTask:
        return self._task

    @property
    def item(self) -> Any:
        return self._item

    @property
    def index(self) -> int:
        return self._index

    @staticmethod
    def create_loop(event: 'ActiveEvent',
                    clone_event: Callable[['ActiveEvent', 'BaseTask'], 'ActiveEvent']) -> None:
        expression = event.task.loop.loop_expression

        result = eval(expression, {}, {
            "context": event.context,
            "data": event.context.data,
            "loop": event.context.loop,
        })

        if not result:
            return

        index = 0
        for item in result:
            new_event = clone_event(event, event.task)

            parent_loop = new_event.context.loop
            new_event.context.loop = WorkflowLoop(
                parent_loop,
                event.task,
                item,
                index)

            new_event.context.update_title()

            index += 1
