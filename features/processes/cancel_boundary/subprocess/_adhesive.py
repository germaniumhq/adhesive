import adhesive


@adhesive.task('Sleep 10 seconds')
def sleep_10_seconds(context: adhesive.Token) -> None:
    context.workspace.run("""
        sleep 10
    """)


@adhesive.task('Should not execute')
def should_not_execute(context: adhesive.Token) -> None:
    raise Exception("The timer should have cancelled the subprocess")


adhesive.bpmn_build("cancel-subprocess.bpmn")
