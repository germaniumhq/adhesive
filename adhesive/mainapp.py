import os
import subprocess
import sys

import click
import adhesive
import adhesive.version


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", help="Show the current version", is_flag=True)
def __main(ctx, version):
    if ctx.invoked_subcommand is not None:
        return

    if version:
        print(f"Adhesive {adhesive.version.current}")
        sys.exit(0)

    __adhesive_build()


@__main.command("verify")
def verify():
    """
    Validate if the BPMN and step definitions are matching
    """
    import adhesive

    adhesive.config.current.verify_mode = True

    __run_the_process_executor()


@__main.command("build")
def __adhesive_build():
    """
    Run the _adhesive.py script
    """
    __run_the_process_executor()


def __run_the_process_executor():
    # FIXME: loading the full adhesive just to fetch the current plugins is
    #        excessive. Loading of libraries such as ncurses and co should
    #        only happen on execution.
    for plugin_path in adhesive.config.current.plugins:
        sys.path.append(plugin_path)

    # We just extend the environment, then call the same python against
    # the adhesive script.
    os.environ["PYTHONPATH"] = os.path.pathsep.join(sys.path)

    # We pass the verify mode
    if adhesive.config.current.verify_mode:
        os.environ["ADHESIVE_VERIFY_MODE"] = "true"

    # we call it using a subprocess, since if we load the code using
    # `eval` in the current script, the `inspect` module isn't returning
    # the source code anymore for the functions, so bye-bye caching.
    # If we do an import to the `_adhesive` module, Pebble messes up
    # and never invokes the code anymore.
    try:
        subprocess.check_call([sys.executable, "_adhesive.py"])
    except Exception as e:
        sys.exit(e.returncode)


if __name__ == "__main__":
    __main()
