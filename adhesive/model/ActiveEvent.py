from typing import Optional, Set

import uuid

from adhesive.steps.WorkflowContext import WorkflowContext
from adhesive.graph.Task import Task
from adhesive.steps.WorkflowData import WorkflowData


class ActiveEvent:
    """
    An event that passes through the system. It can fork
    in case there are multiple executions going down.
    """
    def __init__(self,
                 parent_id: Optional['str'],
                 task: Task) -> None:
        self.id: str = str(uuid.uuid4())
        self.parent_id = parent_id

        self._task = task
        self.context = WorkflowContext(task)

        self.active_children: Set[str] = set()
        self.future = None

    def __getstate__(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "_task": self._task,
            "context": self.context
        }

    def clone(self,
              task: Task,
              parent: 'ActiveEvent') -> 'ActiveEvent':
        """
        Clone the current event for another task id target.
        """
        resolved_parent_id = parent.id if parent else self.parent_id
        result = ActiveEvent(resolved_parent_id, task)
        result.context = self.context.clone(task)

        parent.active_children.add(result.id)

        return result

    def close_child(self,
                    child: 'ActiveEvent') -> None:
        self.active_children.remove(child.id)
        self.context.data = WorkflowData.merge(
            self.context.data,
            child.context.data
        )

        if not self.active_children and self.future:
            self.future.set_result(self)

    @property
    def task(self) -> Task:
        return self._task

    @task.setter
    def task(self, task: Task) -> None:
        self.context.task = task
        self._task = task
