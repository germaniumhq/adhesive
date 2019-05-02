from typing import cast

from adhesive.graph.ScriptTask import ScriptTask
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.steps.WorkflowContext import WorkflowContext


def call_script_task(event: ActiveEvent) -> WorkflowContext:
    exec(cast(ScriptTask, event.task).script,
         {},                          # globals
         {"context": event.context})  # locals

    return event.context
