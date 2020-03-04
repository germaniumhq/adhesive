import logging
from collections import OrderedDict
from typing import Dict, Optional, Union, Iterable, Tuple, Any

from adhesive.consoleui.color_print import green, red
from adhesive.model.ActiveEvent import ActiveEvent
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


class ProcessEvents:
    def __init__(self):
        self.events: Dict[str, ActiveEvent] = dict()
        self.bystate: Dict[ActiveEventState, Dict[str, ActiveEvent]] = dict()
        self.handlers: Dict[ActiveEventState, Dict[str, Tuple[ActiveEvent, Any]]] = dict()

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

    def __contains__(self, item):
        return item in self.events

    def __getitem__(self, item: str) -> ActiveEvent:
        return self.events[item]

    def __setitem__(self, key: str, value: ActiveEvent) -> None:
        self.events[key] = value
        self.bystate[value.state][key] = value
        self.handlers[value.state][key] = (value, None)

    def __delitem__(self, key: str) -> None:
        event = self.events[key]
        del self.events[key]
        del self.bystate[event.state][event.token_id]
        if event.token_id in self.bystate[event.state]:
            del self.bystate[event.state][event.token_id]

    def __len__(self) -> int:
        return len(self.events)
