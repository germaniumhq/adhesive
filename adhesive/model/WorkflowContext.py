from adhesive.graph.Task import Task


class WorkflowContext:
    """
    A context passed to an execution of a task.
    """
    def __init__(self, task: Task) -> None:
        self.task = task

