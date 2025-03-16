import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from typing import Any, Generic

from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.message_param import MessageParam
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent
from prisma.enums import message_role
from prisma.models import processed_pdfs

from src.agents.base_agent import BaseAgent, TConfig
from src.agents.models import PDFSearchResult
from src.agents.utils.citation_formatter import format_inline_citation
from src.agents.utils.decode_data_url_to_image import decode_data_url_to_image, encode_image_to_data_url
from src.agents.utils.resize_image_to_byte_size import resize_image_to_byte_size
from src.lib.prisma import prisma
from src.lib.supabase import supabase
from src.logger import logger
from src.models.messages import (
    ImageContent,
    Message,
    MessageContent,
    PDFContent,
    TextContent,
    TextDeltaContent,
    ToolResultContent,
    ToolUseContent,
)
from src.services.easylog_backend.backend_service import BackendService
from src.utils.media_detection import extract_base64_content, guess_media_type
from src.utils.pydantic_to_anthropic_tool import pydantic_to_anthropic_tool


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

    def __init__(self, thread_id: str, backend: BackendService, **kwargs: dict[str, Any]) -> None:
        """
        Sets up the agent with necessary connections and settings.

        This is like preparing a workstation:
        1. Set up basic tools (from BaseAgent)
        2. Establish connection to Claude (Anthropic's API)
        """
        super().__init__(thread_id, backend, **kwargs)

        # Create a connection to Anthropic using our API key
        # This is like logging into a special service
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    def _convert_messages_to_anthropic_format(self, messages: list[Message]) -> list[MessageParam]:
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

        message_history: list[MessageParam] = [
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
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": guess_media_type(content.content),
                                    "data": extract_base64_content(content.content),
                                },
                            }
                        ]
                        if content.content_format == "image"
                        else content.content,
                        "tool_use_id": str(content.tool_use_id),
                        "is_error": content.is_error,
                    }
                    if isinstance(content, ToolResultContent)
                    else {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content.content_type,
                            "data": content.content,
                        },
                    }
                    if isinstance(content, ImageContent)
                    else {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": content.content,
                        },
                        "citations": {"enabled": True},
                    }
                    if isinstance(content, PDFContent)
                    else {
                        "type": "text",
                        "text": "[empty]",
                    }
                    for content in message.content
                ],
            }
            for message in messages
            if message.role in [message_role.user, message_role.assistant]
        ]

        # Remove messages with empty content and their following message
        # FIXME: We should not even allow this kind of data in the database
        i = len(message_history) - 1
        while i >= 0:
            # Check if current message has empty content
            if not message_history[i]["content"]:
                self.logger.warning(f"Removing message {i} with empty content and its following message")

                # Remove current message
                message_history.pop(i)

                # Remove next message if it exists
                if i < len(message_history):
                    message_history.pop(i)
            i -= 1

        return message_history

    async def handle_stream(
        self,
        stream: AsyncStream[RawMessageStreamEvent],
        tools: list[Callable] = [],
    ) -> AsyncGenerator[MessageContent, None]:
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

        # Store different parts of the response (text, tool use, etc.)
        message_contents: list[TextContent | ToolUseContent] = []

        # Keep track of any partial JSON we need to build up
        partial_json = ""

        # Process each piece of Claude's response as it arrives
        async for event in stream:
            # When Claude starts a new text block
            if event.type == "content_block_start" and event.content_block.type == "text":
                message_contents.append(TextContent(content=event.content_block.text))

            # When Claude wants to use a tool
            elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                message_contents.append(
                    ToolUseContent(
                        name=event.content_block.name,
                        input={},
                        id=event.content_block.id,
                    )
                )

            # When Claude finishes a block
            elif (
                event.type == "content_block_stop"
                and message_contents
                and isinstance(message_contents[-1], TextContent)
            ):
                yield TextContent(
                    content=message_contents[-1].content,
                    type="text",
                )

            # When Claude adds more text to the current block
            elif (
                event.type == "content_block_delta"
                and event.delta.type == "text_delta"
                and message_contents
                and isinstance(message_contents[-1], TextContent)
            ):
                message_contents[-1].content += event.delta.text

                # Yield this content early so we can stream it to the client
                yield TextDeltaContent(content=event.delta.text)

            elif (
                event.type == "content_block_delta"
                and event.delta.type == "citations_delta"
                and isinstance(message_contents[-1], TextContent)
            ):
                self.logger.info(event.delta.citation)
                message_contents[-1].content += format_inline_citation(event.delta.citation)

            # When Claude is building up JSON data for a tool
            elif event.type == "content_block_delta" and event.delta.type == "input_json_delta":
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
                    message_contents[-1].input = json.loads(partial_json or "{}")

                    # Extract the name of the tool that Claude wants to use
                    function_name = message_contents[-1].name

                    # Search through available tools to find one matching the requested name
                    # Returns None if no matching tool is found
                    function = next((tool for tool in tools if tool.__name__ == function_name), None)

                    # If no matching tool was found, raise an error
                    if function is None:
                        raise ValueError(f"Function {function_name} not found")

                    # Execute the tool with the provided input parameters
                    # If the tool is async (returns a coroutine), await it
                    # Otherwise, execute it synchronously
                    tool_result.content = str(
                        await function(**message_contents[-1].input)
                        if asyncio.iscoroutinefunction(function)
                        else function(**message_contents[-1].input)
                    )

                    # When dealing with images, we need to resize them to a reasonable size
                    # and convert them to a data URL
                    if tool_result.content.startswith("data:image/"):
                        tool_result.content = encode_image_to_data_url(
                            image=resize_image_to_byte_size(
                                image=decode_data_url_to_image(tool_result.content),
                                target_size_bytes=500_000,  # 500KB
                                image_format="JPEG",
                                quality=80,
                                tolerance=0.1,
                            ),
                            format="JPEG",
                        )
                        tool_result.content_format = "image"

                except Exception as e:
                    # If anything goes wrong during tool execution:
                    # 1. Mark the result as an error
                    # 2. Store the error message
                    # 3. Log the error
                    tool_result.is_error = True
                    tool_result.content = str(e)
                    logger.error(f"Error executing tool {e}", exc_info=True)

                finally:
                    yield message_contents[-1]
                    yield tool_result

                    # Clear the partial JSON buffer, regardless of success or failure
                    partial_json = ""

    async def search_knowledge(self, query: str) -> processed_pdfs | None:
        knowledge = self.get_knowledge()

        knowledge_items = "\n".join([f"ID: {item.object_id}\nSummary: {item.short_summary}" for item in knowledge])

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system=f"""
            From the following list of documents, find the most relevant document to the query if any.

            {knowledge_items}
            """,
            messages=[
                {"role": "user", "content": query},
            ],
            tools=[
                pydantic_to_anthropic_tool(
                    PDFSearchResult,
                    "Search for a document in the knowledge base",
                )
            ],
            tool_choice={
                "type": "tool",
                "name": PDFSearchResult.__name__,
            },
        )

        self.logger.debug(f"Response: {response}")

        result: PDFSearchResult | None = None
        for tool_use in response.content:
            if tool_use.type == "tool_use":
                result = PDFSearchResult(**json.loads(json.dumps(tool_use.input)))

        if not result:
            return None

        return next((item for item in knowledge if item.object_id == result.id), None)

    async def load_image(self, content_id: str, file_name: str) -> bytes:
        file_data = prisma.processed_pdfs.find_first(
            where={
                "id": content_id,
            },
            include={
                "images": {
                    "include": {
                        "object": True,
                    },
                    "where": {
                        "original_file_name": file_name,
                    },
                }
            },
        )

        if not file_data:
            raise ValueError("File not found")

        if not file_data.images:
            raise ValueError("No images found")

        image = file_data.images[0]

        if not image.object or not image.object.name or not image.object.bucket_id:
            raise ValueError("Image object not found")

        self.logger.info(f"Loading image {image.object.name} from bucket {image.object.bucket_id}")

        return supabase.storage.from_(image.object.bucket_id).download(image.object.name)
