_globals = globals()
_locals = locals()


import click


@click.group(invoke_without_command=True)
@click.pass_context
def __main(ctx):
    if ctx.invoked_subcommand is None:
        __adhesive_build()


@__main.command('verify')
def verify():
    """
    Validate if the BPMN and step definitions are matching
    """
    import adhesive
    adhesive.config.current.verify_mode = True

    __run_the_process_executor()


@__main.command('build')
def __adhesive_build():
    """
    Run the _adhesive.py script
    """
    __run_the_process_executor()


def __run_the_process_executor():
    # we import everything locally so we don't pollute the globals
    import adhesive
    from adhesive.logging import configure_logging
    import sys

    # configure the logging
    configure_logging(adhesive.config.current)

    for plugin_path in adhesive.config.current.plugins:
        sys.path.append(plugin_path)

    with open('_adhesive.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content, _globals, _locals)


if __name__ == "__main__":
    __main()
