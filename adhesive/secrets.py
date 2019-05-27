import contextlib
import os

from adhesive.workspace.Workspace import Workspace
from adhesive import config


@contextlib.contextmanager
def secret(workspace: Workspace,
           secret_name: str,
           target_location: str) -> str:
    try:
        workspace.write_file(target_location, get_secret(secret_name))
        yield target_location
    finally:
        workspace.rm(target_location)


def get_secret(secret_name: str) -> str:
    for location in config.current.secret_locations():
        full_path = os.path.join(location, secret_name)
        if os.path.isfile(full_path):
            with open(full_path, "rt") as f:
                return f.read()

    raise Exception(f"Unable to find secret {secret_name} in "
                    f"{config.current.secret_locations()}")

