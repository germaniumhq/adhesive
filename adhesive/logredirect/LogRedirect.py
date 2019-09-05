import os
import sys
from contextlib import contextmanager
from typing import Union, Any
from threading import local

from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.logredirect import is_enabled
from adhesive import config

from threading import local


python_stdout = sys.stdout
python_stderr = sys.stderr


class StdThreadLocal(local):
    def __init__(self):
        self.__dict__["stdout"] = python_stdout
        self.__dict__["stderr"] = python_stderr


data = StdThreadLocal()


class ObjectForward:
    def __init__(self, key: str) -> None:
        self.__key = key

    def __getattribute__(self, key: str) -> Any:
        if key == "_ObjectForward__key":
            return super(ObjectForward, self).__getattribute__(key)

        return data.__getattribute__(self.__key).__getattribute__(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key == "_ObjectForward__key":
            return super(ObjectForward, self).__setattr__(key, value)

        data[self.__key].__setattr__(key, value)


sys.stdout = ObjectForward("stdout")
sys.stderr = ObjectForward("stderr")


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
    if not is_enabled:
        yield None
        return

    old_stdout = data.stdout
    old_stderr = data.stderr

    try:
        new_stdout = StreamLogger.from_event(old_stdout, event, "stdout")
        new_stderr = StreamLogger.from_event(old_stderr, event, "stderr")

        data.stdout = new_stdout
        data.stderr = new_stderr

        yield None
    finally:
        data.stdout = old_stdout
        data.stderr = old_stderr

        new_stdout.close()
        new_stderr.close()


from adhesive.storage.ensure_folder import ensure_folder
