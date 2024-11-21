from typing import Generator, List

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent


class AnthropicWithPDFConfig(AgentConfig):
    pass


class AnthropicWithPDF(BaseAgent):
    def on_message(
        self, messages: List[Message], config: AnthropicWithPDFConfig
    ) -> Generator[MessageContent, None, None]:
        yield MessageContent(content="Hello, world!!!!")
