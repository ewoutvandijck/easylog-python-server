import json
import os
from abc import abstractmethod
from inspect import signature
from typing import Any, Generator, List

from prisma.models import Threads
from pydantic import BaseModel

from src.db.prisma import prisma
from src.logger import logger
from src.models.messages import Message, MessageContent


class AgentConfig(BaseModel):
    pass


class BaseAgent:
    """Base class for all agents."""

    thread_id: str
    _thread: Threads | None = None

    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        logger.info(f"Initialized agent: {self.__class__.__name__}")

    @abstractmethod
    def on_message(
        self, messages: List[Message], config: AgentConfig
    ) -> Generator[MessageContent, None, None]:
        raise NotImplementedError()

    def get_env(self, key: str) -> str:
        """A convenience method to get an environment variable."""

        env = os.getenv(key)

        if env is None:
            raise ValueError(
                f"Environment variable {key} is not found. Make sure .env file exists and {key} is set."
            )

        return env

    def forward(
        self, messages: List[Message], config: dict
    ) -> Generator[MessageContent, None, None]:
        """
        Validate the config and forward the messages to the agent. Returns a generator of message contents.

        Args:
            messages: The messages to forward to the agent.
            config: The config to validate and forward to the agent.

        Returns:
            A generator of messages.
        """

        logger.info(
            f"Forwarding message to agent: {self.__class__.__name__} with config: {config}"
        )

        agent_config = self._get_config_class().model_validate(config)

        return self.on_message(messages, agent_config)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")

        return metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")
        metadata[key] = value

        prisma.threads.update(
            where={"id": self.thread_id}, data={"metadata": json.dumps(metadata)}
        )

    def _get_thread(self) -> Threads:
        """Get the thread for the agent."""

        if self._thread is None:
            self._thread = prisma.threads.find_first_or_raise(
                where={"id": self.thread_id}
            )

        return self._thread

    def _get_config_class(self) -> type[AgentConfig]:
        """
        Get the config class for the agent.

        Returns:
            The config class.
        """

        sig = signature(self.on_message)
        config_param = sig.parameters["config"]
        attr_type = config_param.annotation

        if attr_type is None:
            raise ValueError("Config parameter must have an annotation")

        if not issubclass(attr_type, AgentConfig):
            raise ValueError(
                f"Config parameter must be an instance of {AgentConfig.__name__}"
            )

        return attr_type
