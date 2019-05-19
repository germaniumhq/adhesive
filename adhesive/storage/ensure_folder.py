import os
from typing import Union


def ensure_folder(item: Union['Workspace', 'ActiveEvent', str]) -> str:
    """
    Ensures the folder for the given item exists.

    :param item:
    :return:
    """
    full_path = get_folder(item)
    os.makedirs(full_path, exist_ok=True)

    return full_path


def get_folder(item: Union['Workspace', 'ActiveEvent', str]) -> str:
    # FIXME: unify configuration?
    adhesive_temp_folder = os.environ.get("ADHESIVE_TEMP_FOLDER", "/tmp/adhesive")

    if isinstance(item, Workspace):
        return os.path.join(
            adhesive_temp_folder,
            item.execution.id,
            "workspaces",
            item.id)

    if isinstance(item, ActiveEvent):
        # FIXME: loop/parent loop check?
        return os.path.join(
            adhesive_temp_folder,
            item.context.execution.id,
            "logs",
            item.task.id,
            item.id)

    if isinstance(item, str):
        return os.path.join(adhesive_temp_folder, item)

    raise Exception(f"Unable to get_folder for {item}.")


from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.workspace.Workspace import Workspace