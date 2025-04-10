from collections.abc import Callable, Iterable

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel

from src.agents.base_agent import BaseAgent


class DebugAgentConfig(BaseModel):
    pass


class DebugAgent(BaseAgent[DebugAgentConfig]):
    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        def test(name: str) -> str:
            return f"Hello, {name}!"

        response = await self.client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            stream=False,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "test",
                        "description": "Test tool",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                }
            ],
        )

        return response, [test]
