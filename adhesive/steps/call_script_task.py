from typing import cast

from adhesive.graph.ScriptTask import ScriptTask
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.steps.ExecutionToken import ExecutionToken


def call_script_task(event: ActiveEvent) -> ExecutionToken:
    exec(
        cast(ScriptTask, event.task).script,
        {},                          # globals
        {
             "context": event.context,
             "loop": event.context.loop,
             "data": event.context.data,
        })  # locals

    return event.context
