from behave import step, use_step_matcher
import subprocess
import os


use_step_matcher("re")


@step("I run adhesive on a workflow with a UT with a single checkbox")
def run_the_workflow_with_a_single_checkbox(contxt):
    subprocess.check_call(["python", "-m", "adhesive.mainapp"],
                          cwd=f"{os.getcwd()}/features/processes/single_checkbox")


@step("the user task renders just fine")
def noop(context):
    pass
