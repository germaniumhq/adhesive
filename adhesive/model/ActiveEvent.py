from typing import Optional, Set

import uuid

from adhesive.steps.WorkflowContext import WorkflowContext
from adhesive.graph.BaseTask import BaseTask
from adhesive.steps.WorkflowData import WorkflowData


class ActiveEvent:
    """
    An event that passes through the system. It can fork
    in case there are multiple executions going down.
    """
    def __init__(self,
                 parent_id: Optional['str'],
                 task: BaseTask) -> None:
        self.id: str = str(uuid.uuid4())
        self.parent_id = parent_id

        self._task = task
        self.context = WorkflowContext(task)

        self.active_children: Set[str] = set()

    def __getstate__(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "_task": self._task,
            "context": self.context
        }

    def clone(self,
              task: BaseTask,
              parent: 'ActiveEvent') -> 'ActiveEvent':
        """
        Clone the current event for another task id target.
        """
        resolved_parent_id = parent.id
        result = ActiveEvent(resolved_parent_id, task)
        result.context = self.context.clone(task)

        parent.active_children.add(result.id)

        return result

    def close_child(self,
                    child: 'ActiveEvent',
                    merge_data: bool) -> None:
        self.active_children.remove(child.id)

        if merge_data:
            self.context.data = WorkflowData.merge(
                self.context.data,
                child.context.data
            )

    @property
    def task(self) -> BaseTask:
        return self._task

    @task.setter
    def task(self, task: BaseTask) -> None:
        self.context.task = task
        self._task = task

    def __repr__(self) -> str:
        return f"ActiveEvent({self.id}): {self.task}"
