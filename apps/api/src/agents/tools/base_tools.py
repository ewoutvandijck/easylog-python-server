from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseTools(ABC):
    @abstractmethod
    def all_tools(self) -> list[Callable]:
        raise NotImplementedError()

    @classmethod
    def tool_noop(cls) -> str:
        """You can use this tool to explicitly do nothing. This is useful when you got the instruction to not do anything.

        Returns:
            str: "[noop]"
        """

        return "[noop]"
