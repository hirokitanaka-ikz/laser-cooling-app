from abc import ABC, abstractmethod


class IData(ABC):
    @property
    @abstractmethod
    def timestamp(self) -> str:
        """
        All data classes must have a timestamp as an instance property.
        """
        pass


    @abstractmethod
    def to_dict(self) -> dict:
        pass