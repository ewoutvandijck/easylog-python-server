from collections.abc import Callable, Iterable

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel

from src.agents.base_agent import BaseAgent


class DebugAgentConfig(BaseModel):
    pass


class DebugAgent(BaseAgent[DebugAgentConfig]):
    async def tools(self) -> list[Callable]:
        return []

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> AsyncStream[ChatCompletionChunk] | ChatCompletion:
        response = await self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[ChatCompletionMessage(role="assistant", content="Hello, world!")],
            stream=True,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "test",
                        "description": "Test tool",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "minLength": 4096},
                            },
                            "required": ["name"],
                        },
                    },
                }
            ],
        )

        return response
