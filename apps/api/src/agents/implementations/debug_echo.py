import time
from collections.abc import AsyncGenerator

from pydantic import BaseModel, Field

from src.agents.base_agent import BaseAgent
from src.models.messages import Message, TextContent


class DebugEchoConfig(BaseModel):
    debug_interval_ms: int = Field(default=100)
    debug_chunk_size: int = Field(default=10)


class DebugEcho(BaseAgent[DebugEchoConfig]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[TextContent, None]:
        """An agent that streams back the messages it receives in chunks of `debug_chunk_size` characters.

        Args:
            messages (List[Message]): The messages to send to the assistant.
            config (DebugAssistantConfig): The configuration for the assistant.

        Yields:
            Generator[TextContent, None, None]: The streamed response from the assistant.
        """

        last_message = messages[-1]
        for content in last_message.content:
            if content.type != "text":
                continue

            text = content.content
            # Continue yielding chunks until we've processed the entire text
            loc_index = 0
            while loc_index < len(text):
                yield TextContent(
                    content=text[loc_index : loc_index + self.config.debug_chunk_size],
                    type="text",
                )
                loc_index += self.config.debug_chunk_size
                time.sleep(self.config.debug_interval_ms / 1000)
