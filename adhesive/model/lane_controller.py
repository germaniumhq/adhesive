import adhesive
from typing import Optional

from adhesive.workspace.Workspace import Workspace
from adhesive.execution import token_utils
from adhesive.execution.ExecutionLaneId import ExecutionLaneId
from adhesive.workspace.local.LocalLinuxWorkspace import LocalLinuxWorkspace

from .ActiveEvent import ActiveEvent
from .AdhesiveProcess import AdhesiveProcess
from .AdhesiveLane import AdhesiveLane


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
    fill_in_lane_id(process, event)

    lane = find_existing_lane_for_event(process, event)

    if not lane:
        lane = create_lane_for_event(process, event)

    lane.references += 1

    event.context.workspace = lane.workspace.clone()


def deallocate_workspace(process: AdhesiveProcess,
                         event: ActiveEvent) -> None:
    """
    Deallocates a workspace. This also checks for potentially the need
    to destroy workspaces (including parent ones)
    """
    lane = find_existing_lane_for_event(process, event)

    if not lane:
        raise Exception(f"Unable to find lane for {event} on lane {event.context.lane}")

    lane.references -= 1

    if lane.references > 0:
        return

    lane.deallocate_lane()
    del process.lanes[event.context.lane.key]


def fill_in_lane_id(process: AdhesiveProcess,
                    event: ActiveEvent) -> None:
    """
    Ensures the lane_id is not the cloned one, but the one where the task
    resides.
    """
    lane_definition = process.process.get_lane_definition(event.task.id)
    lane_name = token_utils.parse_name(event.context, lane_definition.name)

    event.context.lane = ExecutionLaneId(
            lane_id=lane_definition.id,
            lane_name=lane_name)


def find_existing_lane_for_event(process: AdhesiveProcess,
                                 event: ActiveEvent) -> Optional[AdhesiveLane]:
    """
    Finds out the lane for an event (if it exists)
    """
    if event.context.lane.key not in process.lanes:
        return None

    return process.lanes[event.context.lane.key]


def create_lane_for_event(process: AdhesiveProcess,
                          event: ActiveEvent) -> None:
    """
    Creates the lane object and the associated workspace.
    """
    for lane_definition in process.lane_definitions:
        params = token_utils.matches(lane_definition.re_expressions,
                                     event.context.lane.name)

        if params is None:
            continue

        # create the lane object using the context
        gen = lane_definition.code(event.context)
        workspace = type(gen).__enter__(gen)

        if not isinstance(workspace, Workspace):
            raise Exception(f"The lane yielded the wrong type {type(workspace)} instead of a Workspace")

        lane = AdhesiveLane(event.context.lane, workspace, gen)
        process.lanes[event.context.lane.key] = lane

        return lane

    raise Exception(
            f"Unable to find any definition for lane "
            f"`{event.context.lane.name}`. Use the @adhesive.lane "
            f"decorator to create them, and yield the workspace.")

