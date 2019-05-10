from enum import Enum
from typing import Any, Dict, Optional, Callable, Union
import uuid
import logging

LOG = logging.getLogger(__name__)


class ActiveEventState(Enum):
    NEW = 'NEW'
    PROCESSING = 'PROCESSING'
    WAITING = 'WAITING'
    ERROR = 'ERROR'
    RUNNING = 'RUNNING'
    ROUTING = 'ROUTING'
    DONE_CHECK = 'DONE_CHECK'
    DONE_END_TASK = 'DONE_END_TASK'
    DONE = 'DONE'


STATE_INDEX = {
    'NEW': 0,
    'PROCESSING': 1,
    'WAITING': 2,
    'ERROR': 3,
    'RUNNING': 4,
    'ROUTING': 5,
    'DONE_CHECK': 6,
    'DONE_END_TASK': 7,
    'DONE': 8,
}


class ActiveEventStateChangeEvent(object):
    """
    Event that gets on all the before/after callbacks that are
    triggered on state changes.
    """

    def __init__(self,
                 previous_state: Optional[ActiveEventState],
                 target_state: ActiveEventState,
                 data: Any) -> None:
        """
        Create a new event.

        :param ActiveEventState previous_state: The state that the state machine is transitioning from.
        :param ActiveEventState target_state: The state that the state machine is transitioning to.
        :param object data: Optional data that is passed in the event.
        """
        self._previous_state = previous_state
        self._target_state = target_state
        self.data = data
        self._cancelled = False

    def cancel(self) -> None:
        """
        Cancel the current transition.
        """
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        """
        Is the current transition cancelled.
        :return:
        """
        return self._cancelled

    @property
    def previous_state(self) -> Optional[ActiveEventState]:
        """
        The state from which we're transitioning.
        :return:
        """
        return self._previous_state

    @property
    def target_state(self) -> ActiveEventState:
        """
        Thestate towards we're transitioning.
        :return:
        """
        return self._target_state


class ActiveEventStateException(Exception):
    pass


transition_set: Dict[int, bool] = dict()
link_map: Dict[ActiveEventState, Dict[str, ActiveEventState]] = dict()


def register_transition(name: Optional[str], from_state: ActiveEventState, to_state: ActiveEventState) -> None:
    transition_set[STATE_INDEX[from_state.value] << 14 | STATE_INDEX[to_state.value]] = True

    if not name:
        return

    fromMap = link_map.get(from_state.value)

    if not fromMap:
        fromMap = link_map[from_state.value] = dict()

    fromMap[name] = to_state


register_transition('process', ActiveEventState.NEW, ActiveEventState.PROCESSING)
register_transition('run', ActiveEventState.NEW, ActiveEventState.RUNNING)
register_transition('error', ActiveEventState.NEW, ActiveEventState.DONE)
register_transition('route', ActiveEventState.PROCESSING, ActiveEventState.ROUTING)
register_transition('wait_check', ActiveEventState.PROCESSING, ActiveEventState.WAITING)
register_transition('run', ActiveEventState.PROCESSING, ActiveEventState.RUNNING)
register_transition('done', ActiveEventState.PROCESSING, ActiveEventState.DONE)
register_transition('run', ActiveEventState.WAITING, ActiveEventState.RUNNING)
register_transition('done', ActiveEventState.WAITING, ActiveEventState.DONE)
register_transition('error', ActiveEventState.WAITING, ActiveEventState.ERROR)
register_transition('route', ActiveEventState.RUNNING, ActiveEventState.ROUTING)
register_transition('error', ActiveEventState.RUNNING, ActiveEventState.ERROR)
register_transition('done_check', ActiveEventState.RUNNING, ActiveEventState.DONE_CHECK)
register_transition('route', ActiveEventState.ERROR, ActiveEventState.ROUTING)
register_transition('done', ActiveEventState.ERROR, ActiveEventState.DONE)
register_transition('done_check', ActiveEventState.ERROR, ActiveEventState.DONE_CHECK)
register_transition('done_check', ActiveEventState.ROUTING, ActiveEventState.DONE_CHECK)
register_transition('done', ActiveEventState.DONE_CHECK, ActiveEventState.DONE)
register_transition('done_end_task', ActiveEventState.DONE_CHECK, ActiveEventState.DONE_END_TASK)
register_transition('done', ActiveEventState.DONE_END_TASK, ActiveEventState.DONE)


ChangeStateEventListener = Union[
    Callable[[], Optional[ActiveEventState]],
    Callable[[ActiveEventStateChangeEvent], Optional[ActiveEventState]]
]


