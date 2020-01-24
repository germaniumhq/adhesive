import adhesive


@adhesive.task('Sleep 2 Seconds')
def sleep_2_seconds(context: adhesive.Token) -> None:
    for i in range(1000):
        context.workspace.run("""
            sleep 1000
        """)


@adhesive.task('Timeout Happened')
def timeout_happened(context: adhesive.Token) -> None:
    context.data.timeout_happened = True


@adhesive.task('Should Not Execute')
def should_not_execute(context: adhesive.Token) -> None:
    raise Exception("Should not be called")


@adhesive.task('Error Happened')
def error_happened(context: adhesive.Token) -> None:
    context.data.error_happened = True


data = adhesive.bpmn_build("cancel-boundary.bpmn")
