from typing import Any
from adhesive.workspace.kube.YamlNavigator import YamlNavigator


class YamlNoopNavigator(YamlNavigator):
    EMPTY_LIST = list()

    def __init__(self):
        super(YamlNoopNavigator, self).__init__()

    def __getattr__(self, item):
        # If we get calls for other attributes, we just return none
        return YamlNoopNavigator()

    def _raw(self) -> Any:
        return None

    def __len__(self):
        return 0

    def __iter__(self):
        return YamlNoopNavigator.EMPTY_LIST.__iter__()