class ActiveEventStateMachine(object):
    def __init__(self, initial_state: Optional[ActiveEventState]=None) -> None:
        self._transition_listeners: Dict[str, EventListener] = dict()
        self._data_listeners: Dict[str, EventListener] = dict()
        self._initial_state = initial_state or ActiveEventState.NEW

        self._transition_listeners['NEW'] = EventListener()
        self._transition_listeners['PROCESSING'] = EventListener()
        self._transition_listeners['WAITING'] = EventListener()
        self._transition_listeners['ERROR'] = EventListener()
        self._transition_listeners['RUNNING'] = EventListener()
        self._transition_listeners['ROUTING'] = EventListener()
        self._transition_listeners['DONE_CHECK'] = EventListener()
        self._transition_listeners['DONE_END_TASK'] = EventListener()
        self._transition_listeners['DONE'] = EventListener()
        self._data_listeners['NEW'] = EventListener()
        self._data_listeners['PROCESSING'] = EventListener()
        self._data_listeners['WAITING'] = EventListener()
        self._data_listeners['ERROR'] = EventListener()
        self._data_listeners['RUNNING'] = EventListener()
        self._data_listeners['ROUTING'] = EventListener()
        self._data_listeners['DONE_CHECK'] = EventListener()
        self._data_listeners['DONE_END_TASK'] = EventListener()
        self._data_listeners['DONE'] = EventListener()
        self._currentState = None  # type: Optional[ActiveEventState]
        self._current_change_state_event = None  # type: Optional[ActiveEventStateChangeEvent]

    @property
    def state(self) -> ActiveEventState:
        self._ensure_state_machine_initialized()
        assert self._currentState

        return self._currentState

    def process(self, data: Any=None) -> ActiveEventState:
        return self.transition("process", data)

    def error(self, data: Any=None) -> ActiveEventState:
        return self.transition("error", data)

    def route(self, data: Any=None) -> ActiveEventState:
        return self.transition("route", data)

    def wait_check(self, data: Any=None) -> ActiveEventState:
        return self.transition("wait_check", data)

    def run(self, data: Any=None) -> ActiveEventState:
        return self.transition("run", data)

    def done(self, data: Any=None) -> ActiveEventState:
        return self.transition("done", data)

    def done_check(self, data: Any=None) -> ActiveEventState:
        return self.transition("done_check", data)

    def done_end_task(self, data: Any=None) -> ActiveEventState:
        return self.transition("done_end_task", data)

    def _ensure_state_machine_initialized(self) -> None:
        if not self._currentState:
            self._change_state_impl(self._initial_state, None)

    def changeState(self, targetState: ActiveEventState, data: Any=None) -> ActiveEventState:
        self._ensure_state_machine_initialized()
        return self._change_state_impl(targetState, data)

    def _change_state_impl(self, targetState: ActiveEventState, data: Any=None) -> ActiveEventState:
        if not targetState:
            raise Exception("No target state specified. Can not change the state.")

        # this also ignores the fact that maybe there is no transition
        # into the same state.
        if targetState == self._currentState:
            return targetState

        state_change_event: ActiveEventStateChangeEvent = ActiveEventStateChangeEvent(self._currentState, targetState, data)

        if self._currentState and \
                not transition_set.get(STATE_INDEX[self._currentState.value] << 14 | STATE_INDEX[targetState.value]):
            LOG.warning("No transition exists between %s -> %s." % (self._currentState.value, targetState.value))
            return self._currentState

        if self._current_change_state_event:
            # The previous_state if it's None, is only set when the initial transition happens into
            # the start state. Then only the *AFTER* callbacks are being invoked, not the *BEFORE*,
            # because entering the initial state is not cancellable. The state machine is assumed to
            # be in the initial state.
            #
            # Because of that, if there is another _current_change_state_event (i.e. set on a *BEFORE*
            # callback), it's after being already in the initial state, hence having a previous_state.
            assert self._currentState
            assert self._current_change_state_event.previous_state

            raise ActiveEventStateException(
                "The ActiveEventStateMachine is already in a changeState (%s -> %s). "
                "Transitioning the state machine (%s -> %s) in `before` events is not supported." % (
                    self._current_change_state_event.previous_state.value,
                    self._current_change_state_event.target_state.value,
                    self._currentState.value,
                    targetState.value
                ))

        self._current_change_state_event = state_change_event

        if state_change_event.previous_state:
            self._transition_listeners[state_change_event.previous_state.value]\
                .fire(EventType.BEFORE_LEAVE, state_change_event)

        self._transition_listeners[state_change_event.target_state.value]\
            .fire(EventType.BEFORE_ENTER, state_change_event)

        # The event can't be cancelled in the initial state.
        if state_change_event.cancelled:
            assert self._currentState
            return self._currentState

        LOG.debug(f"Transition: {self._currentState} -> {targetState}")

        self._currentState = targetState
        self._current_change_state_event = None

        if state_change_event.previous_state:
            self._transition_listeners[state_change_event.previous_state.value]\
                .fire(EventType.AFTER_LEAVE, state_change_event)

        self._transition_listeners[state_change_event.target_state.value]\
            .fire(EventType.AFTER_ENTER, state_change_event)

        return self._currentState

    def transition(self, link_name: str, data: Any=None) -> ActiveEventState:
        """
        Transition into another state following a named transition.

        :param str link_name:
        :param object data:
        :return: ActiveEventState
        """
        self._ensure_state_machine_initialized()

        assert self._currentState

        source_state = link_map.get(self._currentState.value)

        if not source_state:
            return self._currentState

        if link_name not in source_state:
            LOG.warning("There is no transition named `{}` starting from `{}`.",
                        link_name,
                        self._currentState.value)

            raise Exception("There is no transition named `%s` starting from `%s`." %
                            (link_name, self._currentState.value))

            return self._currentState

        targetState = source_state[link_name]

        if not targetState:
            return self._currentState

        return self.changeState(targetState, data)

    def before_enter(self, state: ActiveEventState, callback: ChangeStateEventListener):
        """
        Add a transition listener that will fire before entering a new state.
        The transition can still be cancelled at this stage via `ev.cancel()`
        in the callback.

        :param ActiveEventState state:
        :param Function callback:
        :return:
        """
        return self._transition_listeners[state.value].add_listener(EventType.BEFORE_ENTER, callback)

    def after_enter(self, state: ActiveEventState, callback: ChangeStateEventListener):
        """
        Add a transition listener that will fire after the new state is entered.
        The transition can not be cancelled at this stage.
        :param ActiveEventState state:
        :param callback:
        :return:
        """
        return self._transition_listeners[state.value].add_listener(EventType.AFTER_ENTER, callback)

    def before_leave(self, state: ActiveEventState, callback: ChangeStateEventListener):
        """
        Add a transition listener that will fire before leaving a state.
        The transition can be cancelled at this stage via `ev.cancel()`.

        :param ActiveEventState state:
        :param callback:
        :return:
        """
        return self._transition_listeners[state.value].add_listener(EventType.BEFORE_LEAVE, callback)

    def after_leave(self, state: ActiveEventState, callback: ChangeStateEventListener):
        """
        Add a transition listener that will fire after leaving a state.
        The transition can not be cancelled at this stage.

        :param ActiveEventState state:
        :param callback:
        :return:
        """
        return self._transition_listeners[state.value].add_listener(EventType.AFTER_LEAVE, callback)

    def on_data(self, state: ActiveEventState, callback: Callable[[Any], Optional[ActiveEventState]]):
        """
        Add a data listener that will be called when data is being pushed for that transition.

        :param ActiveEventState state:
        :param callback:
        :return:
        """
        return self._data_listeners[state.value].add_listener(EventType.DATA, callback)

    def forward_data(self, new_state: ActiveEventState, data: Any) -> None:
        """
        Changes the state machine into the new state, then sends the data
        ignoring the result. This is so on `onData` calls we can just
        short-circuit the execution using: `return stateMachine.forwardData(..)`

        @param new_state The state to transition into.
        @param data The data to send.
        """
        self.send_data(new_state, data)

        return None

    def send_state_data(self, new_state: ActiveEventState, data: Any) -> ActiveEventState:
        """
        Sends the data into the state machine, to be processed by listeners
        registered with `onData`.
        @param new_state
        @param data The data to send.
        """
        self._ensure_state_machine_initialized()

        assert self._currentState

        self.changeState(new_state, data)

        target_state = self._data_listeners[self._currentState.value].fire(EventType.DATA, data)

        if target_state:
            return self.changeState(target_state, data)

        return self._currentState

    def send_data(self,
                  data: Any=None,
                  state: Optional[ActiveEventState]=None) -> ActiveEventState:
        """
        Transitions first the state machine into the new state, then it
        will send the data into the state machine.
        @param newState
        @param data
        """
        self._ensure_state_machine_initialized()

        assert self._currentState

        if state:
            self.changeState(state)

        target_state = self._data_listeners[self._currentState.value]\
            .fire(EventType.DATA, data)

        if target_state:
            return self.changeState(target_state, data)

        return self._currentState


class EventType(Enum):
    BEFORE_ENTER = 'before-enter'
    BEFORE_LEAVE = 'before-leave'
    AFTER_LEAVE = 'after-leave'
    AFTER_ENTER = 'after-enter'
    DATA = 'data'


class EventListenerRegistration(object):
    def __init__(self, event_listener, callback_id):
        self._event_listener = event_listener
        self._callback_id = callback_id

    def detach(self):
        self._event_listener.eventListeners.pop(self._callback_id)


class EventListener(object):
    def __init__(self):
        self.registered = dict()

    def add_listener(self, event_name, callback):
        event_listeners = self.registered.get(event_name.value)

        if not event_listeners:
            event_listeners = self.registered[event_name.value] = dict()

        callback_id = uuid.uuid4()
        event_listeners[callback_id] = callback

        return EventListenerRegistration(self, callback_id)

    def fire(self, event_type, ev):
        result = None

        if not self.registered.get(event_type.value):
            return

        listeners = self.registered[event_type.value]

        for callback in listeners.values():
            potential_result = callback.__call__(ev)

            if potential_result and result:
                raise ActiveEventStateException("Data is already returned")

            result = potential_result

        return result
