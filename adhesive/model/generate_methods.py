from typing import Iterable

import re

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.UserTask import UserTask


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


def display_unmatched_tasks(unmatched_tasks: Iterable[BaseTask]) -> None:
    print("Missing tasks implementations. Generate with:\n")

    for unmatched_task in unmatched_tasks:
        if isinstance(unmatched_task, UserTask):
            print(f"@adhesive.usertask('{generate_matching_re(unmatched_task.name)}')")
            print(f"def {generate_task_name(unmatched_task.name)}(context, ui):")
            print("    pass\n\n")
            continue

        print(f"@adhesive.task('{generate_matching_re(unmatched_task.name)}')")
        print(f"def {generate_task_name(unmatched_task.name)}(context):")
        print("    pass\n\n")

