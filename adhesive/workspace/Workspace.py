from abc import ABC, abstractmethod
from typing import Optional


class Workspace(ABC):
    """
    A workspace is a place where work can be done. That means a writable
    folder is being allocated, that will be cleaned up at the end of the
    execution.
    """
    def __init__(self,
                 pwd: str) -> None:
        self.pwd = pwd

    @abstractmethod
    def write_file(
            self,
            file_name: str,
            content: str) -> None:
        pass

    @abstractmethod
    def run(self, command: str) -> None:
        pass

    @abstractmethod
    def rm(self, path: Optional[str]=None) -> None:
        pass

    @abstractmethod
    def mkdir(self, path: str=None) -> None:
        pass

    @abstractmethod
    def temp_folder(self):
        pass
