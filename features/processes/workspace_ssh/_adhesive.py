import adhesive
from adhesive.workspace import ssh


@adhesive.task('Start\ SSH\ Server')
def start_ssh_server(context):
    print("starting server...")
    container_id = context.workspace.run(
        "docker run -d -p 8022:22 rastasheep/ubuntu-sshd:18.04",
        capture_stdout=True)

    context.data.container_id = container_id
    print("[OK] started server")

@adhesive.task('Test running commands on ssh connections')
def run_ls_inside_server(context):
    with ssh.inside(context.workspace,
            "localhost",
            username="root",
            password="root",
            port=8022) as w:
        # we test the stderr writing
        w.run("echo text; echo error >&2")  # we write on stderr on purpose

        # we test the capture stdout
        ls_result = w.run("ls -la", capture_stdout=True)

        # we test the non-zero error codes
        got_error = True

        try:
            w.run("false")
            got_error = False
        except Exception as e:
            pass

        if not got_error:
            raise Exception("non zero error code didn't raised exception")

        print(ls_result)


@adhesive.task('Shutdown\ Server')
def shutdown_server(context):
    print("shutting down server...")
    context.workspace.run(f"docker rm -f {context.data.container_id}")
    print("[OK] server was shutdown")


@adhesive.task('Test\ Failed')
def test_failed(context):
    print(context.data.as_dict())
    context.data.test_failed = True



@adhesive.task('Check\ if\ test\ failed')
def check_if_test_failed(context):
    if context.data._error:
        print("Uh oh, we got an error in the ssh execution")
        print(context.data._error)

    assert not context.data.test_failed


adhesive.bpmn_build("ssh.bpmn")