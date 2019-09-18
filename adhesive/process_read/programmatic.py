from typing import Optional, List, Callable

from adhesive.graph.BaseTask import BaseTask
from adhesive.graph.Edge import Edge
from adhesive.graph.EndEvent import EndEvent
from adhesive.graph.Loop import Loop
from adhesive.graph.StartEvent import StartEvent
from adhesive.graph.SubProcess import SubProcess
from adhesive.graph.Task import Task
from adhesive.graph.Lane import Lane
from adhesive.graph.UserTask import UserTask
from adhesive.graph.Process import Process


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
                 process_builder: 'ProcessBuilder') -> None:
        self.process_builder = process_builder

    def branch_start(self) -> 'ProcessBuilder':
        """
        We start a new branch in this branch set.
        :return:
        """
        branch_group = self.process_builder.nested_branches[-1]
        last_branch = branch_group.branches[-1]

        self.process_builder.current_task = last_branch.start_task
        new_branch = BranchDefinition(last_branch.start_task)
        branch_group.branches.append(new_branch)

        return self.process_builder

    def task(self,
             name: str,
             when: Optional[str] = None,
             loop: Optional[str] = None,
             lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        The branching is done now, we need to close a branch level.
        :param name:
        :param when:
        :param loop:
        :param lane:
        :return:
        """
        new_task = Task(
            parent_process=self.process_builder.process,
            id=next_id(),
            name=name)
        return self._wire_task_list(new_task, when=when, loop=loop, lane=lane)

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None,
                  lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        The branching is done now, we need to close a branch level.
        :param name:
        :param when:
        :param loop:
        :return:
        """
        new_task = UserTask(
            parent_process=self.process_builder.process,
            id=next_id(),
            name=name)
        return self._wire_task_list(new_task, when=when, loop=loop, lane=lane)

    def sub_process_start(self,
                  name: str,
                  lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        We start a sub process.
        :param name:
        :return:
        """
        sub_process_builder = ProcessBuilder(
            parent_builder=self.process_builder,
            desired_type=SubProcess,
            name=name,
        )

        self._wire_task_list(sub_process_builder.process,
                        lane=lane)

        return sub_process_builder

    def process_end(self, lane: Optional[str] = None) -> 'ProcessBuilder':
        new_task = EndEvent(
            parent_process=self.process_builder.process,
            id=next_id(),
            name="<end-event>")

        return self._wire_task_list(new_task, lane=lane)

    def _wire_task_list(self,
                        new_task: BaseTask,
                        when: Optional[str] = None,
                        loop: Optional[str] = None,
                        lane: Optional[str] = None):
        branch_group = self.process_builder.nested_branches[-1]
        last_tasks = [branch.last_task for branch in branch_group.branches]

        self.process_builder.nested_branches.pop()

        return self.process_builder._wire_task_list(
            last_tasks,
            new_task,
            when=when,
            loop=loop,
            lane=lane)


class ProcessBuilder:
    def __init__(self,
                 parent_builder: Optional['ProcessBuilder'],
                 desired_type=Process,
                 _build: Optional[Callable] = None,
                 name: Optional[str] = None):
        self.parent_builder = parent_builder

        self.process = desired_type(
            parent_process=parent_builder.process if parent_builder else None,
            id=next_id(),
            name="<process>" if name is None else name)

        self.current_task = StartEvent(
            parent_process=self.process,
            id=next_id(),
            name="<start>")

        self.process.add_start_event(self.current_task)

        self.nested_branches: List[BranchGroup] = list()
        self._build = _build

    def branch_start(self) -> 'ProcessBuilder':
        """
        We start a new branch set. The other branches will be
        added from the ProcessBranchBuilder.
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
             loop: Optional[str] = None,
             lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        We add a regular task in the process.
        :param name:
        :param when:
        :param loop:
        :param lane:
        :return:
        """
        new_task = Task(
            parent_process=self.process,
            id=next_id(),
            name=name)

        return self._wire_task(new_task, loop=loop, when=when, lane=lane)

    def process_end(self) -> 'ProcessBuilder':
        new_task = EndEvent(
            parent_process=self.process,
            id=next_id(),
            name="<end-event>")

        return self._wire_task(new_task)

    def sub_process_start(self,
                          name: Optional[str] = None,
                          when: Optional[str] = None,
                          loop: Optional[str] = None,
                          lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        We start a subprocess. Subprocesses can also loop over the whole subprocess.
        :param name:
        :param when:
        :param loop:
        :param lane:
        :return:
        """
        sub_process_builder = ProcessBuilder(
            parent_builder=self,
            desired_type=SubProcess,
            name=name,
        )

        self._wire_task(sub_process_builder.process,
                        loop=loop,
                        when=when,
                        lane=lane)

        return sub_process_builder

    def sub_process_end(self) -> 'ProcessBuilder':
        """
        End a subprocess definition.
        :return:
        """
        if not self.parent_builder:
            raise Exception("Not in a subprocess. You need to call `sub_process_start()` to "
                            "start a subprocess definition.")

        self.process_end()
        self.current_task = self.process

        return self.parent_builder

    def user_task(self,
                  name: str,
                  when: Optional[str] = None,
                  loop: Optional[str] = None,
                  lane: Optional[str] = None):
        new_task = UserTask(
            parent_process=self.process,
            id=next_id(),
            name=name)
        self._wire_task(new_task, when=when, loop=loop, lane=lane)

        return self

    def build(self, *args, **kw):
        if not self._build:
            raise Exception("Not in the root process. build() is only available on the topmost "
                            "process.")

        return self._build(*args, **kw)

    def _wire_task(self,
                   new_task: BaseTask,
                   when: Optional[str] = None,
                   loop: Optional[str] = None,
                   lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        Wire the given task in the process.
        :param new_task:
        :param when:
        :param loop:
        :return:
        """
        if loop is not None:
            new_task.loop = Loop(loop, parallel=True)

        if isinstance(new_task, EndEvent):
            self.process.add_end_event(new_task)
        else:
            self.process.add_task(new_task)

        if self.nested_branches:
            self.nested_branches[-1].branches[-1].last_task = new_task

        new_edge = Edge(
            next_id(),
            self.current_task.id,
            new_task.id,
            when)

        self.current_task = new_task
        self.process.add_edge(new_edge)

        if lane is None:
            return self

        # we have a lane to consider
        lane_element = self.process.lanes.get(lane, None)

        if not lane_element:
            lane_element = Lane(next_id(), lane)
            self.process.add_lane(lane_element)

        self.process.add_task_to_lane(lane_element, new_task.id)

        return self

    def _wire_task_list(self,
                        previous_tasks: List[BaseTask],
                        new_task: BaseTask,
                        when: Optional[str] = None,
                        loop: Optional[str] = None,
                        lane: Optional[str] = None) -> 'ProcessBuilder':
        """
        Wire the given task in the process.
        :param new_task:
        :param when:
        :param loop:
        :param lane:
        :return:
        """
        if loop is not None:
            new_task.loop = Loop(loop)

        if isinstance(new_task, EndEvent):
            self.process.add_end_event(new_task)
        else:
            self.process.add_task(new_task)

        self.current_task = new_task

        for previous_task in previous_tasks:
            new_edge = Edge(
                next_id(),
                previous_task.id,
                new_task.id,
                when)

            self.process.add_edge(new_edge)

        if lane is None:
            return self

        # we have a lane to consider
        lane_element = self.process.lanes.get(lane, None)

        if not lane_element:
            lane_element = Lane(next_id(), lane)
            self.process.add_lane(lane_element)

        self.process.add_task_to_lane(lane_element, new_task.id)

        return self


def next_id():
    global current_id

    current_id += 1
    return f"_{current_id}"


def generate_from_calls(_build) -> ProcessBuilder:
    return ProcessBuilder(
        parent_builder=None,
        desired_type=Process,
        _build=_build,
    )
