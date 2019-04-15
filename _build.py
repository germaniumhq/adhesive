import adhesive


@adhesive.task("^Ensure tooling: (.+)$")
def ensure_tooling(context, tool_name: str) -> None:
    pass


@adhesive.task("^GBS: (.+)$")
def gbs_build(context, folder_name: str) -> None:
    pass


@adhesive.task("Run tool: mypy")
def run_mypy(context):
    pass


@adhesive.task("PyPi Publish")
def nexus_publish(context):
    pass


@adhesive.task("Nexus Publish")
def nexus_publish(context):
    pass


@adhesive.task("Archive")
def archive(context):
    pass


adhesive.bpmn_build('adhesive.bpmn')
