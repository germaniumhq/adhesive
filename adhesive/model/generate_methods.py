from typing import Iterable

import re

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.UserTask import UserTask


INVALID_CHARACTER = re.compile(r'[^\w\d]')

def generate_task_name(name: str) -> str:
    return INVALID_CHARACTER.sub("_", name).lower()


def display_unmatched_tasks(unmatched_tasks: Iterable[BaseTask]) -> None:
    print("Missing tasks implementations. Generate with:\n")

    for unmatched_task in unmatched_tasks:
        if isinstance(unmatched_task, UserTask):
            print(f"@adhesive.usertask('{re.escape(unmatched_task.name)}')")
            print(f"def {generate_task_name(unmatched_task.name)}(context, ui):")
            print("    pass\n\n")
            continue

        print(f"@adhesive.task('{re.escape(unmatched_task.name)}')")
        print(f"def {generate_task_name(unmatched_task.name)}(context):")
        print("    pass\n\n")

