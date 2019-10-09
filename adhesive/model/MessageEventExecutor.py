import logging
import uuid
from concurrent.futures import Future
from threading import Thread

from adhesive import ExecutionMessageEvent
from adhesive.consoleui.color_print import green, red, yellow
from adhesive.execution import token_utils
from adhesive.graph.MessageEvent import MessageEvent
from adhesive.model.ActiveEvent import ActiveEvent

LOG = logging.getLogger(__name__)


class MessageEventExecutor:
    def __init__(self,
                 root_event: ActiveEvent,
                 message_event: MessageEvent,
                 execution_message_event: ExecutionMessageEvent,
                 clone_event) -> None:
        self.id = str(uuid.uuid4())

        self.root_event = root_event
        self.message_event = message_event
        self.execution_message_event = execution_message_event
        self.clone_event = clone_event

        self.future = Future()

        Thread(target=self.run_thread_loop).start()

    def run_thread_loop(self):
        event_name_parsed = token_utils.parse_name(
            self.root_event.context,
            self.message_event.name)
        LOG.info(yellow("Run  ") + yellow(event_name_parsed, bold=True))

        # FIXME: implement a decent test
        try:
            params = token_utils.matches(self.execution_message_event.re_expressions,
                                         event_name_parsed)

            for event_data in self.execution_message_event.code(self.root_event.context, *params):
                new_event = self.clone_event(
                    self.root_event,
                    self.message_event,
                    parent_id=self.root_event.token_id)

                new_event.context.data.event = event_data
        except Exception as e:
            LOG.info(red("Failed ") + red(event_name_parsed, bold=True))
            LOG.debug(e)
            self.future.set_exception(e)
        else:
            LOG.info(green("Done ") + green(event_name_parsed, bold=True))
            self.future.set_result("__done")
