from typing import Dict, Optional
import copy


# FIXME: move this to its own library: YamlDict seems a good name
from adhesive.workspace.kube.YamlNavigator import YamlNavigator
from adhesive.workspace.kube.YamlNoopNavigator import YamlNoopNavigator


class YamlDictNavigator(YamlNavigator):
    """
    A property navigator that allows accessing a dictionary via
    properties.
    """
    def __init__(self,
                 content: Optional[Dict]=None,
                 *args,
                 property_name: Optional[str]=""):
        if args:
            raise Exception("You need to pass the named arguments")

        super(YamlDictNavigator, self).__init__()

        self.__content = content if content is not None else dict()
        self.__property_name = property_name

    def __deepcopy__(self, memodict={}):
        return YamlDictNavigator(
            property_name=self.__property_name,
            content=copy.deepcopy(self._raw))

    def __getattr__(self, item):
        if item == '_YamlDictNavigator__content':
            return self.__content

        if item == '_YamlDictNavigator__property_name':
            return self.__property_name

        if item not in self.__content:
            return YamlNoopNavigator(
                property_name=f"{self.__property_name}.{item}")

        result = self.__content[item]

        if isinstance(result, dict):
            return YamlDictNavigator(result)
        elif isinstance(result, list):
            return YamlListNavigator(result)

        return result

    def __getitem__(self, item):
        result = self.__content[item]

        if isinstance(result, dict):
            return YamlDictNavigator(result)
        elif isinstance(result, list):
            return YamlListNavigator(result)

        return result

    def __setattr__(self, key, value):
        if isinstance(value, YamlNavigator):
            value = value._raw

        if "_YamlDictNavigator__content" == key:
            super(YamlDictNavigator, self).__setattr__(key, value)
            return

        if "_YamlDictNavigator__property_name" == key:
            super(YamlDictNavigator, self).__setattr__(key, value)
            return

        self.__content[key] = value

    def __setitem__(self, key, value):
        if isinstance(value, YamlNavigator):
            self.__content[key] = value._raw
            return

        self.__content[key] = value

    def __delattr__(self, item):
        self.__content.__delitem__(item)

    def __delitem__(self, key):
        self.__content.__delitem__(key)

    def __iter__(self):
        return self.__content.__iter__()

    def __len__(self) -> int:
        return len(self.__content)

    def _items(self):
        return self.__content.items()

    @property
    def _raw(self) -> Dict:
        """
        Gets access to the underlying collection.
        :return:
        """
        return self.__content

    def __repr__(self) -> str:
        return f"YamlDictNavigator({self.__property_name}) {self.__content}"


from adhesive.workspace.kube.YamlListNavigator import YamlListNavigator