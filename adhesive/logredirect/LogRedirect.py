import os
import sys
from contextlib import contextmanager
from typing import Union, Any

from adhesive.model.ActiveEvent import ActiveEvent


class StreamLogger:
    def __init__(self,
                 name: str,
                 folder: str) -> None:
        if not folder:
            raise Exception(f"No folder specified for output: {folder}")

        self.log = open(
            os.path.join(folder, name),
            "at")

        self._closed = False

    @staticmethod
    def from_event(event: Union[ActiveEvent, str],
                   name: str) -> 'StreamLogger':
        folder = ensure_folder(event)
        return StreamLogger(name, folder)

    @property
    def fileno(self):
        return self.log.fileno

    def flush(self):
        self.log.flush()

    def write(self, message):
        if self._closed:
            raise Exception("already closed")

        self.log.write(message)
        self.log.flush()

    def close(self) -> None:
        self.log.close()
        self._closed = True


@contextmanager
def redirect_stdout(event: Union[ActiveEvent, str]) -> Any:
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        new_stdout = StreamLogger.from_event(event, "stdout")
        new_stderr = StreamLogger.from_event(event, "stderr")

        sys.stdout = new_stdout
        sys.stderr = new_stderr

        yield None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        new_stdout.close()
        new_stderr.close()


from adhesive.storage.ensure_folder import ensure_folder
