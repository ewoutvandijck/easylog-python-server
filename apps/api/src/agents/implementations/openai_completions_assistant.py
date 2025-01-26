from typing import AsyncGenerator, List, Literal

from openai import AsyncStream
from openai.types.chat_model import ChatModel
from pydantic import BaseModel, Field
from src.agents.openai_agent import OpenAIAgent
from src.models.messages import Message, TextContent


class OpenAICompletionsAssistantConfig(BaseModel):
    model: ChatModel = Field(default="o1")
    system_message: str | None = Field(default=None)
    temperature: float | None = Field(default=None)
    top_p: float | None = Field(default=None)
    max_tokens: int | None = Field(default=None)
    reasoning_effort: Literal["low", "medium", "high"] = Field(default="medium")


class OpenAICompletionsAssistant(OpenAIAgent[OpenAICompletionsAssistantConfig]):
    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        """An agent that uses OpenAI's simpler chat completions API to generate responses.
        Unlike the full Assistants API, this uses a more straightforward approach
        where messages are sent directly to the model without persistent threads
        or assistant configurations.

        Note: When using GPT o1, you must set stream=False in the config for the
        model to work properly..

        Args:
            messages (List[Message]): All messages in the conversation, including the new one.

        Yields:
            Generator[TextContent, None, None]: Streams back the AI's response piece by piece.
        """

        # This implementation is simpler than the full Assistants API because:
        # 1. It doesn't need to create or manage assistants
        # 2. It doesn't maintain conversation threads
        # 3. It sends messages directly to the model for immediate responses

        # Convert the messages to OpenAI's format and add a system message if configured
        # The system message helps set the tone and behavior of the AI assistant
        _messages = self._convert_messages_to_openai_messages(messages)
        if self.config.system_message:
            _messages.insert(
                0, {"role": "developer", "content": self.config.system_message}
            )

        # We take all the messages in the conversation and convert them to
        # OpenAI's expected format (this handles things like roles and content properly)
        self.logger.info("Sending messages directly to OpenAI for completion")
        stream_or_completion = await self.client.chat.completions.create(
            # Use the configuration settings (model, temperature, etc.)
            # that were specified when this assistant was created (excluding the system message)
            **self.config.model_dump(exclude={"system_message"}, exclude_none=True),
            messages=_messages,
            response_format={"type": "text"},
        )

        if isinstance(stream_or_completion, AsyncStream):
            async for message in self.handle_completions_stream(stream_or_completion):
                yield message
        else:
            yield TextContent(
                content=stream_or_completion.choices[0].message.content,
                type="text",
            )
