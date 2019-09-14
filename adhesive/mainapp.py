_globals = globals()
_locals = locals()

import logging


def __main():
    """
    The main adhesive program.
    """

    # we import everything locally so we don't pollute the globals
    import adhesive
    from adhesive.config import LocalConfigReader
    from adhesive.logging import configure_logging
    import sys

    # read local configuration.
    adhesive.config.current = \
        LocalConfigReader.read_configuration()

    configure_logging(adhesive.config.current)

    for plugin_path in adhesive.config.current.plugins:
        sys.path.append(plugin_path)

    with open('_adhesive.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content, _globals, _locals)


if __name__ == "__main__":
    __main()

