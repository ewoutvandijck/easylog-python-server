import asyncio
import json
from typing import AsyncGenerator, Callable, List

from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent

from src.agents.base_agent import AgentConfig, BaseAgent
from src.logger import logger
from src.models.messages import Message, MessageContent


class AnthropicAgent(BaseAgent):
    # Anthropic client instance for making API calls
    client: AsyncAnthropic
    pdfs: list[str] = []

    def __init__(self, *args, **kwargs):
        # Initialize parent BaseAgent class
        super().__init__(*args, **kwargs)

        # Initialize Anthropic client with API key from environment
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    async def handle_stream(
        self,
        stream: AsyncStream[RawMessageStreamEvent],
        messages: List[Message],
        agent_config: AgentConfig,
        tools: list[Callable] = [],
    ) -> AsyncGenerator[MessageContent, None]:
        current_index = 0
        blocks: list[tuple[str, str]] = []

        async for event in stream:
            logger.info(event)
            if (
                event.type == "content_block_start"
                and event.content_block.type == "text"
            ):
                blocks.append(("text", event.content_block.text))
            elif (
                event.type == "content_block_start"
                and event.content_block.type == "tool_use"
            ):
                blocks.append((event.content_block.name, ""))
            elif event.type == "content_block_stop":
                current_index += 1
            elif (
                event.type == "content_block_delta" and event.delta.type == "text_delta"
            ):
                blocks[current_index] = (
                    blocks[current_index][0],
                    blocks[current_index][1] + event.delta.text,
                )
                yield MessageContent(content=event.delta.text, index=current_index)
            elif (
                event.type == "content_block_delta"
                and event.delta.type == "input_json_delta"
            ):
                blocks[current_index] = (
                    blocks[current_index][0],
                    blocks[current_index][1] + event.delta.partial_json,
                )
            elif (
                event.type == "message_delta" and event.delta.stop_reason == "tool_use"
            ):
                function_name, json_str = blocks[current_index - 1]
                function = next(
                    (tool for tool in tools if tool.__name__ == function_name), None
                )

                if function is None:
                    raise ValueError(f"Function {function_name} not found")

                kwargs = json.loads(json_str or "{}")

                function_result = (
                    await function(**kwargs)
                    if asyncio.iscoroutinefunction(function)
                    else function(**kwargs)
                )

                logger.info(f"Function result: {function_result}")

                new_messages = messages.copy()
                new_messages.append(
                    Message(
                        role="user",
                        content=[MessageContent(content=str(function_result))],
                    )
                )

                async for content in self.on_message(new_messages, agent_config):
                    yield content
