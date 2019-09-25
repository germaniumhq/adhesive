#!/usr/bin/env python3


import adhesive
import os
from adhesive.workspace import docker


@adhesive.lane('local')
def lane_default(context):
    context.workspace.pwd = os.getcwd()
    yield context.workspace


@adhesive.task('Render AsciiDoc to DocBook')
def convert_asciidoc_to_docbook(context):
    with docker.inside(
        context.workspace,
        "bmst/docker-asciidoctor") as dw:
        dw.run("""
            asciidoctor -b docbook -o README.docbook.xml README.adoc
        """)


@adhesive.task('Render AsciiDoc to PDF')
def convert_asciidoc_to_docbook(context):
    with docker.inside(
        context.workspace,
        "bmst/docker-asciidoctor") as dw:
        dw.run("""
            asciidoctor-pdf -o README.pdf README.adoc
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
    .sub_process_start("Render Documents", lane="local")\
        .branch_start()\
            .task("Render AsciiDoc to DocBook", lane="local")\
        .branch_end()\
        .branch_start()\
            .task("Render AsciiDoc to PDF", lane="local")\
        .branch_end()\
    .sub_process_end()\
    .sub_process_start("Convert Documents", lane="local")\
        .branch_start()\
            .task("Convert DocBook to Markdown", lane="local")\
        .branch_end()\
        .branch_start()\
            .task("Convert DocBook to ReStructuredText", lane="local")\
        .branch_end()\
    .sub_process_end()\
    .task("Remove DocBook documentation", lane="local")\
    .process_end()\
    .build()
