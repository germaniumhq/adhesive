from typing import Iterable, Union

import re

from adhesive.graph.ComplexGateway import ComplexGateway
from adhesive.graph.MessageEvent import MessageEvent
from adhesive.graph.ProcessTask import ProcessTask
from adhesive.graph.UserTask import UserTask
from adhesive.graph.Lane import Lane


INVALID_CHARACTER = re.compile(r'[^\w\d]')
MULTIPLE_UNDERSCORES = re.compile(r'_+')

LABEL_EXPRESSION = re.compile(r'\\\{.*?\\\}')
SPACES = re.compile(r'\\ ')


def generate_task_name(name: str) -> str:
    result = INVALID_CHARACTER.sub("_", name)
    result = MULTIPLE_UNDERSCORES.sub("_", result)
    result = result.lower()

    return result


def generate_matching_re(name: str) -> str:
    result = re.escape(name)
    result = LABEL_EXPRESSION.sub('.*?', result)
    result = SPACES.sub(' ', result)

    return result


def escape_string(name: str) -> str:
    return repr(name)


def display_unmatched_items(unmatched_items: Iterable[Union[ProcessTask, Lane]]) -> None:
    print("Missing tasks implementations. Generate with:\n")

    for unmatched_item in unmatched_items:
        if isinstance(unmatched_item, UserTask):
            print(f"@adhesive.usertask({escape_string(unmatched_item.name)})")
            print(f"def {generate_task_name(unmatched_item.name)}(context, ui):")
            print("    pass\n\n")
            continue

        if isinstance(unmatched_item, Lane):
            print(f"@adhesive.lane({escape_string(unmatched_item.name)})")
            print(f"def lane_{generate_task_name(unmatched_item.name)}(context):")
            print("    yield context.workspace.clone()\n\n")
            continue

        if isinstance(unmatched_item, MessageEvent):
            print(f"@adhesive.message({escape_string(unmatched_item.name)})")
            print(f"def message_{generate_task_name(unmatched_item.name)}(context):")
            print("    message_data = 'data'")
            print("    yield message_data\n\n")
            continue

        if isinstance(unmatched_item, ComplexGateway):
            print(f"@adhesive.gateway({escape_string(unmatched_item.name)})")
        else:
            print(f"@adhesive.task({escape_string(unmatched_item.name)})")

        print(f"def {generate_task_name(unmatched_item.name)}(context):")
        print("    pass\n\n")
