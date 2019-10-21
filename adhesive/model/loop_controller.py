from typing import Any
import uuid
import logging

from adhesive.execution import token_utils
from adhesive.execution.ExecutionLoop import ExecutionLoop
from adhesive.graph import ProcessTask

from .ActiveEvent import ActiveEvent
from .ActiveLoopType import ActiveLoopType

LOG = logging.getLogger(__name__)


def is_top_loop_event(event: ActiveEvent):
    return event.task.loop and (not event.context.loop or event.context.loop.task != event.task)


def create_loop(event: ActiveEvent,
                clone_event,
                target_task: ProcessTask) -> None:
    """
    Create a loop event.
    """
    new_event = clone_event(event, target_task)

    assert new_event.context

    loop_id = str(uuid.uuid4())

    owning_loop = event.context.loop

    # FIXME: task check should have just worked
    if event.context.loop and \
        event.context.loop.task.id == event.task.id:
        owning_loop = owning_loop.parent_loop

    new_event.loop_type = ActiveLoopType.INITIAL
    new_event.context.loop = ExecutionLoop(
        loop_id=loop_id,
        parent_loop=owning_loop,
        task=new_event.task,
        item=None,
        index=-1,
        expression=target_task.loop.loop_expression
    )


def evaluate_initial_loop(event: ActiveEvent, clone_event) -> None:
    """
    evals the initial expression of the loop and determines its type. If the
    expression returns a collection the loop creates all the events with a
    COLLECTION type. If it returns a truthy, the loop creates a single
    CONDITION event. If it's falsy, the current event changes to INITIAL_EMPTY.
    """
    LOG.debug(f"Loop: Evaluate a new loop: {event.task.loop.loop_expression}")
    loop_data = evaluate_loop_expression(event)

    if not loop_data:
        LOG.debug("Loop is INITIAL_EMPTY")
        event.loop_type = ActiveLoopType.INITIAL_EMPTY
        return

    if not is_collection(loop_data):
        LOG.debug(f"Loop: CONDITION loop for {event.context.loop.loop_id}")
        new_event = clone_event(event, event.task)
        new_event.loop_type = ActiveLoopType.CONDITION

        assert new_event.context

        new_event.context.loop = ExecutionLoop(
            loop_id=event.context.loop.loop_id,
            parent_loop=event.context.loop.parent_loop,
            task=event.task,
            item=loop_data,
            index=0,
            expression=event.context.task.loop.loop_expression)

        new_event.context.task_name = token_utils.parse_name(
                new_event.context,
                new_event.context.task.name)

        return

    LOG.debug(f"Loop: COLLECTION loop for {event.context.loop.loop_id}")

    index = 0
    for item in loop_data:
        new_event = clone_event(event, event.task)
        new_event.loop_type = ActiveLoopType.COLLECTION

        assert new_event.context

        LOG.debug(f"Loop: parent loop {event.context.loop.parent_loop}")

        new_event.context.loop = ExecutionLoop(
            loop_id=event.context.loop.loop_id,
            parent_loop=event.context.loop.parent_loop,
            task=event.task,
            item=item,
            index=index,
            expression=event.context.task.loop.loop_expression)

        # if we're iterating over a map, we're going to store the
        # values as well.
        if isinstance(loop_data, dict):
            new_event.context.loop._value = loop_data[item]

        # FIXME: this knows way too much about how the ExecutionTokens are
        # supposed to function
        # FIXME: rename all event.contexts to event.token. Context is only
        # true in the scope of an execution task.
        LOG.debug(f"Loop value {new_event.context.loop.value}")
        new_event.context.task_name = token_utils.parse_name(
                new_event.context,
                new_event.context.task.name)

        LOG.debug(f"Loop new task name: {new_event.context.task_name}")

        index += 1


def is_conditional_loop_event(event: ActiveEvent) -> bool:
    """
    Checks the event if it's a conditional loop event.
    """
    return event.loop_type == ActiveLoopType.CONDITION


def next_conditional_loop_iteration(event: ActiveEvent, clone_event) -> bool:
    """
    evals the expression of the conditional loop event, to see if should still
    execute.
    """
    if event.loop_type != ActiveLoopType.CONDITION:
        return False

    result = evaluate_loop_expression(event)

    if not result:
        return False

    new_event = clone_event(event, event.task)
    new_event.loop_type = ActiveLoopType.CONDITION

    assert new_event.context

    new_event.context.loop = ExecutionLoop(
        loop_id=event.context.loop.loop_id,
        parent_loop=event.context.loop.parent_loop,
        task=event.task,
        item=result,
        index=event.context.loop.index + 1,
        expression=event.context.loop.expression)

    new_event.context.task_name = token_utils.parse_name(
            new_event.context,
            new_event.context.task.name)

    return True


def is_collection(what: Any) -> bool:
    return hasattr(what, "__iter__")


def evaluate_loop_expression(event: ActiveEvent) -> Any:
    """
    Evaluates a loop expression.
    """
    eval_data = token_utils.get_eval_data(event.context)
    result = eval(event.task.loop.loop_expression, {}, eval_data)

    return result

