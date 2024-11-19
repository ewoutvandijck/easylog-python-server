from abc import abstractmethod
from typing import Generator, List

from pydantic import BaseModel

from src.logging import logger
from src.models.messages import Message, MessageContent


class AgentConfig(BaseModel):
    pass


class BaseAgent:
    def __init__(self):
        logger.info(f"Initialized agent: {self.__class__.__name__}")

    @abstractmethod
    def on_message(
        self, messages: List[Message], config: AgentConfig
    ) -> Generator[MessageContent, None, None]:
        raise NotImplementedError()

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

    def _get_config_class(self) -> type[AgentConfig]:
        """
        Get the config class for the agent.

        Returns:
            The config class.
        """

        from inspect import signature

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
