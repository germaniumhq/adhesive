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
    adhesive_temp_folder = os.environ.get("ADHESIVE_TEMP_FOLDER", "/tmp/adhesive")

    return os.path.join(adhesive_temp_folder, item.execution.id, "workspaces", item.id)
