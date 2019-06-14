from typing import Optional, List, Callable

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Edge import Edge
from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.Loop import Loop
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.Task import Task
from adhesive.graph.UserTask import UserTask
from adhesive.graph.Workflow import Workflow


current_id = 0


class BranchDefinition:
    def __init__(self,
                 start_task: BaseTask):
        self.start_task = start_task
        self.last_task = start_task


class BranchGroup:
    """
    A single parallel fork of branches.
    """
    def __init__(self, start_branch: BranchDefinition):
        self.branches: List[BranchDefinition] = list()
        self.branches.append(start_branch)


class BranchEndBuilder:
    def __init__(self,
                 workflow_builder: 'WorkflowBuilder') -> None:
        self.workflow_builder = workflow_builder

    def branch_start(self) -> 'WorkflowBuilder':
        """
        We start a new branch in this branch set.
        :return:
        """
        branch_group = self.workflow_builder.nested_branches[-1]
        last_branch = branch_group.branches[-1]

        self.workflow_builder.current_task = last_branch.start_task
        new_branch = BranchDefinition(last_branch.start_task)
        branch_group.branches.append(new_branch)

        return self.workflow_builder

    def task(self,
             name: str,
             when: Optional[str] = None,
             loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        The branching is done now, we need to close a branch level.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        new_task = Task(next_id(), name)
        return self._wire_task_list(new_task, when=when, loop=loop)

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        The branching is done now, we need to close a branch level.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        new_task = UserTask(next_id(), name)
        return self._wire_task_list(new_task, when=when, loop=loop)

    def sub_process_start(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        We start a sub process.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        sub_process_builder = WorkflowBuilder(
            parent_builder=self.workflow_builder,
            desired_type=SubProcess,
            name=name,
        )

        self._wire_task_list(sub_process_builder.workflow,
                        loop=loop,
                        when=when)

        return sub_process_builder

    def process_end(self,
             when: Optional[str] = None,
             loop: Optional[str] = None) -> 'WorkflowBuilder':
        new_task = EndEvent(next_id(), name="<end-event>")
        return self._wire_task_list(new_task, when=when, loop=loop)

    def _wire_task_list(self,
                        new_task: BaseTask,
                        when: Optional[str] = None,
                        loop: Optional[str] = None):
        branch_group = self.workflow_builder.nested_branches[-1]
        last_tasks = [branch.last_task for branch in branch_group.branches]

        self.workflow_builder.nested_branches.pop()

        return self.workflow_builder._wire_task_list(last_tasks, new_task, when=when, loop=loop)


class WorkflowBuilder:
    def __init__(self,
                 parent_builder: Optional['WorkflowBuilder'],
                 desired_type=Workflow,
                 _build: Optional[Callable] = None,
                 name: Optional[str] = None):
        self.parent_builder = parent_builder

        self.workflow = desired_type(next_id(), name="<process>" if name is None else name)
        self.current_task = StartEvent(next_id(), "<start>")
        self.workflow.add_start_event(self.current_task)

        self.nested_branches: List[BranchGroup] = list()
        self._build = _build

    def branch_start(self) -> 'WorkflowBuilder':
        """
        We start a new branch set. The other branches will be
        added from the WorkflowBranchBuilder.
        :return:
        """
        new_branch = BranchDefinition(self.current_task)
        branch_set = BranchGroup(new_branch)
        self.nested_branches.append(branch_set)

        return self

    def branch_end(self) -> 'BranchEndBuilder':
        """
        We end the branch set.
        :return:
        """
        return BranchEndBuilder(self)

    def task(self,
             name: str,
             when: Optional[str] = None,
             loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        We add a regular task in the workflow.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        new_task = Task(next_id(), name)
        return self._wire_task(new_task, loop=loop, when=when)

    def process_end(self) -> 'WorkflowBuilder':
        new_task = EndEvent(next_id(), name="<end-event>")
        return self._wire_task(new_task)

    def sub_process_start(self,
                          name: Optional[str] = None,
                          when: Optional[str] = None,
                          loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        We start a subprocess. Subprocesses can also loop over the whole subprocess.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        sub_process_builder = WorkflowBuilder(
            parent_builder=self,
            desired_type=SubProcess,
            name=name,
        )

        self._wire_task(sub_process_builder.workflow,
                        loop=loop,
                        when=when)

        return sub_process_builder

    def sub_process_end(self) -> 'WorkflowBuilder':
        """
        End a subprocess definition.
        :return:
        """
        if not self.parent_builder:
            raise Exception("Not in a subprocess. You need to call `sub_process_start()` to "
                            "start a subprocess definition.")

        self.process_end()
        self.current_task = self.workflow

        return self.parent_builder

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None):
        new_task = UserTask(next_id(), name)
        self._wire_task(new_task, when=when, loop=loop)

        return self

    def build(self, *args, **kw):
        if not self._build:
            raise Exception("Not in the root process. build() is only available on the topmost "
                            "workflow.")

        return self._build(*args, **kw)

    def _wire_task(self,
                   new_task: BaseTask,
                   when: Optional[str] = None,
                   loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        Wire the given task in the workflow.
        :param new_task:
        :param when:
        :param loop:
        :return:
        """
        if loop is not None:
            new_task.loop = Loop(loop)

        if isinstance(new_task, EndEvent):
            self.workflow.add_end_event(new_task)
        else:
            self.workflow.add_task(new_task)

        if self.nested_branches:
            self.nested_branches[-1].branches[-1].last_task = new_task

        new_edge = Edge(
            next_id(),
            self.current_task.id,
            new_task.id,
            when)

        self.current_task = new_task
        self.workflow.add_edge(new_edge)

        return self

    def _wire_task_list(self,
                        previous_tasks: List[BaseTask],
                        new_task: BaseTask,
                        when: Optional[str] = None,
                        loop: Optional[str] = None) -> 'WorkflowBuilder':
        """
        Wire the given task in the workflow.
        :param new_task:
        :param when:
        :param loop:
        :return:
        """
        if loop is not None:
            new_task.loop = Loop(loop)

        if isinstance(new_task, EndEvent):
            self.workflow.add_end_event(new_task)
        else:
            self.workflow.add_task(new_task)

        self.current_task = new_task

        for previous_task in previous_tasks:
            new_edge = Edge(
                next_id(),
                previous_task.id,
                new_task.id,
                when)

            self.workflow.add_edge(new_edge)

        return self


def next_id():
    global current_id

    current_id += 1
    return f"_{current_id}"


def generate_from_calls(_build) -> WorkflowBuilder:
    return WorkflowBuilder(
        parent_builder=None,
        desired_type=Workflow,
        _build=_build,
    )
