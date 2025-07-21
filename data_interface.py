from abc import ABC, abstractmethod


class IData(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass