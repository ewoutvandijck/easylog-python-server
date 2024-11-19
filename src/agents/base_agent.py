from abc import abstractmethod
from typing import Generator

from pydantic import BaseModel

from src.logging import logger
from src.models.messages import MessageContent


class AgentConfig(BaseModel):
    pass


class BaseAgent:
    def __init__(self):
        logger.info(f"Initialized agent: {self.__class__.__name__}")

    def forward(
        self, input: str, config: dict
    ) -> Generator[MessageContent, None, None]:
        logger.info(
            f"Forwarding message to agent: {self.__class__.__name__} with config: {config}"
        )
        agent_config = self._get_config_class().model_validate(config)
        return self.on_message(input, agent_config)

    def _get_config_class(self) -> type[AgentConfig]:
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

    @abstractmethod
    def on_message(
        self, input: str, config: AgentConfig
    ) -> Generator[MessageContent, None, None]:
        raise NotImplementedError()
