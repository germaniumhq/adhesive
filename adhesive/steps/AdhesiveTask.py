from typing import Callable, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Task import Task
from adhesive.logredirect.LogRedirect import redirect_stdout
from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.steps.AdhesiveBaseTask import AdhesiveBaseTask
from .ExecutionToken import ExecutionToken


class AdhesiveTask(AdhesiveBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str,
                 loop: Optional[str] = None,
                 when: Optional[str] = None) -> None:
        """
        Create a new adhesive task. The `loop` and `when` are only
        available when doing a programmatic API.
        :param code:
        :param expressions:
        :param loop:
        :param when:
        """
        super(AdhesiveTask, self).__init__(code, *expressions)

        self.loop = loop
        self.when = when

    def matches(self,
                task: BaseTask,
                resolved_name: str) -> Optional[List[str]]:
        if not isinstance(task, Task):
            return None

        return super(AdhesiveTask, self).matches(task, resolved_name)

    def invoke(
            self,
            event: ActiveEvent) -> ExecutionToken:
        with redirect_stdout(event):
            context = event.context

            params = self.matches(context.task, context.task_name)

            self.code(context, *params)  # type: ignore

            return context
