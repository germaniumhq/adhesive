from adhesive.graph import Workflow


def write_dot_file(file_name: str,
                   workflow: Workflow) -> None:
    with open(file_name, "wt") as f:
        f.write("digraph {\n")

        for task_id, task in workflow.tasks.items():
            f.write(f"{getid(task_id)} [label=\"{task.name}\"];\n")

        for edge_id, edge in workflow.edges.items():
            f.write(f"{getid(edge.source_id)} -> {getid(edge.target_id)};\n")

        f.write("}\n")


def getid(id: str) -> str:
    return "n" + id.replace('-', '')