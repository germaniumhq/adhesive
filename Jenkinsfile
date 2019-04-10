germaniumPyExePipeline(
    name: "adhesive",
    runFlake8: false,

    binaries: [
        "Win 32": [
            platform: "python:3.6-win32",
            prefix: "/_gbs/win32/",
            exe: "/src/dist/adhesive.exe",
            dockerTag: "germaniumhq/adhesive:win32",
        ],
        "Lin 64": [
            platform: "python:3.6",
            prefix: "/_gbs/lin64/",
            exe: "/src/dist/adhesive",
            dockerTag: "germaniumhq/adhesive:lin64",
        ]
    ]
)

