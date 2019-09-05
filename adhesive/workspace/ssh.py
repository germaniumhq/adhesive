from typing import Union, Optional, Any, Dict
import shlex
from contextlib import contextmanager
import paramiko
import sys
import os

from .Workspace import Workspace


class SshWorkspace(Workspace):
    def __init__(self,
                 execution_id: str,
                 token_id: str,
                 ssh: str,
                 pwd: Optional[str] = None,
                 **kw: Dict[str, Any]) -> None:
        super(SshWorkspace, self).__init__(
            execution_id=execution_id,
            token_id=token_id,
            pwd='/' if not pwd else pwd)

        # cloning needs to create new connections since tasks are executed
        # in different processes
        self._ssh = ssh
        self._kw = kw

        self.ssh = paramiko.client.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.ssh.connect(ssh, **kw)

        self.sftp = self.ssh.open_sftp()

    def run(self,
            command: str,
            capture_stdout: bool = False) -> Union[str, None]:
        stdin, stdout, stderr = self.ssh.exec_command(f"cd {shlex.quote(self.pwd)};{command}")
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
        self.sftp.chdir(self.pwd)
        with self.sftp.file(file_name, "w") as f:
            f.write(content)

    def rm(self, path: Optional[str]=None) -> None:
        self.run('rm -fr {path}')

    def mkdir(self, path: str = None) -> None:
        self.run('mkdir -p {shlex.quote(path)}')

    def copy_to_agent(self,
                      from_path: str,
                      tdo_path: str):
        raise Exception("not implemented")

    def copy_from_agent(self,
                        from_path: str,
                        to_path: str):
        raise Exception("not implemented")

    def clone(self):
        result = SshWorkspace(self,
                              execution_id=self.execution_id,
                              token_id=self.token_id,
                              ssh=self._ssh,
                              pwd=self.pwd,
                              **self._kw)

        return result

    def _destroy(self) -> None:
        self.sftp.close()
        self.ssh.close()

# TypeError: Can't instantiate abstract class SshWorkspace with abstract methods clone, copy_from_agent, copy_to_agent, mkdir, rm, write_file


@contextmanager
def inside(workspace: Workspace,
           ssh: str,
           **kw: Dict[str, Any]):
    w = None

    try:
        w = SshWorkspace(execution_id=workspace.execution_id,
                         token_id=workspace.token_id,
                         ssh=ssh,
                         **kw)
        yield w
    finally:
        if w is not None:
            w._destroy()

