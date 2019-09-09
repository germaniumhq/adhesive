import os
from typing import Union

from adhesive import config


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
    if isinstance(item, Workspace):
        return os.path.join(
            config.current.temp_folder,
            item.execution_id,
            "workspace")

    if isinstance(item, ActiveEvent):
        # FIXME: implement test when programmatic process builder is available
        return os.path.join(
            config.current.temp_folder,
            item.execution_id,
            "logs",
            _get_loop(item),
            item.task.id,
            item.token_id)

    if isinstance(item, str):
        return os.path.join(config.current.temp_folder, item)

    raise Exception(f"Unable to get_folder for {item}.")


def _get_loop(event: 'ActiveEvent') -> str:
    loop = event.context.loop
    result = ""

    while loop:
        result += f"_loop_{loop.index}/"
        loop = loop.parent_loop

    return result


from adhesive.model.ActiveEvent import ActiveEvent
from adhesive.workspace.Workspace import Workspace
