import uuid
from typing import Callable, Any, Optional, Union

# from adhesive.model.ActiveEvent import ActiveEvent  # FIXME move from here
# references to the ActiveEvent
from adhesive.execution import token_utils
from adhesive.graph.ProcessTask import ProcessTask


class ExecutionLoop:
    """
    Holds the current looping information.
    """
    def __init__(self,
                 *args,
                 loop_id: str,
                 parent_loop: Optional['ExecutionLoop'],
                 task: ProcessTask,
                 item: Any,
                 index: int,
                 expression: str) -> None:
        if args:
            raise Exception("You need to pass the parameters by name")

        self.loop_id = loop_id
        self._task = task
        self._key = item
        self._value = item
        self._index = index
        self.parent_loop = parent_loop
        self._expression = expression

    @property
    def task(self) -> ProcessTask:
        return self._task

    @property
    def key(self) -> Any:
        return self._key

    @property
    def item(self) -> Any:
        return self._value

    @property
    def value(self) -> Any:
        return self._value

    @property
    def index(self) -> int:
        return self._index

    @property
    def expression(self) -> str:
        return self._expression

    def __repr__(self) -> str:
        """
        String object representation
        """
        return f"Loop[ loop_id: {self.loop_id}, index: {self.index}, key: {self._key}, value: {self._value}"

    @staticmethod
    def create_loop(event: 'ActiveEvent',
                    clone_event: Callable[['ActiveEvent', 'ProcessTask'], 'ActiveEvent'],
                    target_task: 'ProcessTask') -> int:
        expression = target_task.loop.loop_expression

        eval_data = token_utils.get_eval_data(event.context)
        result = eval(expression, {}, eval_data)

        if not result:
            return 0

        index = 0
        for item in result:
            new_event = clone_event(event, target_task)
            loop_id = str(uuid.uuid4())

            parent_loop = new_event.context.loop
            new_event.context.loop = ExecutionLoop(
                loop_id=loop_id,
                parent_loop=parent_loop,
                task=target_task,
                item=item,
                index=index)

            # if we're iterating over a map, we're going to store the
            # values as well.
            if isinstance(result, dict):
                new_event.context.loop._value = result[item]

            # FIXME: this knows way too much about how the ExecutionTokens are
            # supposed to function
            # FIXME: rename all event.contexts to event.token. Context is only
            # true in the scope of an execution task.
            new_event.context.task_name = token_utils.parse_name(
                    new_event.context,
                    new_event.context.task.name)

            index += 1

        return index


def parent_loop_id(e: 'ActiveEvent') -> Optional[str]:
    if not e.context.loop:
        return None

    if not e.context.loop.parent_loop:
        return None

    return f"{e.context.loop.parent_loop.loop_id}:{e.context.loop.parent_loop.index}"


def loop_id(event: 'ActiveEvent') -> Optional[str]:
    """
    Finds the loop id where this event executes. This is the owning loop ID.
    :param event:
    :return:
    """
    loop: ExecutionLoop = event.context.loop

    if not loop:
        return None

    if loop.task == event.context.task:
        loop = loop.parent_loop

    if not loop:
        return None

    return f"{loop.loop_id}:{loop.index}"
