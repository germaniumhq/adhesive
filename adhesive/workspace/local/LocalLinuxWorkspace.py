import shutil
import subprocess
import os
import uuid

from contextlib import contextmanager
from typing import Optional

from adhesive.workspace.Workspace import Workspace


class LocalLinuxWorkspace(Workspace):
    """
    A workspace is a place where work can be done. That means a writable
    folder is being allocated, that will be cleaned up at the end of the
    execution.
    """
    def __init__(self,
                 pwd: Optional[str]=None) -> None:
        if not pwd:
            # FIXME: detect the temp folder
            pwd = os.path.join("/tmp/", str(uuid.uuid4()))
            os.mkdir(pwd)

        super(LocalLinuxWorkspace, self).__init__(pwd=pwd)

    def write_file(
            self,
            file_name: str,
            content: str) -> None:

        full_path = os.path.join(self.pwd, file_name)

        with open(full_path, "wt") as f:
            f.write(content)

    def run(self, command: str) -> None:
        subprocess.check_call([
            "/bin/sh", "-c", command
        ], cwd=self.pwd)

    def rm(self, path: Optional[str]=None) -> None:
        if path is None:
            shutil.rmtree(self.pwd)
            return

        if not path:
            raise Exception("You need to pass a subpath to delete")

        shutil.rmtree(os.path.join(self.pwd, path))

    def mkdir(self, path: str=None) -> None:
        os.mkdir(os.path.join(self.pwd, path))

    @contextmanager
    def temp_folder(self):
        current_folder = self.pwd
        folder = os.path.join(self.pwd, str(uuid.uuid4()))

        self.mkdir(folder)
        self.pwd = folder

        try:
            yield folder
        finally:
            self.rm(folder)
            self.pwd = current_folder
