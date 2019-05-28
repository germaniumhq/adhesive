import adhesive
from adhesive.secrets import secret
from adhesive.workspace import docker
from adhesive.steps.ExecutionToken import ExecutionToken


@adhesive.task("Test Secret On Local Workspace")
def test_secret_on_local_workspace(context: ExecutionToken):
    with secret(context.workspace,
                "SECRET_FILE",
                "/tmp/secret.file"):
        context.workspace.run("cat /tmp/secret.file")


@adhesive.task("Test Secret On Docker Workspace")
def test_secret_on_docker_workspace(context):
    with docker.inside(context.workspace, "ubuntu:18.04") as w:
        with secret(w, "SECRET_FILE", "/tmp/secret.file"):
            w.run("cat /tmp/secret.file")


adhesive.build()
