from typing import List, Optional
import copy


# FIXME: move this to its own library: YamlDict seems a good name
from adhesive.workspace.kube.YamlDictNavigator import YamlDictNavigator
from adhesive.workspace.kube.YamlNavigator import YamlNavigator


class YamlListNavigator(YamlNavigator):
    """
    A property navigator that allows accessing a list and
    correctly wraps potentially nested dictionaries.
    """
    def __init__(self,
                 content: Optional[List]=None):
        self.__content = content if content is not None else list()

    def __deepcopy__(self, memodict={}):
        return YamlListNavigator(copy.deepcopy(self.__content))

    def __getitem__(self, item):
        result = self.__content[item]

        if isinstance(result, dict):
            return YamlDictNavigator(result)

        if isinstance(result, list):
            return YamlListNavigator(result)

        return result

    def __setitem__(self, key, value):
        if isinstance(value, YamlNavigator):
            value = value._raw

        self.__content[key] = value

    def __delitem__(self, key):
        self.__content.__delitem__(key)

    def __iter__(self):
        return self.__content.__iter__()

    def __len__(self) -> int:
        return len(self.__content)

    @property
    def _raw(self) -> List:
        """
        Get access to the underlying collection.
        :return:
        """
        return self.__content
