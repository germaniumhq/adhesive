from typing import Callable, List, Optional

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Task import Task
from adhesive.steps.AdhesiveBaseTask import AdhesiveBaseTask
from .WorkflowContext import WorkflowContext


class AdhesiveTask(AdhesiveBaseTask):
    """
    A task implementation.
    """
    def __init__(self,
                 code: Callable,
                 *expressions: str) -> None:
        super(AdhesiveTask, self).__init__(code, *expressions)

    def matches(self,
                task: BaseTask,
                resolved_name: str) -> Optional[List[str]]:
        if not isinstance(task, Task):
            return None

        return super(AdhesiveTask, self).matches(task, resolved_name)

    def invoke(
            self,
            context: WorkflowContext) -> WorkflowContext:
        params = self.matches(context.task, context.task_name)

        self.code(context, *params)  # type: ignore

        return context
