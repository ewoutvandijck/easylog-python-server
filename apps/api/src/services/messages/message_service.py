from typing import AsyncGenerator, Sequence, cast

from prisma import Json
from prisma.enums import MessageContentType, MessageRole

from src.agents.agent_loader import AgentLoader
from src.db.prisma import prisma
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
    ToolUseContent,
)
from src.services.easylog_backend.backend_service import BackendService


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        input_content: list[
            TextContent | ImageContent | PDFContent | ToolResultContent | ToolUseContent
        ],
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

        backend_service = BackendService(bearer_token) if bearer_token else None

        logger.info(f"Loading agent {agent_class}")

        # Try to load the agent
        agent = AgentLoader.get_agent(
            agent_class, thread_id, agent_config, backend_service
        )

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
                        if message_content.type == MessageContentType.text
                        else ImageContent(
                            content=message_content.content or "",
                            content_type=cast(ContentType, message_content.content_type)
                            or "image/jpeg",
                        )
                        if message_content.type == MessageContentType.image
                        else PDFContent(
                            content=message_content.content or "",
                        )
                        if message_content.type == MessageContentType.pdf
                        else ToolResultContent(
                            tool_use_id=message_content.tool_use_id or "",
                            content=message_content.content or "",
                            is_error=message_content.tool_use_is_error or False,
                        )
                        if message_content.type == MessageContentType.tool_result
                        else ToolUseContent(
                            id=message_content.tool_use_id or "",
                            name=message_content.tool_use_name or "",
                            input=dict(message_content.tool_use_input)
                            if message_content.tool_use_input
                            else {},
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
        output_content: list[MessageContent] = []
        tool_result_content: ToolResultContent | None = None
        async for content_chunk in agent.forward(thread_history):
            logger.info(f"Received chunk: {content_chunk}")

            if isinstance(content_chunk, ToolResultContent):
                tool_result_content = content_chunk
                break

            output_content.append(content_chunk)

            # Yield early to allow the frontend to render the message as it comes in
            yield content_chunk

        MessageService.save_message(
            thread_id,
            agent_class,
            input_content,
            MessageRole.user,
        )

        # Save the agent response
        MessageService.save_message(
            thread_id,
            agent_class,
            [
                chunk
                for chunk in output_content
                # Don't save text deltas
                if not isinstance(chunk, TextDeltaContent)
            ],
            MessageRole.assistant,
        )

        logger.info("Message saved")

        if tool_result_content:
            yield tool_result_content
            async for chunk in cls.forward_message(
                thread_id,
                [tool_result_content],
                agent_class,
                agent_config,
                bearer_token,
            ):
                yield chunk

    @classmethod
    def save_message(
        cls,
        thread_id: str,
        agent_class: str,
        content_chunks: Sequence[MessageContent],
        role: MessageRole,
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
                        }
                        if isinstance(content_chunk, ImageContent)
                        else {
                            "type": "pdf",
                            "content": content_chunk.content,
                        }
                        if isinstance(content_chunk, PDFContent)
                        else {
                            "type": "tool_result",
                            "content": content_chunk.content,
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
