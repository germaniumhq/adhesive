from typing import Dict, Optional
import copy


# FIXME: move this to its own library: YamlDict seems a good name


class YamlDictNavigator:
    """
    A property navigator that allows accessing a dictionary via
    properties.
    """
    def __init__(self,
                 content: Optional[Dict]=None):
        self.__content = content if content is not None else dict()

    def __deepcopy__(self, memodict={}):
        return YamlDictNavigator(copy.deepcopy(self.__content))

    def __getattr__(self, item):
        if item == '_YamlDictNavigator__content':
            return self.__content

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
        if isinstance(value, YamlDictNavigator):
            value = value.__content
        elif isinstance(value, YamlListNavigator):
            value = value.__content

        if "_YamlDictNavigator__content" == key:
            super(YamlDictNavigator, self).__setattr__(key, value)
            return

        self.__content[key] = value

    def __setitem__(self, key, value):
        if isinstance(value, YamlDictNavigator):
            self.__content[key] = value.__content
            return

        self.__content[key] = value

    def __iter__(self):
        return self.__content.__iter__()

    def _items(self):
        return self.__content.items()

    def _raw(self):
        """
        Get access to the underlying collection.
        :return:
        """
        return self.__content


from adhesive.workspace.kube.YamlListNavigator import YamlListNavigator