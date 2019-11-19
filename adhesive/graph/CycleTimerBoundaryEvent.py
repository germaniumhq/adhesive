from adhesive.graph.TimerBoundaryEvent import TimerBoundaryEvent
from adhesive.graph.time.ParsedCycleDefinition import ParsedCycleDefinition


class CycleTimerBoundaryEvent(TimerBoundaryEvent):
    def __init__(self,
                 *,
                 parent_process: str,
                 id: str,
                 name: str,
                 expression: str) -> None:
        super(CycleTimerBoundaryEvent, self).__init__(
            parent_process=parent_process,
            id=id,
            name=name
        )

        self.definition = ParsedCycleDefinition.from_str(expression)
