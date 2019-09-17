import adhesive
from typing import Optional
import logging

from adhesive.graph.Process import Process
from adhesive.workspace.Workspace import Workspace
from adhesive.execution import token_utils
from adhesive.execution.ExecutionLaneId import ExecutionLaneId
from adhesive.workspace.local.LocalLinuxWorkspace import LocalLinuxWorkspace

from .ActiveEvent import ActiveEvent
from .AdhesiveProcess import AdhesiveProcess
from .AdhesiveLane import AdhesiveLane
from .ActiveLoopType import ActiveLoopType

LOG = logging.getLogger(__name__)


def ensure_default_lane(process: AdhesiveProcess) -> None:
    """
    Ensures the 'default' lane is defined.
    """
    default_lane_id = ExecutionLaneId("root", "default")

    if default_lane_id.key in process.lanes:
        return

    @adhesive.lane('default')
    def lane_default(context):
        yield LocalLinuxWorkspace(
                context.execution_id,
                context.token_id)


def allocate_workspace(process: AdhesiveProcess,
                       event: ActiveEvent) -> None:
    """
    Allocates a workspace. This matches against the available lanes,
    and creates the workspace.
    """
    LOG.debug(f"Lane allocate workspace check for {event}")

    original_execution_lane_id = event.context.lane
    fill_in_lane_id(process, event)

    lane = find_existing_lane_for_event(process, event)

    if not lane:
        LOG.debug(f"Crating a new lane for {event}")
        lane = create_lane_for_event(process, event, original_execution_lane_id)

    lane.increment_references()

    event.context.workspace = lane.workspace.clone()


def deallocate_workspace(process: AdhesiveProcess,
                         event: ActiveEvent) -> None:
    """
    Deallocates a workspace. This also checks for potentially the need
    to destroy workspaces (including parent ones)
    """
    LOG.debug(f"Lane deallocate workspace check for {event}")

    lane = find_existing_lane_for_event(process, event)

    if not lane:
        raise Exception(f"Unable to find lane for {event} on lane {event.context.lane}")

    lane.decrement_references()

    while lane and lane.references == 0:
        parent_lane = lane.parent_lane

        lane.deallocate_lane()
        del process.lanes[lane.lane_id.key]

        lane = parent_lane


def fill_in_lane_id(process: AdhesiveProcess,
                    event: ActiveEvent) -> None:
    """
    Ensures the lane_id is not the cloned one, but the one where the task
    resides.
    """
    parent_process = event.task.parent_process

    if not parent_process and isinstance(event.task, Process):
        parent_process = event.task

    lane_definition = parent_process.get_lane_definition(event.task.id)

    event.context.lane = ExecutionLaneId(
            lane_id=lane_definition.id,
            lane_name=lane_definition.name)


def find_existing_lane_for_event(process: AdhesiveProcess,
                                 event: ActiveEvent) -> Optional[AdhesiveLane]:
    """
    Finds out the lane for an event (if it exists)
    """
    if event.context.lane.key not in process.lanes:
        return None

    return process.lanes[event.context.lane.key]


def create_lane_for_event(process: AdhesiveProcess,
                          event: ActiveEvent,
                          execution_lane_id: ExecutionLaneId) -> None:
    """
    Creates the lane object and the associated workspace.
    """
    for lane_definition in process.lane_definitions:
        params = token_utils.matches(lane_definition.re_expressions,
                                     event.context.lane.name)

        if params is None:
            continue

        # create the lane object using the context
        gen = lane_definition.code(event.context, *params)

        workspace = type(gen).__enter__(gen)

        if not isinstance(workspace, Workspace):
            raise Exception(f"The lane yielded the wrong type {type(workspace)} instead of a Workspace")

        if execution_lane_id:
            parent_lane = process.lanes[execution_lane_id.key]
        else:
            parent_lane = None

        lane = AdhesiveLane(
            lane_id=event.context.lane,
            workspace=workspace,
            generator=gen,
            parent_lane=parent_lane)

        process.lanes[event.context.lane.key] = lane

        return lane

    raise Exception(
            f"Unable to find any definition for lane "
            f"`{event.context.lane.name}`. Use the @adhesive.lane "
            f"decorator to create them, and yield the workspace.")

