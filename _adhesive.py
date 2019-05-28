import textwrap

import adhesive
import gbs
from adhesive import scm
from adhesive.secrets import secret
from adhesive.workspace import docker

tools = {
    "mypy": textwrap.dedent("""\
        FROM germaniumhq/python:3.7
        ENV REFRESHED_AT 2018.10.14-06:56:31
        RUN pip install mypy
        """),

    "ansible": textwrap.dedent("""\
        FROM germaniumhq/python:3.7
        ENV REFRESHED_AT 2018.10.14-06:58:16
        RUN pip install ansible
    """),

    "flake8": textwrap.dedent("""\
        FROM germaniumhq/python:3.7
        ENV REFRESHED_AT 2018.10.14-06:56:31
        RUN pip install flake8
    """),

    "python": textwrap.dedent("""\
        FROM germaniumhq/python:3.7
    """),

    "behave": textwrap.dedent("""\
        FROM python:3.7

        RUN pip install behave
        RUN curl https://get.docker.com | sh
    """),

    "git": textwrap.dedent("""\
        FROM germaniumhq/ubuntu:18.04
        ENV REFRESHED_AT 2018.10.18-05:25:08
        USER root
        RUN apt update -y && apt install -y git && rm -rf /var/lib/apt/lists/*
        USER germanium
    """),

    "version-manager": textwrap.dedent("""\
        FROM bmst/version-manager:2.5.0
    """)
}


@adhesive.task("Read Parameters")
def read_parameters(context) -> None:
    context.data.run_mypy = False
    context.data.test_integration = True


@adhesive.task("Checkout Code")
def checkout_code(context) -> None:
    scm.checkout(context.workspace)


@adhesive.task(r"^Ensure Tooling:\s+(.+)$")
def ensure_tooling(context, tool_name) -> None:
    w = context.workspace

    with w.temp_folder():
        w.write_file("Dockerfile", tools[tool_name])
        w.run(f"docker build -t germaniumhq/tools-{tool_name}:latest .")


@adhesive.task("^Run tool: (.*?)$")
def run_tool(context, tool_name: str) -> None:
    with docker.inside(context.workspace,
                       f"germaniumhq/tools-{tool_name}") as w:
        w.run("mypy .")


@adhesive.task("GBS: lin64")
def gbs_build_lin64(context) -> None:
    gbs.build(workspace=context.workspace,
              platform="python:3.7",
              gbs_prefix=f"/_gbs/lin64/")


@adhesive.task("GBS Test: lin64")
def gbs_test_lin64(context) -> None:
    image_name = gbs.test(
        workspace=context.workspace,
        platform="python:3.7",
        tag="gbs_test",
        gbs_prefix=f"/_gbs/lin64/")

    with docker.inside(context.workspace, "gbs_test") as w:
        w.run("ADHESIVE_TEMP_FOLDER=/tmp/adhesive-test "
              "python -m unittest")


@adhesive.task("GBS Integration Test: lin64")
def gbs_integration_test_lin64(context) -> None:
    image_name = gbs.test(
        workspace=context.workspace,
        platform="python:3.7",
        tag="gbs_test",
        gbs_prefix=f"/_gbs/lin64/")

    with docker.inside(context.workspace, "gbs_test") as w:
        w.run("python --version")
        w.run("ADHESIVE_TEMP_FOLDER=/tmp/adhesive-test "
              "behave -t ~@manualtest")


@adhesive.task("GBS: win32")
def gbs_build_win32(context) -> None:
    pass
    #gbs.build(workspace=context.workspace,
    #          platform="python:win32",
    #          gbs_prefix=f"/_gbs/win32/")


@adhesive.task('^PyPI publish to (.+?)$')
def publish_to_pypi(context, registry):
    with docker.inside(context.workspace, "") as w:
        with secret(w, "PYPIRC_RELEASE_FILE", "/home/germanium/.pip/pip.conf"):
            w.run(f"python setup.py sdist upload -r {registry}")


@adhesive.usertask('Publish to PyPI\?')
def publish_to_pypi_confirm(context, ui):
    ui.add_checkbox_group(
        "publish",
        title="Publish",
        values=(
            ("nexus", "Publish to Nexus"),
            ("pypitest", "Publish to PyPI Test"),
            ("pypi", "Publish to PyPI"),
        ),
        value=("nexus","pypitest", "pypi")
    )


adhesive.bpmn_build("adhesive-self.bpmn")
