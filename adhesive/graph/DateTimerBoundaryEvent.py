from adhesive.graph.TimerBoundaryEvent import TimerBoundaryEvent
from adhesive.graph.time.ParsedDateDefinition import ParsedDateDefinition


class DateTimerBoundaryEvent(TimerBoundaryEvent):
    def __init__(self,
                 *,
                 parent_process: str,
                 id: str,
                 name: str,
                 expression: str) -> None:
        super(DateTimerBoundaryEvent, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name
        )

        self.definition = ParsedDateDefinition.from_str(expression)
