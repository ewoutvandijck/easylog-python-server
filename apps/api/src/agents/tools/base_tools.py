from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseTools(ABC):
    @abstractmethod
    def all_tools(self) -> list[Callable]:
        raise NotImplementedError()
