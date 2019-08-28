from typing import Union, Optional, Any, Dict
from contextlib import contextmanager
import paramiko

from .Workspace import Workspace


class SshWorkspace(Workspace):
    def __init__(self,
                 workspace: Workspace,
                 ssh: Optional[str],
                 **kw: Dict[str, Any]) -> None:
        super(SshWorkspace, self).__init__(
            execution=workspace.execution,
            pwd=workspace.pwd)

        if not ssh:
            return

        self.ssh = paramiko.client.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.ssh.connect(ssh, **kw)

    def run(self,
            command: str,
            capture_stdout: bool = False) -> Union[str, None]:
        stdin, stdout, stderr = self.ssh.exec_command(command)
        print(stdout)

    def write_file(
            self,
            file_name: str,
            content: str) -> None:
        raise Exception("not implemented")

    def rm(self, path: Optional[str]=None) -> None:
        raise Exception("not implemented")

    def mkdir(self, path: str = None) -> None:
        raise Exception("not implemented")

    def copy_to_agent(self,
                      from_path: str,
                      to_path: str):
        raise Exception("not implemented")

    def copy_from_agent(self,
                        from_path: str,
                        to_path: str):
        raise Exception("not implemented")

    def clone(self):
        result = SshWorkspace(self, None)
        result.ssh = self.ssh

    def _destroy(self) -> None:
        self.ssh.close()

# TypeError: Can't instantiate abstract class SshWorkspace with abstract methods clone, copy_from_agent, copy_to_agent, mkdir, rm, write_file


@contextmanager
def inside(workspace: Workspace,
           ssh: str,
           **kw: Dict[str, Any]):
    w = None

    try:
        w = SshWorkspace(workspace=workspace,
                         ssh=ssh,
                         **kw)
        yield w
    finally:
        if w is not None:
            w._destroy()

