import asyncio
import json
from typing import AsyncGenerator, Callable, Generic, List

from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.message_param import MessageParam
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent

from src.agents.base_agent import BaseAgent, TConfig
from src.logger import logger
from src.models.messages import (
    Message,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)


class AnthropicAgent(BaseAgent[TConfig], Generic[TConfig]):
    """
    A friendly AI assistant that talks to Claude (Anthropic's AI model).
    Think of this as a translator between your app and Claude.

    What can this assistant do?
    1. Connect to Claude (like making a phone call to a smart friend)
    2. Send your messages to Claude and get responses back
    3. Use special tools when needed (like a calculator or search engine)
    4. Get responses piece by piece (like reading a message as someone types it)

    Simple example:
        # Create your AI assistant
        agent = AnthropicAgent()

        # Ask it a question and wait for the response
        response = await agent.on_message(["What's the weather like?"])
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
        Handles Claude's response as it comes in, piece by piece.

        Imagine you're on a phone call where:
        1. Your friend Claude is thinking out loud
        2. Every time Claude says something, we write it down
        3. Sometimes Claude needs to use tools (like a calculator)
        4. We send each piece of what Claude says back to you right away

        For example:
        - Claude: "Let me calculate 2+2..."
        - *Claude uses calculator tool*
        - Claude: "The answer is 4!"

        Args:
            stream: Claude's incoming response (like a live phone call)
            messages: The conversation history (what was said before)
            tools: Special helpers Claude can use (like calculators or search engines)
            content_index: Keeps track of which part of the response we're on

        Returns:
            Each piece of Claude's response as soon as we get it
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
                    # Parse the accumulated JSON string into a Python object and set it as the tool's input
                    message_contents[-1].input = json.loads(partial_json)

                    # Extract the name of the tool that Claude wants to use
                    function_name = message_contents[-1].name

                    # Search through available tools to find one matching the requested name
                    # Returns None if no matching tool is found
                    function = next(
                        (tool for tool in tools if tool.__name__ == function_name), None
                    )

                    # If no matching tool was found, raise an error
                    if function is None:
                        raise ValueError(f"Function {function_name} not found")

                    # Execute the tool with the provided input parameters
                    # If the tool is async (returns a coroutine), await it
                    # Otherwise, execute it synchronously
                    function_result = (
                        await function(**message_contents[-1].input)
                        if asyncio.iscoroutinefunction(function)
                        else function(**message_contents[-1].input)
                    )

                    # Convert the tool's result to a string
                    tool_result.content = str(function_result)

                except Exception as e:
                    # If anything goes wrong during tool execution:
                    # 1. Mark the result as an error
                    # 2. Store the error message
                    # 3. Log the error
                    tool_result.is_error = True
                    tool_result.content = str(e)
                    logger.error(f"Error executing tool {function_name}: {e}")

                finally:
                    # Clear the partial JSON buffer, regardless of success or failure
                    partial_json = ""

                # Continue the conversation with Claude by:
                # 1. Including all previous messages
                # 2. Adding Claude's latest response (including tool use)
                # 3. Adding the tool's result as a user message
                async for content in self.on_message(
                    [
                        *messages,  # Previous conversation
                        Message(
                            role="assistant", content=message_contents
                        ),  # Claude's current response
                        Message(
                            role="user", content=[tool_result]
                        ),  # Tool execution result
                    ],
                ):
                    # Maintain consistent chunk indexing for streaming
                    content.chunk_index = current_index - 1
                    yield content

    def _convert_messages_to_anthropic_format(
        self, messages: List[Message]
    ) -> list[MessageParam]:
        """
        Translates messages into a language Claude can understand.

        Think of this like translating between English and Spanish:
        - We have our way of writing messages
        - Claude has its own way of understanding messages
        - This function converts between the two

        Example:
            Our format:
                Message(role="user", content="What's 2+2?")

            Claude's format:
                {
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": "What's 2+2?"
                    }]
                }

        Args:
            messages: Our version of the messages

        Returns:
            Claude's version of the same messages
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
