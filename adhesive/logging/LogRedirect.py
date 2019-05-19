import os
import sys
from contextlib import contextmanager
from typing import Optional, Union

from adhesive.model.ActiveEvent import ActiveEvent

stdout = sys.stdout
stderr = sys.stderr


_real_stdout = sys.stdout
_real_stderr = sys.stdout


class StreamLogger:
    def __init__(self,
                 name: str,
                 folder: Optional[str]=None) -> None:
        if not folder:
            raise Exception(f"No folder specified for output: {folder}")

        if not folder:
            folder = ensure_folder(self)

        self.log = open(
            os.path.join(folder, name),
            "at")

        self._closed = False

    @staticmethod
    def from_event(event: Union[ActiveEvent, str],
                   name: str) -> 'StreamLogger':
        folder = ensure_folder(event)
        return StreamLogger(name, folder)

    def flush(self):
        pass

    def write(self, message):
        if self._closed:
            raise Exception("already closed")
        self.log.write(message)
        self.log.flush()

    def close(self) -> None:
        self.log.close()
        self._closed = True


class FileLogger:
    def __init__(self,
                 stdout: StreamLogger,
                 stderr: StreamLogger) -> None:
        self.stdout = stdout
        self.stderr = stderr

    def close(self) -> None:
        self.stdout.close()
        self.stderr.close()


@contextmanager
def redirect_stdout(event: Union[ActiveEvent, str]) -> None:
    global stdout
    global stderr

    log = None

    old_stdout = stdout
    old_stderr = stderr

    try:
        stdout = StreamLogger.from_event(event, "stdout")
        stderr = StreamLogger.from_event(event, "stderr")

        log = FileLogger(stdout, stderr)

        sys.stdout = log.stdout
        sys.stderr = log.stderr

        yield None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        log.close()


from adhesive.storage.ensure_folder import ensure_folder
