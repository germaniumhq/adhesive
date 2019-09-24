from typing import Optional, Any
import yaml
import shlex
import uuid

from adhesive.workspace import Workspace
from adhesive.workspace.kube.YamlDictNavigator import YamlDictNavigator


class KubeApi():
    def __init__(self, workspace: Workspace) -> None:
        self._workspace = workspace

    def get(self,
            *args,
            kind: str,
            name: str,
            namespace: Optional[str] = None) -> Any:
        """
        Gets an object from the kubernetes API
        :param args:
        :param kind:
        :param name:
        :param namespace:
        :return:
        """
        if args:
            raise Exception("You need to use named arguments.")

        command = f"kubectl get {kind} {name} -o yaml"

        if namespace:
            command += f" --namespace={namespace}"

        object_data = self._workspace.run(
            command,
            capture_stdout=True)

        return YamlDictNavigator(yaml.safe_load(object_data))

    def getall(self,
            *args,
            kind: str,
            filter: Optional[str] = None,
            namespace: Optional[str] = None) -> Any:
        """
        Gets an object from the kubernetes API
        :param args:
        :param kind:
        :param name:
        :param namespace:
        :return:
        """
        if args:
            raise Exception("You need to use named arguments.")

        command = f"kubectl get {kind} -o yaml"

        if filter:
            command += f" -l {shlex.quote(filter)}"

        if namespace:
            command += f" --namespace={namespace}"

        object_data = self._workspace.run(
            command,
            capture_stdout=True)

        return list(map(YamlDictNavigator, yaml.safe_load_all(object_data)))

    def exists(self,
               *args,
               kind: str,
               name: str,
               namespace: Optional[str] = None) -> bool:
        """
        Checks if an object exists
        :param args:
        :param kind:
        :param name:
        :param namespace:
        :return:
        """
        if args:
            raise Exception("You need to use named arguments.")

        command = f"kubectl get {kind} {name}"

        if namespace:
            command += f" --namespace={namespace}"

        try:
            self._workspace.run(command)
            return True
        except Exception:
            return False

    def delete(self,
               *args,
               kind: str,
               name: str,
               namespace: Optional[str] = None) -> None:
        """
        Delete an object
        :param args:
        :param kind:
        :param name:
        :param namespace:
        :return:
        """

        if args:
            raise Exception("You need to use named arguments.")

        command = f"kubectl delete {kind} {name}"

        if namespace:
            command += f" --namespace={namespace}"

        self._workspace.run(command)

    def create(self,
               *args,
               kind: str,
               name: str,
               namespace: Optional[str] = None) -> None:
        """
        Delete an object
        :param args:
        :param kind:
        :param name:
        :param namespace:
        :return:
        """

        if args:
            raise Exception("You need to use named arguments.")

        command = f"kubectl create {kind} {name}"

        if namespace:
            command += f" --namespace={namespace}"

        self._workspace.run(command)

    def apply(self,
              content: str,
              namespace: Optional[str] = None) -> None:
        """
        Apply the content
        :param content:
        :return:
        """
        file_name = f"/tmp/{str(uuid.uuid4())}.yml"
        command = f"kubectl apply -f {file_name}"

        if namespace:
            command += f" --namespace {namespace}"

        try:
            self._workspace.write_file(file_name, content)
            self._workspace.run(command)
        finally:
            self._workspace.rm(file_name)
