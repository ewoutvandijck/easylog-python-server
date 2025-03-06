from collections.abc import AsyncGenerator, Sequence
from typing import Literal, cast

from prisma import Json
from prisma.enums import message_content_type, message_role

from src.agents.agent_loader import AgentLoader
from src.agents.base_agent import BaseAgent
from src.lib.prisma import prisma
from src.logger import logger
from src.models.messages import (
    ContentType,
    ImageContent,
    Message,
    MessageContent,
    PDFContent,
    TextContent,
    TextDeltaContent,
    ToolResultContent,
    ToolResultDeltaContent,
    ToolUseContent,
)
from src.services.easylog_backend.backend_service import BackendService
from src.settings import settings


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        input_content: list[MessageContent],
        agent_class: str,
        agent_config: dict,
        bearer_token: str | None = None,
    ) -> AsyncGenerator[MessageContent, None]:
        """Forward a message to the agent and yield the individual chunks of the response. Will also save the user message and the agent response to the database.

        Args:
            thread_id (str): The ID of the thread.
            content (list[TextContent]): The content of the user message.
            agent_class (str): The class of the agent.
            agent_config (dict): The config of the agent.

        Raises:
            AgentNotFoundError: The agent class was not found.

        Returns:
            AsyncGenerator[TextContent, None]: A generator of message chunks.

        Yields:
            Iterator[TextContent]: A generator of message chunks.
        """

        backend_service = BackendService(bearer_token=bearer_token or "", base_url=settings.EASYLOG_API_URL)

        logger.info(f"Loading agent {agent_class}")

        # Try to load the agent
        agent = AgentLoader.get_agent(agent_class, thread_id, backend_service, agent_config)

        if not agent:
            raise AgentNotFoundError(f"Agent class {agent_class} not found")

        logger.info(f"Agent {agent_class} loaded")

        logger.info("Getting thread history")

        # Fetch the thread history including the new user message
        thread_history = [
            *(
                Message(
                    role=message.role.value,
                    content=[
                        TextContent(
                            content=message_content.content or "",
                        )
                        if message_content.type == message_content_type.text
                        else ImageContent(
                            content=message_content.content or "",
                            content_type=cast(ContentType, message_content.content_type) or "image/jpeg",
                        )
                        if message_content.type == message_content_type.image
                        else PDFContent(
                            content=message_content.content or "",
                        )
                        if message_content.type == message_content_type.pdf
                        else ToolResultContent(
                            tool_use_id=message_content.tool_use_id or "",
                            content=message_content.content or "",
                            content_format=cast(Literal["image", "unknown"], message_content.content_format),
                            is_error=message_content.tool_use_is_error or False,
                        )
                        if message_content.type == message_content_type.tool_result
                        else ToolUseContent(
                            id=message_content.tool_use_id or "",
                            name=message_content.tool_use_name or "",
                            input=dict(message_content.tool_use_input) if message_content.tool_use_input else {},
                        )
                        for message_content in message.contents
                        if message_content is not None
                    ],
                )
                for message in prisma.messages.find_many(
                    where={
                        "thread_id": thread_id,
                    },
                    include={"contents": True},
                )
                if message.contents is not None
            ),
            Message(
                role="user",
                content=input_content,
            ),
        ]

        logger.info(f"Thread history: {len(thread_history)} messages")

        logger.info("Forwarding message through agent")

        # Forward the history through the agent
        generated_messages: list[Message] = []

        try:
            async for content_chunk, role in cls.call_agent(agent, thread_history):
                # There's a size limit of 4096 on SSE events, so we need to yield the content in chunks.
                # See: https://ithy.com/article/0e048e4cbc904c509bee7b462dd26dd9
                if isinstance(content_chunk, ToolResultContent) and len(content_chunk.content) > 1000:
                    content = content_chunk.content
                    while content:
                        chunk = content[:1000]
                        content = content[1000:]

                        yield ToolResultDeltaContent(
                            tool_use_id=content_chunk.tool_use_id,
                            content=chunk,
                            content_format=content_chunk.content_format,
                            is_error=content_chunk.is_error,
                        )
                else:
                    yield content_chunk

                last_message = generated_messages[-1] if len(generated_messages) > 0 else None

                if not last_message or last_message.role != role:
                    generated_messages.append(Message(role=role, content=[]))

                generated_messages[-1].content.append(content_chunk)
        except Exception as e:
            logger.error(f"Error forwarding message: {e}", exc_info=e)
            logger.error("Messages wont be saved!")
            raise e

        MessageService.save_message(
            thread_id,
            agent_class,
            input_content,
            message_role.user,
        )

        for message in generated_messages:
            # Save the agent response
            MessageService.save_message(
                thread_id,
                agent_class,
                [content for content in message.content if not isinstance(content, TextDeltaContent)],
                message_role.assistant if message.role == "assistant" else message_role.user,
            )

    @classmethod
    async def call_agent(
        cls, agent: BaseAgent, thread_history: list[Message]
    ) -> AsyncGenerator[tuple[MessageContent, Literal["user", "assistant"]], None]:
        """Call the agent with the thread history and return the response.

        Args:
            agent (BaseAgent): The agent to call.
            thread_history (list[Message]): The thread history.

        Returns:
            AsyncGenerator[tuple[MessageContent, int], None]: A generator of message chunks.
        """

        generated_content: list[MessageContent] = []

        async for content_chunk in agent.forward(thread_history):
            logger.info(f"Received chunk: {content_chunk.model_dump_json()[:2000]}")

            if isinstance(content_chunk, ToolResultContent):
                yield content_chunk, "user"

                async for chunk in cls.call_agent(
                    agent,
                    [
                        *thread_history,
                        Message(
                            role="assistant",
                            content=generated_content,
                        ),
                        Message(
                            role="user",
                            content=[content_chunk],
                        ),
                    ],
                ):
                    yield chunk
            else:
                yield content_chunk, "assistant"

                if not isinstance(content_chunk, TextDeltaContent):
                    generated_content.append(content_chunk)

    @classmethod
    def save_message(
        cls,
        thread_id: str,
        agent_class: str,
        content_chunks: Sequence[MessageContent],
        role: message_role,
    ) -> None:
        prisma.messages.create(
            data={
                "thread": {"connect": {"id": thread_id}},
                "agent_class": agent_class,
                "role": role,
                "contents": {
                    "create": [  # type: ignore
                        {
                            "type": "text",
                            "content": content_chunk.content,
                        }
                        if isinstance(content_chunk, TextContent)
                        else {
                            "type": "image",
                            "content": content_chunk.content,
                            "content_type": content_chunk.content_type,
                        }
                        if isinstance(content_chunk, ImageContent)
                        else {
                            "type": "pdf",
                            "content": content_chunk.content,
                            "content_type": "application/pdf",
                        }
                        if isinstance(content_chunk, PDFContent)
                        else {
                            "type": "tool_result",
                            "content": content_chunk.content,
                            "content_format": content_chunk.content_format,
                            "tool_use_is_error": content_chunk.is_error,
                            "tool_use_id": content_chunk.tool_use_id,
                        }
                        if isinstance(content_chunk, ToolResultContent)
                        else {
                            "type": "tool_use",
                            "tool_use_id": content_chunk.id,
                            "tool_use_name": content_chunk.name,
                            "tool_use_input": Json(content_chunk.input),
                        }
                        if isinstance(content_chunk, ToolUseContent)
                        else {
                            "type": "text_delta",
                            "content": content_chunk.content,
                        }
                        for content_chunk in content_chunks
                        if isinstance(content_chunk, MessageContent)
                    ]
                },
            }
        )
