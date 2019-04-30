from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.WorkflowExecutor import WorkflowExecutor

import abc


class UserTaskProvider:
    @abc.abstractmethod
    def register_event(self,
                       executor: WorkflowExecutor,
                       event: ActiveEvent) -> None:
        pass
