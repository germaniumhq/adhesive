from typing import Optional

import schedule

from adhesive.graph.time.TimerBoundaryEvent import TimerBoundaryEvent


class ActiveTimer:
    def __init__(self,
                 event_id: str,
                 timer_boundary_event: TimerBoundaryEvent) -> None:
        # FIXME: the active timer event should fire the event with the data
        # cloned from the initial_event_id.
        self.timer_boundary_event = timer_boundary_event
        self.job = schedule\
            .every(timer_boundary_event.total_seconds())\
            .seconds\
            .tag(event_id)\
            .do(self.timer_triggered)

    def timer_triggered(self)  -> Optional[schedule.CancelJob]:
        raise NotImplementedError("Needs to fire the event")