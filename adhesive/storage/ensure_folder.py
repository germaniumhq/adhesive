import os
from typing import Union

from adhesive.workspace.Workspace import Workspace


def ensure_folder(item: Union[Workspace]) -> str:
    """
    Ensures the folder for the given item exists.

    :param item:
    :return:
    """
    full_path = get_folder(item)
    os.makedirs(full_path, exist_ok=True)

    return full_path


def get_folder(item: Union[Workspace]) -> str:
    # FIXME: make the storage folder configurable.
    return os.path.join("/tmp/adhesive/", item.execution.id, "workspaces", item.id)
