from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.model.ProcessExecutor import ProcessExecutor

import abc


class UserTaskProvider:
    @abc.abstractmethod
    def register_event(self,
                       executor: ProcessExecutor,
                       event: ActiveEvent) -> None:
        pass
