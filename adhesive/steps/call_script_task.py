from typing import cast

from adhesive.graph.ScriptTask import ScriptTask
from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.steps.ExecutionToken import ExecutionToken


def call_script_task(event: ActiveEvent) -> ExecutionToken:
    with redirect_stdout(event):
        exec(
            cast(ScriptTask, event.task).script,
            {},                          # globals
            {
                 "context": event.context,
                 "loop": event.context.loop,
                 "data": event.context.data,
            })  # locals

        return event.context
