from typing import Optional, Any, TypeVar
import abc

T = TypeVar('T')


class YamlNavigator:
    @abc.abstractproperty
    def _raw(self) -> T:
        """
        Gets access to the underlying collection.
        :return: 
        """
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        pass
