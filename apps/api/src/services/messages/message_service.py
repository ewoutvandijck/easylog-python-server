from typing import AsyncGenerator, Literal

from src.agents.agent_loader import AgentLoader
from src.db.prisma import prisma
from src.logger import logger
from src.models.messages import Message, MessageChunkContent, MessageContent
from src.services.easylog_backend.backend_service import BackendService


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        content: list[MessageContent],
        agent_class: str,
        agent_config: dict,
        bearer_token: str | None = None,
    ) -> AsyncGenerator[MessageChunkContent, None]:
        """Forward a message to the agent and yield the individual chunks of the response. Will also save the user message and the agent response to the database.

        Args:
            thread_id (str): The ID of the thread.
            content (list[MessageContent]): The content of the user message.
            agent_class (str): The class of the agent.
            agent_config (dict): The config of the agent.

        Raises:
            AgentNotFoundError: The agent class was not found.

        Returns:
            AsyncGenerator[MessageChunkContent, None]: A generator of message chunks.

        Yields:
            Iterator[MessageChunkContent]: A generator of message chunks.
        """

        backend_service = BackendService(bearer_token) if bearer_token else None
        agent_loader = AgentLoader(thread_id, backend_service)

        logger.info(f"Loading agent {agent_class}")

        # Try to load the agent
        agent = agent_loader.get_agent(agent_class)
        if not agent:
            raise AgentNotFoundError(
                f"Agent class {agent_class} not found, available agents are {', '.join(map(lambda agent: agent.__class__.__name__, agent_loader.agents))}"
            )

        logger.info(f"Agent {agent_class} loaded")
        logger.info("Getting thread history")

        # Fetch the thread history including the new user message
        thread_history = [
            *(
                Message(
                    role=message.role,  # type: ignore
                    content=[
                        MessageContent(
                            type=message_content.content_type,  # type: ignore
                            content=message_content.content,
                        )
                        for message_content in message.contents or []
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
        compressed_chunks: list[MessageChunkContent] = []

        logger.info("Forwarding message through agent")

        # Forward the history through the agent
        async for chunk in agent.forward(thread_history, agent_config):
            logger.info(f"Received chunk: {chunk}")
            last_chunk = compressed_chunks[-1] if compressed_chunks else None
            if last_chunk and last_chunk.type == "text":
                last_chunk.content += chunk.content
            else:
                compressed_chunks.append(
                    MessageChunkContent(
                        chunk_index=len(compressed_chunks),
                        type=chunk.type,
                        content=chunk.content,
                    )
                )
                last_chunk = compressed_chunks[-1]

            # Yield the chunk to the client
            yield MessageChunkContent(
                # We include a chunk index so the client can reorder the chunks if needed
                chunk_index=last_chunk.chunk_index,
                type=chunk.type,
                content=chunk.content,
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

        # Save the agent response
        cls.save_message(
            thread_id=thread_id,
            message=Message(
                role="assistant",
                content=[
                    MessageContent(type=chunk.type, content=chunk.content)
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
                    ]
                },
            }
        )
