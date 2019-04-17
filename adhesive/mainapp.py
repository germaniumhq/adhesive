def main():
    with open('_build.py', 'r', encoding='utf-8') as f:
        content = f.read()

    exec(content)


if __name__ == '__main__':
    main()
