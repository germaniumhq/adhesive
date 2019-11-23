import abc

from adhesive.graph.BoundaryEvent import BoundaryEvent


class TimerBoundaryEvent(BoundaryEvent, metaclass=abc.ABCMeta):
    """
    A base class for all the timer boundary events
    """
    @abc.abstractmethod
    def total_seconds(self) -> int: ...
