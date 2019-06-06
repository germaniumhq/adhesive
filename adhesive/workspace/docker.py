import os
import shlex
import subprocess
import sys
from contextlib import contextmanager
from typing import Optional, Union, Iterable
from uuid import uuid4

from adhesive.storage.ensure_folder import ensure_folder
from .Workspace import Workspace


class DockerWorkspace(Workspace):
    def __init__(self,
                 workspace: Workspace,
                 image_name: str,
                 extra_docker_params: str = "") -> None:
        super(DockerWorkspace, self).__init__(
            execution=workspace.execution,
            pwd=workspace.pwd)

        pwd = workspace.pwd
        uid = os.getuid()
        gid = os.getgid()
        groups = os.getgroups()

        if groups:
            groups_str = ""
            for group in groups:
                groups_str += f"--group-add {group} "
        else:
            groups_str = ""

        self.container_id = workspace.run(
            f"docker run -t "
            f"-v {pwd}:{pwd} "
            f"-d "
            f"--entrypoint cat "
            f"-u {uid}:{gid} "
            f"{groups_str} "
            f"{extra_docker_params} "
            f"{shlex.quote(image_name)}",
            capture_stdout=True
        ).strip()

    def run(self,
            command: str,
            capture_stdout: bool = False) -> Union[str, None]:
        if capture_stdout:
            return subprocess.check_output(
                [
                    "docker", "exec",
                    "-w", self.pwd,
                    self.container_id,
                    "/bin/sh", "-c",
                    command
                ],
                cwd=self.pwd,
                stderr=sys.stderr).decode('utf-8')

        subprocess.check_call(
            [
                "docker", "exec",
                          "-w", self.pwd,
                          self.container_id,
                          "/bin/sh", "-c",
                          command
            ],
            cwd=self.pwd,
            stdout=sys.stdout,
            stderr=sys.stderr)

    def write_file(
            self,
            file_name: str,
            content: str) -> None:
        """
        Write a file on the remote docker instance. Since we can't
        really just write files, we create a temp file, then we
        copy it remotely.
        :param file_name:
        :param content:
        :return:
        """
        try:
            tmp_folder = ensure_folder("tmp")
            tmp_file = os.path.join(tmp_folder, str(uuid4()))
            with open(tmp_file, "wt") as f:
                f.write(content)
            self.copy_to_agent(tmp_file, file_name)
        finally:
            os.remove(tmp_file)

    def rm(self, path: Optional[str]=None) -> None:
        """
        Remove a path from the container. We're calling `rm` to do
        the actual operation.
        :param path:
        :return:
        """
        if not path:
            raise Exception("You need to pass a subpath for deletion")

        self.run(f"rm -fr {shlex.quote(path)}")

    def mkdir(self, path: str = None) -> None:
        full_path = os.path.join(self.pwd, path)
        self.run(f"mkdir -p {shlex.quote(full_path)}")

    def copy_to_agent(self,
                      from_path: str,
                      to_path: str):
        subprocess.check_call(
            [
                "docker", "cp", from_path, f"{self.container_id}:{to_path}"
            ],
            stdout=sys.stdout,
            stderr=sys.stderr)

    def copy_from_agent(self,
                        from_path: str,
                        to_path: str):
        subprocess.check_call(
            [
                "docker", "cp", f"{self.container_id}:{from_path}", to_path
            ],
            stdout=sys.stdout,
            stderr=sys.stderr)

    def _destroy(self):
        subprocess.check_call(
            [
                "docker", "rm", "-f", self.container_id
            ],
            stdout=sys.stdout,
            stderr=sys.stderr)


@contextmanager
def inside(workspace: Workspace,
           image_name: str,
           extra_docker_params: str = ""):
    w = None

    try:
        w = DockerWorkspace(workspace=workspace,
                            image_name=image_name,
                            extra_docker_params=extra_docker_params)
        yield w
    finally:
        if w is not None:
            w._destroy()


@contextmanager
def build(workspace: Workspace,
          tags: Union[str, Iterable[str]]) -> str:

    # we always consider a list of tags
    if isinstance(tags, str):
        tags = [tags]

    command = "docker build "

    for tag in tags:
        command += f"-t {tag} -q "

    command += "."

    return workspace.run(command)
