from adhesive.graph.BaseTask import BaseTask


class BoundaryEvent(BaseTask):
    def __init__(self,
                 _id: str,
                 name: str) -> None:
        super(BoundaryEvent, self).__init__(_id, name)
        self.attached_task_id = 'not attached'

        self.cancel_activity = True
        self.parallel_multiple = False


class ErrorBoundaryEvent(BoundaryEvent):
    pass
