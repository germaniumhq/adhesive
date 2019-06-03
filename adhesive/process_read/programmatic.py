import uuid
from typing import Optional, Set, List

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Edge import Edge
from adhesive.graph.Loop import Loop
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.Task import Task
from adhesive.graph.Workflow import Workflow


class BranchDefinition:
    def __init__(self,
                 start_task: BaseTask):
        self.start_task = start_task
        self.last_task = start_task


class BranchSet:
    """
    A single parallel fork of branches.
    """
    def __init__(self, start_branch: BranchDefinition):
        self.branches: Set[BranchDefinition] = set()
        self.branches.add(start_branch)


class WorkflowBuilder:
    def __init__(self):
        self.workflow = Workflow(str(uuid.uuid4()))
        self.current_task = StartEvent(str(uuid.uuid4()), "<start>")
        self.workflow.add_start_event(self.current_task)

        self.nested_branches: List[BranchSet] = list()

    def branch_start(self) -> 'WorkflowBuilder':
        """
        We start a new branch set. The other branches will be
        added from the WorkflowBranchBuilder.
        :return:
        """
        new_branch = BranchDefinition(self.current_task)
        branch_set = BranchSet(new_branch)
        self.nested_branches.append(branch_set)

        return self

    def branch_end(self):
        pass

    def task(self,
             name: str,
             when: Optional[str] = None,
             loop: Optional[str] = None) -> 'WorkflowBuilder':
        new_task = Task(str(uuid.uuid4()), name)

        if loop is not None:
            new_task.loop = Loop(loop)

        new_edge = Edge(
            str(uuid.uuid4()),
            self.current_task.id,
            new_task.id,
            when)

        self.workflow.add_task(new_task)
        self.workflow.add_edge(new_edge)

        self.current_task = new_task

    def sub_process_start(self,
                          name: str,
                          when: Optional[str] = None,
                          loop: Optional[str] = None):
        pass

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None):
        pass


def process_start() -> WorkflowBuilder:
    return WorkflowBuilder()
