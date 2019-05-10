import os
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
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
        """
        Run a new command in the current workspace.

        :param command:
        :return:
        """
        pass

    @abstractmethod
    def rm(self, path: Optional[str]=None) -> None:
        """
        Recursively remove the file or folder given as path. If no path is sent,
        the whole workspace will be cleared.

        :param path:
        :return:
        """
        pass

    @abstractmethod
    def mkdir(self, path: str=None) -> None:
        """
        Create a folder, including all its needed parents.

        :param path:
        :return:
        """
        pass

    @abstractmethod
    def copy_to_agent(self,
                      from_path: str,
                      to_path: str) -> None:
        """
        Copy the files to the agent from the current disk.
        :param from_path:
        :param to_path:
        :return:
        """
        pass

    @abstractmethod
    def copy_from_agent(self,
                        from_path: str,
                        to_path: str) -> None:
        """
        Copy the files from the agent to the current disk.
        :param from_path:
        :param to_path:
        :return:
        """
        pass

    @contextmanager
    def temp_folder(self):
        """
        Create a temporary folder in the current `pwd` that will be deleted
        when the `with` block ends.

        :return:
        """
        current_folder = self.pwd
        folder = os.path.join(self.pwd, str(uuid.uuid4()))

        self.mkdir(folder)
        self.pwd = folder

        try:
            yield folder
        finally:
            self.rm(folder)
            self.pwd = current_folder

    @contextmanager
    def chdir(self, target_folder: str):
        current_folder = self.pwd
        folder = os.path.join(self.pwd, target_folder)

        self.pwd = folder

        try:
            yield folder
        finally:
            self.pwd = current_folder
