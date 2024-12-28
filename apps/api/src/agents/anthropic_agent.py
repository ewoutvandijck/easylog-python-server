import asyncio
import json
from typing import AsyncGenerator, Callable, Generic, List

from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.message_param import MessageParam
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent

from src.agents.base_agent import BaseAgent, TConfig
from src.models.messages import (
    Message,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)


class AnthropicAgent(BaseAgent[TConfig], Generic[TConfig]):
    """
    A base class for creating AI agents that use Anthropic's Claude model.
    Think of this as the foundation for building specialized AI assistants.

    This agent can:
    1. Connect to Anthropic's API (like establishing a phone line to Claude)
    2. Send messages and receive responses
    3. Use special tools when needed to get extra information
    4. Handle responses that come in pieces (streaming)

    Example usage:
        agent = AnthropicAgent()
        response = await agent.on_message(["How can I help?"])
    """

    # Store the connection to Anthropic's API
    client: AsyncAnthropic
    # Keep track of any PDF documents we're working with
    pdfs: list[str] = []

    def __init__(self, *args, **kwargs):
        """
        Sets up the agent with necessary connections and settings.

        This is like preparing a workstation:
        1. Set up basic tools (from BaseAgent)
        2. Establish connection to Claude (Anthropic's API)
        """
        # Initialize the basic agent features
        super().__init__(*args, **kwargs)

        # Create a connection to Anthropic using our API key
        # This is like logging into a special service
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    async def handle_stream(
        self,
        stream: AsyncStream[RawMessageStreamEvent],
        messages: List[Message],
        tools: list[Callable] = [],
        content_index: int = 0,
    ) -> AsyncGenerator[TextContent, None]:
        """
        Processes Claude's response as it comes in, piece by piece.
        This is like having a conversation where someone is thinking out loud
        and you're writing down each part as they say it.

        Example flow:
        1. Claude starts responding
        2. We receive each piece of the response
        3. If Claude needs to use a tool, we pause, use the tool, and continue
        4. We send each piece of the response back as it arrives

        Args:
            stream: The incoming response from Claude
            messages: Previous messages in the conversation
            agent_config: Settings for how the agent should behave
            tools: Special functions Claude can use to get more information

        Returns:
            Parts of Claude's response as they become available
        """
        # Keep track of which part of the response we're processing
        current_index = content_index

        # Store different parts of the response (text, tool use, etc.)
        message_contents: list[TextContent | ToolUseContent] = []

        # Keep track of any partial JSON we need to build up
        partial_json = ""

        # Process each piece of Claude's response as it arrives
        async for event in stream:
            # When Claude starts a new text block
            if (
                event.type == "content_block_start"
                and event.content_block.type == "text"
            ):
                message_contents.append(TextContent(content=event.content_block.text))

            # When Claude wants to use a tool
            elif (
                event.type == "content_block_start"
                and event.content_block.type == "tool_use"
            ):
                message_contents.append(
                    ToolUseContent(
                        name=event.content_block.name,
                        input={},
                        id=event.content_block.id,
                    )
                )

            # When Claude finishes a block
            elif event.type == "content_block_stop":
                current_index += 1

            # When Claude adds more text to the current block
            elif (
                event.type == "content_block_delta"
                and event.delta.type == "text_delta"
                and isinstance(message_contents[-1], TextContent)
            ):
                message_contents[-1].content += event.delta.text

                # Yield this content early so we can stream it to the client
                yield TextContent(content=event.delta.text, chunk_index=current_index)

            # When Claude is building up JSON data for a tool
            elif (
                event.type == "content_block_delta"
                and event.delta.type == "input_json_delta"
            ):
                partial_json += event.delta.partial_json

            # When Claude wants to use a tool and has all the information ready
            elif (
                event.type == "message_delta"
                and event.delta.stop_reason == "tool_use"
                and isinstance(message_contents[-1], ToolUseContent)
            ):
                tool_result = ToolResultContent(
                    tool_use_id=message_contents[-1].id,
                    content="",
                    is_error=False,
                )

                try:
                    message_contents[-1].input = json.loads(partial_json)

                    function_name = message_contents[-1].name

                    # Find the right tool to use
                    function = next(
                        (tool for tool in tools if tool.__name__ == function_name), None
                    )

                    if function is None:
                        raise ValueError(f"Function {function_name} not found")

                    # Use the tool and get its result
                    # Some tools need to run asynchronously (in the background)
                    function_result = (
                        await function(**message_contents[-1].input)
                        if asyncio.iscoroutinefunction(function)
                        else function(**message_contents[-1].input)
                    )

                    tool_result.content = str(function_result)
                except Exception as e:
                    tool_result.is_error = True
                    tool_result.content = str(e)
                finally:
                    partial_json = ""

                async for content in self.on_message(
                    [
                        *messages,
                        Message(role="assistant", content=message_contents),
                        Message(role="user", content=[tool_result]),
                    ],
                ):
                    content.chunk_index = current_index - 1
                    yield content

    def _convert_messages_to_anthropic_format(
        self, messages: List[Message]
    ) -> list[MessageParam]:
        """
        Converts our message format into one that Claude can understand.
        This is like translating between two languages.

        Example:
        Our format:
            Message(role="user", content="How are you?")
        Claude's format:
            {"role": "user", "content": [{"type": "text", "text": "How are you?"}]}

        Args:
            messages: List of messages in our format

        Returns:
            List of messages in Claude's format

        The function handles different types of content:
        - Regular text messages
        - Tool usage requests
        - Tool results
        """
        return [
            {
                "role": message.role,
                "content": [
                    # For regular text messages
                    {
                        "type": "text",
                        "text": content.content,
                    }
                    if isinstance(content, TextContent)
                    # For when Claude wants to use a tool
                    else {
                        "type": "tool_use",
                        "id": content.id,
                        "input": content.input,
                        "name": content.name,
                    }
                    if isinstance(content, ToolUseContent)
                    # For tool results we want to tell Claude about
                    else {
                        "type": "tool_result",
                        "content": str(content.content),
                        "tool_use_id": str(content.tool_use_id),
                        "is_error": content.is_error,
                    }
                    for content in message.content
                ],
            }
            for message in messages
        ]
