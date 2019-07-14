import os
import sys
from contextlib import contextmanager
from typing import Union, Any

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive import config


class StreamLogger:
    def __init__(self,
                 old_stdout: Any,
                 name: str,
                 folder: str) -> None:
        if not folder:
            raise Exception(f"No folder specified for output: {folder}")

        self.log = open(
            os.path.join(folder, name),
            "at")
        self.old_stdout = old_stdout

        self._closed = False

    @staticmethod
    def from_event(old_stdout: Any,
                   event: Union[ActiveEvent, str],
                   name: str) -> 'StreamLogger':
        folder = ensure_folder(event)
        return StreamLogger(old_stdout, name, folder)

    @property
    def fileno(self):
        return self.log.fileno

    def flush(self):
        self.log.flush()

    def write(self, message):
        if self._closed:
            raise Exception("already closed")

            self.old_stdout.write(message)
            self.old_stdout.flush()

        self.log.write(message)
        self.log.flush()

    def close(self) -> None:
        self.log.close()
        self._closed = True


@contextmanager
def redirect_stdout(event: Union[ActiveEvent, str]) -> Any:
    if config.current.stdout:
        yield None
        return

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        new_stdout = StreamLogger.from_event(old_stdout, event, "stdout")
        new_stderr = StreamLogger.from_event(old_stderr, event, "stderr")

        sys.stdout = new_stdout
        sys.stderr = new_stderr

        yield None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        new_stdout.close()
        new_stderr.close()


from adhesive.storage.ensure_folder import ensure_folder
