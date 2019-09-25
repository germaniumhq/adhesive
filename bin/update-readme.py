#!/usr/bin/env python3


import adhesive
from adhesive.workspace import docker


@adhesive.task('Render AsciiDoc to DocBook')
def convert_asciidoc_to_docbook(context):
    with docker.inside(
        context.workspace,
        "bmst/docker-asciidoctor") as dw:
        dw.run("""
            asciidoctor -o wut README.adoc
        """)


@adhesive.task('Convert DocBook to Markdown')
def convert_docbook_to_markdown(context):
    with docker.inside(
        context.workspace,
        "pandoc/core") as dw:
        dw.run("""
            pandoc --from docbook --to markdown_strict README.docbook.xml -o README.md
        """)

@adhesive.task('Convert DocBook to ReStructuredText')
def convert_docbook_to_restructuredtext(context):
    with docker.inside(
        context.workspace,
        "pandoc/core") as dw:
        dw.run("""
            pandoc --from docbook --to rst README.docbook.xml -o README.rst
        """)


@adhesive.task('Remove DocBook documentation')
def remove_docbook_documentation(context):
    context.workspace.run("""
        rm README.docbook.xml
    """)


adhesive.process_start()\
    .task("Render AsciiDoc to DocBook")\
    .branch_start()\
        .task("Convert DocBook to Markdown")\
    .branch_end()\
    .branch_start()\
        .task("Convert DocBook to ReStructuredText")\
    .branch_end()\
    .task("Remove DocBook documentation")\
    .process_end()\
    .build()
