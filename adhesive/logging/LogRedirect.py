import sys
from contextlib import contextmanager

from adhesive.model.ActiveEvent import ActiveEvent


class StreamLogger:
    def __init__(self,
                 event: ActiveEvent,
                 post_fix: str) -> None:
        self.log = open(
            event.context.workspace,
            "w")

    def write(self, message):
        self.log.write(message)

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
def redirect_logs() -> None:
    log = None

    try:
        stdout = StreamLogger("stdout")
        stderr = StreamLogger("stderr")

        log = FileLogger(stdout, stderr)

        sys.stdout = log.stdout
        sys.stderr = log.stderr
    finally:
        if log:
            log.close()
