import os
from typing import Union


def ensure_folder(item: Union['Workspace', 'StreamLogger']) -> str:
    """
    Ensures the folder for the given item exists.

    :param item:
    :return:
    """
    full_path = get_folder(item)
    os.makedirs(full_path, exist_ok=True)

    return full_path


def get_folder(item: Union['Workspace', 'StreamLogger']) -> str:
    # FIXME: make the storage folder configurable.
    if isinstance(item, Workspace):
        return os.path.join(
            "/tmp/adhesive/",
            item.execution.id,
            "workspaces",
            item.id)

    if isinstance(item, StreamLogger):
        # FIXME: loop/parent loop check?
        return os.path.join(
            "/tmp/adhesive/",
            item.event.context.execution.id,
            "logs",
            item.event.task.id,
            item.event.id)


from adhesive.logging.LogRedirect import StreamLogger
from adhesive.workspace.Workspace import Workspace


