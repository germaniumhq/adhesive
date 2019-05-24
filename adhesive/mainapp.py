import adhesive
from adhesive.config import LocalConfigReader

_globals = globals()
_locals = locals()

# read local configuration.
adhesive.config.current =\
    LocalConfigReader.read_configuration()

def main():
    with open('_adhesive.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content, _globals, _locals)


if __name__ == "__main__":
    main()
