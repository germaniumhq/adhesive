from typing import Optional

import schedule

from adhesive.graph.time.CycleTimerBoundaryEvent import CycleTimerBoundaryEvent
from adhesive.model.time.ActiveTimer import ActiveTimer


class CycleBoundaryActiveTimer(ActiveTimer):
    def __init__(self,
                 event_id: str,
                 timer_boundary_event: CycleTimerBoundaryEvent):
        super(CycleBoundaryActiveTimer, self).__init__(
            event_id=event_id,
            timer_boundary_event=timer_boundary_event
        )

        self.execution_count = 0

    def timer_triggered(self) -> Optional[schedule.CancelJob]:
        super(CycleBoundaryActiveTimer, self).timer_triggered()

        self.execution_count += 1
        if self.timer_boundary_event.definition.repeat_count < 0:
            return

        if self.execution_count >= self.timer_boundary_event.definition.repeat_count:
            return schedule.CancelJob
