from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseTools(ABC):
    @abstractmethod
    def all_tools(self) -> list[Callable]:
        raise NotImplementedError()

    @classmethod
    def tool_noop(cls) -> None:
        """You can use this tool to explicitly do nothing. This is useful when you got the instruction to not do anything."""

        return None

    @classmethod
    def tool_call_super_agent(cls) -> None:
        """You can use this tool to call the super agent. This is useful when you got the instruction to call the super agent."""

        return None
