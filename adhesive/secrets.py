import contextlib
import os
import re
from typing import Union

from adhesive.workspace.Workspace import Workspace
from adhesive import config

PARENT_PATH_RE = re.compile(r'^(.+)[\\/].+?$')


@contextlib.contextmanager
def secret(workspace: Workspace,
           secret_name: str,
           target_location: str) -> str:
    try:
        m = PARENT_PATH_RE.match(target_location)

        if m:
            workspace.mkdir(m.group(1))

        workspace.write_file(target_location, get_secret(secret_name))
        yield target_location
    finally:
        workspace.rm(target_location)


def get_secret(secret_name: str) -> Union[str, bytes]:
    for location in config.current.secret_locations():
        full_path = os.path.join(location, secret_name)
        if os.path.isfile(full_path):
            with open(full_path, "r") as f:
                return f.read()

    raise Exception(f"Unable to find secret {secret_name} in "
                    f"{config.current.secret_locations()}")

