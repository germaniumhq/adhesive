from typing import Union, Optional, Any, Dict
from contextlib import contextmanager
import paramiko
import sys
import os

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
        channel = stdout.channel

        if capture_stdout:
            result = bytes()

            while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
                while channel.recv_ready():
                    result += channel.recv(1024)

                while channel.recv_stderr_ready():
                    os.write(sys.stderr.fileno(), channel.recv_stderr(1024))

            exit_status = channel.recv_exit_status()

            if exit_status != 0:
                raise Exception(f"Exit status is not zero, instead is {exit_status}")

            return result.decode('utf-8')

        while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
            while channel.recv_ready():
                os.write(sys.stdout.fileno(), channel.recv(1024))

            while channel.recv_stderr_ready():
                os.write(sys.stderr.fileno(), channel.recv_stderr(1024))

        exit_status = channel.recv_exit_status()

        if exit_status != 0:
            raise Exception(f"Exit status is not zero, instead is {exit_status}")



    def write_file(
            self,
            file_name: str,
            content: str) -> None:
        pass
        #raise Exception("not implemented")

    def rm(self, path: Optional[str]=None) -> None:
        raise Exception("not implemented")

    def mkdir(self, path: str = None) -> None:
        raise Exception("not implemented")

    def copy_to_agent(self,
                      from_path: str,
                      tdo_path: str):
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

