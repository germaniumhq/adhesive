from adhesive.steps.WorkflowContext import WorkflowContext
from adhesive.graph.Task import Task


class ActiveEvent:
    """
    An event that passes through the system. It can fork
    in case there are multiple executions going down.
    """
    def __init__(self, task: Task) -> None:
        self._task = task
        self.context = WorkflowContext(task)

    def clone(self, task: Task) -> 'ActiveEvent':
        """
        Clone the current event for another task id target.
        """
        result = ActiveEvent(task)
        result.context = self.context.clone(task)

        return result

    @property
    def task(self) -> Task:
        return self._task

    @task.setter
    def task(self, task: Task) -> None:
        self.context.task = task
        self._task = task
