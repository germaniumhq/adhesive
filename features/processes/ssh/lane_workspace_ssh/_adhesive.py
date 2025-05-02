import random

import adhesive
from adhesive.workspace import ssh


def find_open_port() -> int:
    # FIXME: this should find an open port on the host, not inside the
    # docker container. a bit trickier to do.
    port = random.randint(10000, 60000)
    return port


@adhesive.lane("ssh")
def lane_ssh(token):
    with ssh.inside(
        token.workspace,
        "172.17.0.1",
        username="root",
        password="root",
        port=token.data.ssh_port,
    ) as w:
        yield w


@adhesive.task("Start SSH Server")
def start_ssh_server(token):
    print("starting server...")
    token.data.ssh_port = find_open_port()
    container_id = token.workspace.run(
        f"docker run -d -p {token.data.ssh_port}:22 rastasheep/ubuntu-sshd:18.04",
        capture_stdout=True,
    )

    token.data.container_id = container_id
    print("[OK] started server")


@adhesive.task("Task")
def run_ls_in_ssh(token):
    print(token.workspace)
    token.workspace.run(
        f"""
        whoami
        ls -la
    """
    )


@adhesive.task("Shutdown Server")
def shutdown_server(token):
    print("shutting down server...")
    token.workspace.run(f"docker rm -f {token.data.container_id}")
    print("[OK] server was shutdown")


@adhesive.task("Raise Error")
def raise_error(token: adhesive.Token) -> None:
    raise token.data.event


# We need to create more than the number of available channels, to see if we leak
# channels with executions. Another limit is the amount of parallel connections.
# For that we configure the pool_size in the `.adhesive/config.yml` in this folder.
adhesive.bpmn_build(
    "lane-workspace.bpmn",
    initial_data={
        "items": range(40),
    }
)
