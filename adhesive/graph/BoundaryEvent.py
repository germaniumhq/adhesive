from adhesive.graph.Event import Event


class BoundaryEvent(Event):
    def __init__(self,
                 *args,
                 parent_process: 'Process',
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
