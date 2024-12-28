from typing import AsyncGenerator, Literal

from src.agents.agent_loader import AgentLoader
from src.db.prisma import prisma
from src.logger import logger
from src.models.messages import (
    Message,
    TextContent,
)
from src.services.easylog_backend.backend_service import BackendService


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        content: list[TextContent],
        agent_class: str,
        agent_config: dict,
        bearer_token: str | None = None,
    ) -> AsyncGenerator[TextContent, None]:
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
                    role=message.role,  # type: ignore
                    content=[
                        TextContent(
                            content=message_content.content,
                        )
                        for message_content in message.contents or []
                        # TODO: store and retrieve other content types
                        if message_content.content_type == "text"
                    ],
                )
                for message in cls.find_messages(thread_id)
            ),
            Message(
                role="user",
                content=content,
            ),
        ]

        logger.info(f"Thread history: {len(thread_history)} messages")

        # Chunks are "compressed" so we don't have to store every single token in the database.
        compressed_chunks: list[TextContent] = []

        logger.info("Forwarding message through agent")

        # Forward the history through the agent
        async for chunk in agent.forward(thread_history):
            logger.info(f"Received chunk: {chunk}")

            index = chunk.chunk_index

            # Try to find existing chunk with same index
            existing_chunk = next(
                (c for c in compressed_chunks if c.chunk_index == index), None
            )

            if existing_chunk and isinstance(existing_chunk, TextContent):
                existing_chunk.content += chunk.content
            else:
                compressed_chunks.append(
                    TextContent(
                        type="text",
                        content=chunk.content,
                        chunk_index=index,
                    )
                )
                existing_chunk = compressed_chunks[-1]

            # Yield the chunk to the client
            yield TextContent(
                type="text",
                content=chunk.content,
                chunk_index=index,
            )

        logger.info("Saving user message")

        # Save the user message
        cls.save_message(
            thread_id=thread_id,
            message=Message(
                role="user",
                content=content,
            ),
            agent_class=agent_class,
            role="user",
        )

        logger.info("Saving agent response")

        logger.info(f"Compressed chunks: {compressed_chunks}")

        # Save the agent response
        cls.save_message(
            thread_id=thread_id,
            message=Message(
                role="assistant",
                content=[
                    TextContent(
                        type="text",
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                    )
                    for chunk in compressed_chunks
                ],
            ),
            agent_class=agent_class,
            role="assistant",
        )

        logger.info("Message saved")

    @classmethod
    def find_messages(cls, thread_id: str):
        return prisma.messages.find_many(
            where={
                "thread_id": thread_id,
            },
            include={"contents": True},
        )

    @classmethod
    def save_message(
        cls,
        thread_id: str,
        message: Message,
        agent_class: str,
        role: Literal["user", "assistant"],
    ) -> None:
        prisma.messages.create(
            data={
                "thread": {"connect": {"id": thread_id}},
                "agent_class": agent_class,
                "role": role,
                "contents": {
                    "create": [
                        {
                            "content": message_content.content,
                            "content_type": message_content.type,
                        }
                        for message_content in message.content
                        # TODO: store and retrieve other content types
                        if isinstance(message_content, TextContent)
                    ]
                },
            }
        )
