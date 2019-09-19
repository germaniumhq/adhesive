from typing import Iterable, Union

import re

from adhesive.graph.ComplexGateway import ComplexGateway
from adhesive.graph.BaseTask import BaseTask
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


def display_unmatched_items(unmatched_items: Iterable[Union[BaseTask, Lane]]) -> None:
    print("Missing tasks implementations. Generate with:\n")

    for unmatched_item in unmatched_items:
        if isinstance(unmatched_item, UserTask):
            print(f"@adhesive.usertask('{generate_matching_re(unmatched_item.name)}')")
            print(f"def {generate_task_name(unmatched_item.name)}(context, ui):")
            print("    pass\n\n")
            continue

        if isinstance(unmatched_item, Lane):
            print(f"@adhesive.lane('{generate_matching_re(unmatched_item.name)}')")
            print(f"def lane_{generate_task_name(unmatched_item.name)}(context):")
            print("    yield context.workspace.clone()\n\n")
            continue

        if isinstance(unmatched_item, ComplexGateway):
            print(f"@adhesive.gateway('{generate_matching_re(unmatched_item.name)}')")
        else:
            print(f"@adhesive.task('{generate_matching_re(unmatched_item.name)}')")

        print(f"def {generate_task_name(unmatched_item.name)}(context):")
        print("    pass\n\n")
