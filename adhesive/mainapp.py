_globals = globals()
_locals = locals()


def main():
    with open('_adhesive.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content, _globals, _locals)
