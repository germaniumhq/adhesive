from typing import Optional

from adhesive.graph.BaseTask import BaseTask


class BoundaryEvent(BaseTask):
    def __init__(self,
                 *args,
                 parent_process: Optional['Process'],
                 id: str,
                 name: str) -> None:
        if args:
            raise Exception("You need to use named arguments")

        super(BoundaryEvent, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name)
        self.attached_task_id = 'not attached'

        self.cancel_activity = True
        self.parallel_multiple = False


class ErrorBoundaryEvent(BoundaryEvent):
    pass
