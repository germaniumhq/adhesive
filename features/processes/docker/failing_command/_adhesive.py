import adhesive
from adhesive.workspace import docker


@adhesive.task("Failing docker inside task")
def failing_docker_inside_task(context: adhesive.Token):
    with docker.inside(context.workspace,
                       'ubuntu:20.04') as docker_workspace:
        docker_workspace.run('false')  # should fail


adhesive.build()
