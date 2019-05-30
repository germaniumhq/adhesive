import adhesive
from adhesive.config import LocalConfigReader
import sys

_globals = globals()
_locals = locals()


def __main():
    # read local configuration.
    adhesive.config.current = \
        LocalConfigReader.read_configuration()

    for plugin_path in adhesive.config.current.plugins:
        sys.path.append(plugin_path)

    with open('_adhesive.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content, _globals, _locals)


if __name__ == "__main__":
    __main()
