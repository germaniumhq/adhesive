import uuid
from typing import Callable, Any, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.model.ActiveEvent import ActiveEvent


class WorkflowLoop:
    """
    Holds the current looping information.
    """
    def __init__(self,
                 loop_id: str,
                 parent_loop: Optional['WorkflowLoop'],
                 task: BaseTask,
                 item: Any,
                 index: int) -> None:
        self.loop_id = loop_id
        self._task = task
        self._key = item
        self._value = item
        self._index = index
        self.parent_loop = parent_loop

    @property
    def task(self) -> BaseTask:
        return self._task

    @property
    def key(self) -> Any:
        return self._key

    @property
    def value(self) -> Any:
        return self._value

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
            loop_id = str(uuid.uuid4())

            parent_loop = new_event.context.loop
            new_event.context.loop = WorkflowLoop(
                loop_id,
                parent_loop,
                event.task,
                item,
                index)

            # if we're iterating over a map, we're going to store the
            # values as well.
            if isinstance(result, dict):
                new_event.context.loop._value = result[item]

            new_event.context.update_title()

            index += 1
