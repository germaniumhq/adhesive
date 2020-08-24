import logging
from collections import OrderedDict
from typing import Dict, Optional, Union, Iterable, Tuple, Any, cast

from adhesive.graph.ProcessTask import ProcessTask
from adhesive.consoleui.color_print import green, red
from adhesive.execution.ExecutionLoop import loop_id
from adhesive.model.ActiveEvent import ActiveEvent, PRE_RUN_STATES
from adhesive.model.ActiveEventStateMachine import ActiveEventState
from adhesive.model.ActiveLoopType import ActiveLoopType

LOG = logging.getLogger(__name__)


def log_running_done(event: ActiveEvent,
                     task_error = None):
    if event.loop_type in (ActiveLoopType.INITIAL, ActiveLoopType.INITIAL_EMPTY):
        return

    if not task_error:
        LOG.info(green("Done ") + green(event.context.task_name, bold=True))
        return

    if task_error.failed_event != event:
        LOG.info(red("Terminated ") +
                 red(event.context.task_name, bold=True) +
                 red(" reason: ") +
                 red(str(task_error.failed_event), bold=True))
        return

    LOG.info(red("Failed ") + red(event.context.task_name, bold=True))


def is_deduplication_event(event: ActiveEvent) -> bool:
    return event.deduplication_id is not None


class ProcessEvents:
    """
    A class that transitions and keeps track of all the events
    that run in a process.
    """
    def __init__(self):
        self.events: Dict[str, ActiveEvent] = dict()
        self.bystate: Dict[ActiveEventState, Dict[str, ActiveEvent]] = dict()
        self.handlers: Dict[ActiveEventState, Dict[str, Tuple[ActiveEvent, Any]]] = dict()

        # Keeps the count of active deduplicated events, for a given deduplication ID.
        self._deduplicated_active_count: Dict[str, int] = dict()
        self._deduplicated_waiting: Dict[str, ActiveEvent] = dict()

        for state in ActiveEventState:
            self.bystate[state] = OrderedDict()

        for state in ActiveEventState:
            self.handlers[state] = OrderedDict()

        self.changed = False

    def transition(self,
                   *,
                   event: Union[ActiveEvent, str],
                   state: ActiveEventState,
                   data: Any = None) -> None:
        LOG.debug(f"Event transition {event} -> {state}")
        self.changed = True

        if not isinstance(event, ActiveEvent):
            event = self.events[event]

        if event.state == ActiveEventState.RUNNING:
            log_running_done(event, data.task_error if data and hasattr(data, 'task_error') else None)

        del self.bystate[event.state][event.token_id]
        if event.token_id in self.handlers[event.state]:
            del self.handlers[event.state][event.token_id]

        event.state = state
        self.bystate[event.state][event.token_id] = event
        self.handlers[event.state][event.token_id] = (event, data)

    def get(self,
            state: ActiveEventState) -> Optional[ActiveEvent]:
        for _id, event in self.bystate[state].items():
            return event

        return None

    def pop(self,
            state: ActiveEventState) -> Tuple[Optional[ActiveEvent], Any]:
        result = None

        for _id, event in self.handlers[state].items():
            result = event
            break

        if not result:
            return None, None

        del self.handlers[state][result[0].token_id]

        return result[0], result[1]

    def iterate(self,
                states: Union[ActiveEventState, Iterable[ActiveEventState]]):
        if isinstance(states, ActiveEventState):
            for _id, event in self.bystate[states].items():
                yield event

            return

        for state in states:
            for _id, event in self.bystate[state].items():
                yield event

        return

    def excluding(self,
                  states: Union[ActiveEventState, Iterable[ActiveEventState]]):
        if isinstance(states, ActiveEventState):
            states = { states }

        for state in ActiveEventState:
            if state in states:
                continue

            for _id, event in self.bystate[state].items():
                yield event

        return

    def get_other_task_waiting(
                self,
                event: ActiveEvent) -> \
            Tuple[Optional[ActiveEvent], int]:
        """
        Get any other event that might be waiting to be executed on the
        same task.
        :param event:
        :return:
        """
        result = None
        count = 0

        # if we have a task that requires deduplication, we need to look
        # if there's a waiting deduplication id.
        if is_deduplication_event(event) and \
                event.deduplication_id in self._deduplicated_waiting:
            return self._deduplicated_waiting[event.deduplication_id], 1

        if event.context.loop and \
                event.context.loop.task.id == event.task.id and \
                event.context.loop.index >= 0:
            return result, count

        for ev in self.iterate(PRE_RUN_STATES):
            if ev == event:
                continue

            if ev.task == event.task and loop_id(ev) == loop_id(event):
                if not result:
                    result = ev

                count += 1

        return result, count

    def __contains__(self, item):
        return item in self.events

    def __getitem__(self, item: str) -> ActiveEvent:
        return self.events[item]

    def __setitem__(self, key: str, event: ActiveEvent) -> None:
        self.events[key] = event
        self.bystate[event.state][key] = event
        self.handlers[event.state][key] = (event, None)

    def register_deduplication_event(self, event: ActiveEvent) -> None:
        if event.deduplication_id is None:
            raise Exception("deduplication_id is none. This is an Adhesive BUG, "
                            "please report it.")

        if event.deduplication_registered:
            LOG.warning(f"The event is already registered: {event}. "
                        f"Not counting it twice.")
            return

        event.deduplication_registered = True
        self._deduplicated_active_count[event.deduplication_id] = \
            self._deduplicated_active_count.get(event.deduplication_id, 0) + 1

    def unregister_deduplication_event(self, event: ActiveEvent):
        # if the event wasn't registered, there's nothing to unregister
        if not event.deduplication_registered:
            return

        if event.deduplication_id is None:
            raise Exception("deduplication_id is none. This is an Adhesive BUG, "
                            "please report it.")

        self._deduplicated_active_count[event.deduplication_id] = \
            self._deduplicated_active_count.get(event.deduplication_id, 0) - 1

        if self._deduplicated_active_count[event.deduplication_id] == 0:
            del self._deduplicated_active_count[event.deduplication_id]

    def clear_waiting_deduplication(self, *, event: ActiveEvent):
        if event.deduplication_id in self._deduplicated_waiting:
            del self._deduplicated_waiting[event.deduplication_id]

    def set_waiting_deduplication(self, *, event: ActiveEvent) -> None:
        """
        Tests the waiting deduplication event for a given
        deduplication id. If there's another deduplication event
        for the same ID it gets discarded.
        :param event:
        :return:
        """
        if event.deduplication_id is None:
            raise Exception("Adhesive BUG. No deduplication_id for event: {event}")

        existing_event = self._deduplicated_waiting.pop(event.deduplication_id, None)

        if existing_event:
            self.transition(event=existing_event, state=ActiveEventState.DONE)

        self._deduplicated_waiting[event.deduplication_id] = event

    def get_waiting_deduplication(self, *, event: ActiveEvent) -> Optional[ActiveEvent]:
        if event.deduplication_id is None:
            raise Exception("Adhesive BUG. No deduplication_id for event: {event}")

        return self._deduplicated_waiting.get(event.deduplication_id, None)

    def are_deduplication_events_running(self, *, event: ActiveEvent) -> bool:
        assert event.deduplication_id
        return self._deduplicated_active_count.get(event.deduplication_id, 0) > 0

    def __delitem__(self, key: str) -> None:
        event = self.events[key]
        del self.events[key]
        del self.bystate[event.state][event.token_id]
        if event.token_id in self.bystate[event.state]:
            del self.bystate[event.state][event.token_id]

    def __len__(self) -> int:
        return len(self.events)
