import uuid
from collections.abc import AsyncGenerator, Iterable

from openai.types.chat import ChatCompletionMessageParam
from prisma import Base64, Json
from prisma.enums import message_content_type, message_role, widget_type

from src.agents.agent_loader import AgentLoader
from src.agents.base_agent import BaseAgent
from src.lib.prisma import prisma
from src.logger import logger
from src.models.message_create import (
    MessageCreateInputContent,
    MessageCreateInputFileContent,
    MessageCreateInputImageContent,
    MessageCreateInputTextContent,
)
from src.models.messages import (
    FileContent,
    ImageContent,
    MessageContent,
    MessageResponse,
    TextContent,
    TextDeltaContent,
    ToolResultContent,
    ToolUseContent,
)
from src.services.messages.utils.db_message_to_openai_param import db_message_to_openai_param
from src.services.messages.utils.generated_message_to_openai_param import generated_message_to_openai_param
from src.services.messages.utils.input_message_to_openai_param import input_content_to_openai_param


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        input_content: list[MessageCreateInputContent],
        agent_class: str,
        agent_config: dict,
        headers: dict,
        max_recursion_depth: int = 15,
    ) -> AsyncGenerator[MessageContent | MessageResponse, None]:
        """Forward a message to the agent and yield the individual chunks of the response. Will also save the user message and the agent response to the database.

        Args:
            thread_id (str): The ID of the thread.
            content (list[TextContent]): The content of the user message.
            agent_class (str): The class of the agent.
            agent_config (dict): The config of the agent.
            headers (dict): The headers of the request.
            max_recursion_depth (int): The maximum depth of recursion for the agent.
        Raises:
            AgentNotFoundError: The agent class was not found.

        Returns:
            AsyncGenerator[TextContent, None]: A generator of message chunks.

        Yields:
            Iterator[TextContent]: A generator of message chunks.
        """

        logger.info(f"Loading agent {agent_class}")

        # Try to load the agent
        agent = AgentLoader.get_agent(agent_class, thread_id, agent_config, headers)

        if not agent:
            raise AgentNotFoundError(f"Agent class {agent_class} not found")

        logger.info(f"Agent {agent_class} loaded")

        logger.info("Getting thread history")

        # Fetch the thread history including the new user message
        thread_history: Iterable[ChatCompletionMessageParam] = [
            *(
                db_message_to_openai_param(message)
                for message in await prisma.messages.find_many(
                    where={
                        "thread_id": thread_id,
                    },
                    include={"contents": True},
                )
                if message.contents is not None
            ),
            input_content_to_openai_param(input_content),
        ]

        logger.info(f"Thread history: {len(thread_history)} messages")

        logger.info("Forwarding message through agent")

        # Forward the history through the agent
        generated_messages: list[MessageResponse] = []

        yielded_messages: set[str] = set()

        try:
            async for content_chunk, messages in cls.call_agent(
                agent, thread_history, generated_messages, max_recursion_depth
            ):
                generated_messages = messages

                for message in messages:
                    if message.id in yielded_messages:
                        continue

                    yield MessageResponse(**message.model_dump(exclude={"content"}), content=[])

                    yielded_messages.add(message.id)

                yield content_chunk

        except Exception as e:
            logger.error(f"Error forwarding message: {e}", exc_info=e)
            raise e

        await prisma.messages.create(
            data={
                "agent_class": agent_class,
                "thread": {"connect": {"id": thread_id}},
                "role": message_role.user,
                "contents": {
                    "create": [
                        {
                            "type": message_content_type[content.type],
                            "text": content.text if isinstance(content, MessageCreateInputTextContent) else None,
                            "image_url": content.image_url
                            if isinstance(content, MessageCreateInputImageContent)
                            else None,
                            "file_data": Base64.fromb64(content.file_data)
                            if isinstance(content, MessageCreateInputFileContent)
                            else None,
                            "file_name": content.file_name
                            if isinstance(content, MessageCreateInputFileContent)
                            else None,
                        }
                        for content in input_content
                    ]
                },
            },
        )

        for message in generated_messages:
            for content in message.content:
                if isinstance(content, ToolUseContent):
                    logger.info(f"Tool use content: {content.input}")

            await prisma.messages.create(
                data={
                    "id": message.id,
                    "agent_class": agent_class,
                    "thread_id": thread_id,
                    "role": message_role[message.role],
                    "tool_use_id": message.tool_use_id,
                    "contents": {
                        "create": [
                            {
                                "id": content.id,
                                "type": message_content_type[content.type],
                                "text": content.text if isinstance(content, TextContent) else None,
                                "image_url": content.image_url if isinstance(content, ImageContent) else None,
                                "file_data": Base64.fromb64(content.file_data)
                                if isinstance(content, FileContent)
                                else None,
                                "file_name": content.file_name if isinstance(content, FileContent) else None,
                                "widget_type": widget_type[content.widget_type]
                                if isinstance(content, ToolResultContent) and content.widget_type is not None
                                else None,
                                "tool_use_id": content.tool_use_id
                                if isinstance(content, ToolResultContent) or isinstance(content, ToolUseContent)
                                else None,
                                "tool_name": content.name if isinstance(content, ToolUseContent) else None,
                                "tool_input": Json(content.input) if isinstance(content, ToolUseContent) else Json({}),
                                "tool_output": content.output if isinstance(content, ToolResultContent) else None,
                            }
                            for content in message.content
                            if not isinstance(content, TextDeltaContent)
                        ]
                    },
                }
            )

    @classmethod
    async def call_agent(
        cls,
        agent: BaseAgent,
        thread_history: Iterable[ChatCompletionMessageParam],
        initial_generated_messages: list[MessageResponse],
        max_recursion_depth: int = 5,
        current_depth: int = 0,
    ) -> AsyncGenerator[tuple[MessageContent, list[MessageResponse]], None]:
        """Call the agent with the thread history and return the response.

        Args:
            agent (BaseAgent): The agent to call.
            thread_history (list[Message]): The thread history.
            initial_generated_messages (list[MessageResponse]): Initial generated messages.
            max_recursion_depth (int): Maximum depth for recursive calls.
            current_depth (int): Current recursion depth.

        Returns:
            AsyncGenerator[tuple[MessageContent, list[MessageResponse]], None]:
                A generator of message chunks and the current state of generated messages.
        """

        if current_depth >= max_recursion_depth:
            logger.warning(f"Maximum recursion depth ({max_recursion_depth}) reached, stopping recursion")
            return

        generated_messages: list[MessageResponse] = []

        is_cancelled: bool = False

        async for content_chunk, should_stop in agent.forward_message(thread_history):
            logger.info(f"Received chunk: {content_chunk.model_dump_json()[:2000]}")

            if should_stop:
                is_cancelled = True

            last_message = generated_messages[-1] if len(generated_messages) > 0 else None

            if isinstance(content_chunk, ToolResultContent):
                generated_messages.append(
                    MessageResponse(
                        id=str(uuid.uuid4()),
                        role="tool",
                        tool_use_id=content_chunk.tool_use_id,
                        content=[],
                    )
                )
            elif not last_message or last_message.role == "tool":
                generated_messages.append(
                    MessageResponse(
                        id=str(uuid.uuid4()),
                        role="assistant",
                        content=[],
                    )
                )

            if not isinstance(content_chunk, TextDeltaContent):
                generated_messages[-1].content.append(content_chunk)

            # First yield the current chunk before potential recursive calls
            yield content_chunk, [*initial_generated_messages, *generated_messages]

        if is_cancelled:
            logger.warning("Agent call was cancelled, stopping recursion")
            return

        if any(generated_message.role == "tool" for generated_message in generated_messages):
            new_thread_history = [
                *thread_history,
                *[generated_message_to_openai_param(message) for message in generated_messages],
            ]

            new_initial_generated_messages = [*initial_generated_messages, *generated_messages]

            # Recursively call the agent if we have a tool call
            async for nested_chunk, nested_messages in cls.call_agent(
                agent,
                new_thread_history,
                new_initial_generated_messages,
                max_recursion_depth,
                current_depth + 1,
            ):
                yield nested_chunk, nested_messages
