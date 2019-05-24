import os
import subprocess

from behave import step, use_step_matcher

use_step_matcher("re")


@step("I run adhesive on a workflow with a UT with a single checkbox")
def run_the_workflow_with_a_single_checkbox(contxt):
    subprocess.check_call(["python", "-m", "adhesive.mainapp"],
                          cwd=f"{os.getcwd()}/features/processes/single_checkbox")


@step("I run adhesive on '(.*?)'")
def run_an_adhesive_workflow(context, folder):
    pipes = subprocess.Popen(
        ["python", f"features/{folder}/_adhesive.py"],
        cwd=f"{os.getcwd()}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = pipes.communicate()
    context.pipes = pipes

    context.process_return_code = pipes.returncode
    context.process_stdout = stdout.decode("utf-8")
    context.process_stderr = stderr.decode("utf-8")


@step("the adhesive process has failed")
def run_the_workflow_with_a_single_checkbox(context):
    assert context.process_return_code != 0


@step("there is in the (.*?) the text '(.*?)'")
def check_the_text_in_stdouterr(context, where, searched_text):
    if where == "stdout":
        print("STDOUT")
        print(context.process_stdout)
        assert searched_text in context.process_stdout
    else:
        print("STDERR")
        print(context.process_stderr)
        assert searched_text in context.process_stderr


@step("the user task renders just fine")
def noop(context):
    pass
