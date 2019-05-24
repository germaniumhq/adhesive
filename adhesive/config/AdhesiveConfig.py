import abc
from typing import Any


class AdhesiveConfig:
    def __init__(self):
        pass

    @abc.abstractmethod
    def __getattr__(self, item) -> Any:
        pass
