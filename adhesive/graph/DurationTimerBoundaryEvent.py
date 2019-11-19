from adhesive.graph.TimerBoundaryEvent import TimerBoundaryEvent
from adhesive.graph.time.ParsedDurationDefinition import ParsedDurationDefinition


class DurationTimerBoundaryEvent(TimerBoundaryEvent):
    def __init__(self,
                 *,
                 parent_process: str,
                 id: str,
                 name: str,
                 expression: str) -> None:
        super(DurationTimerBoundaryEvent, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name
        )

        self.definition = ParsedDurationDefinition.from_str(expression)
