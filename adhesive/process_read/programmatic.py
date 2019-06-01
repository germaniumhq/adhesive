from typing import Optional

from adhesive.graph.Workflow import Workflow
import uuid


class WorkflowBuilder:
    def __init__(self):
        self.workflow = Workflow(str(uuid.uuid4()))

    def branch_start(self):
        pass

    def branch_end(self):
        pass

    def task(self,
             name: str,
             when: Optional[str] = None,
             break_when: Optional[str] = None,
             loop: Optional[str] = None):
        pass

    def sub_process_start(self,
                          name: str,
                          when: Optional[str] = None,
                          break_when: Optional[str] = None,
                          loop: Optional[str] = None):
        pass

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  break_when: Optional[str] = None,
                  loop: Optional[str] = None):
        pass


def process_start() -> WorkflowBuilder:
    return WorkflowBuilder()
