import adhesive
from adhesive.workspace import docker


@adhesive.lane("Docker Container")
def lane_docker_container(context):
    with docker.inside(context.workspace, "maven") as w:
        yield w


@adhesive.task("Create Docker Container")
def create_docker_container(context):
    context.data.container_id = docker.create_container(context.workspace, "maven")


@adhesive.task("^Touch File: (.*)$")
def touch_file(context, file_name):
    context.workspace.run(f"""
        touch {file_name}
    """)


@adhesive.task("^Check if File Exists: (.*)$")
def check_file_exists(context, file_name):
    context.workspace.run(f"""
        ls -l {file_name}
    """)


@adhesive.task("Tear Down Container")
def destroy_docker_container(context):
    docker.destroy_container(
        context.workspace,
        context.data.container_id)


adhesive.bpmn_build("lane.bpmn")