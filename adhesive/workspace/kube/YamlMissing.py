from typing import Any
from adhesive.workspace.kube.YamlNavigator import YamlNavigator


class YamlMissing(YamlNavigator):
    EMPTY_LIST = list()

    def __init__(self,
                 *args,
                 property_name: str):
        if args:
            raise Exception("You need to pass named arguments")

        super(YamlMissing, self).__init__()

        self.__property_name = property_name

    def __getattr__(self, item):
        # If we get calls for other attributes, we just return none
        return YamlMissing(property_name=f"{self.__property_name}.{item}")

    def _raw(self) -> Any:
        return None

    def __len__(self):
        return 0

    def __iter__(self):
        return YamlMissing.EMPTY_LIST.__iter__()

    def __repr__(self):
        return f"YamlMissing({self.__property_name})"

    def __deepcopy__(self, memodict={}):
        return YamlMissing(property_name=self.__property_name)