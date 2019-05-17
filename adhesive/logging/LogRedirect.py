import os
import sys
from contextlib import contextmanager

from adhesive.model.ActiveEvent import ActiveEvent


class StreamLogger:
    def __init__(self,
                 event: ActiveEvent,
                 name: str) -> None:
        self.event = event

        if not isinstance(event, ActiveEvent):
            raise Exception(f"Not an event: {event}")

        folder = ensure_folder(self)

        self.log = open(
            os.path.join(folder, name),
            "wt")

    def write(self, message):
        self.log.write(message)
        self.log.flush()

    def close(self) -> None:
        self.log.close()


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
def redirect_stdout(event: ActiveEvent) -> None:
    log = None

    try:
        stdout = StreamLogger(event, "stdout")
        stderr = StreamLogger(event, "stderr")

        log = FileLogger(stdout, stderr)

        sys.stdout = log.stdout
        sys.stderr = log.stderr

        yield None
    finally:
        if log:
            log.close()


from adhesive.storage.ensure_folder import ensure_folder
