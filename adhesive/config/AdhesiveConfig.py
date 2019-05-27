import abc
import os
from typing import Any, List


class AdhesiveConfig:
    def __init__(self):
        pass

    @abc.abstractmethod
    def __getattr__(self, item) -> Any:
        pass

    @abc.abstractmethod
    def secret_locations(self) -> List[str]:
        return [
            os.path.join(".", ".adhesive", "secrets"),
            os.path.join(os.environ.get("HOME", "."), ".adhesive", "secrets"),
        ]
