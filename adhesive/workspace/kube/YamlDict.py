from typing import Dict, Optional
import copy


# FIXME: move this to its own library: YamlDict seems a good name
from adhesive.workspace.kube.YamlNavigator import YamlNavigator
from adhesive.workspace.kube.YamlMissing import YamlMissing


class YamlDict(YamlNavigator):
    """
    A property navigator that allows accessing a dictionary via
    properties.
    """
    def __init__(self,
                 *args,
                 content: Optional[Dict]=None,
                 property_name: Optional[str]=""):
        if args:
            raise Exception("You need to pass the named arguments")

        super(YamlDict, self).__init__()

        self.__content = content if content is not None else dict()
        self.__property_name = property_name

    def __deepcopy__(self, memodict={}):
        return YamlDict(
            property_name=self.__property_name,
            content=copy.deepcopy(self._raw))

    def __getattr__(self, item):
        if item == '_YamlDict__content':
            return self.__content

        if item == '_YamlDict__property_name':
            return self.__property_name

        if item not in self.__content:
            return YamlMissing(
                property_name=f"{self.__property_name}.{item}")

        result = self.__content[item]

        if isinstance(result, dict):
            return YamlDict(
                property_name=f"{self.__property_name}.{item}",
                content=result)
        elif isinstance(result, list):
            return YamlList(
                property_name=f"{self.__property_name}.{item}",
                content=result)

        return result

    def __getitem__(self, item):
        result = self.__content[item]

        if isinstance(result, dict):
            return YamlDict(
                property_name=f"{self.__property_name}.[{item}]",
                content=result)
        elif isinstance(result, list):
            return YamlList(
                property_name=f"{self.__property_name}.[{item}]",
                content=result)

        return result

    def __setattr__(self, key, value):
        if isinstance(value, YamlNavigator):
            value = value._raw

        if "_YamlDict__content" == key:
            super(YamlDict, self).__setattr__(key, value)
            return

        if "_YamlDict__property_name" == key:
            super(YamlDict, self).__setattr__(key, value)
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
        return YamlIteratorWrapper(
            iter=self.__content.__iter__(),
            property_name=self.__property_name,
        )

    def __len__(self) -> int:
        return len(self.__content)

    def _items(self):
        return YamlDictWrapper(
            items_view=self.__content.items(),
            property_name=self.__property_name,
        )

    @property
    def _raw(self) -> Dict:
        """
        Gets access to the underlying collection.
        :return:
        """
        return self.__content

    def __repr__(self) -> str:
        return f"YamlDict({self.__property_name}) {self.__content}"


from adhesive.workspace.kube.YamlList import YamlList
from adhesive.workspace.kube.YamlIteratorWrapper import YamlIteratorWrapper, YamlDictWrapper
