from collections.abc import AsyncGenerator, Iterable

from openai.types.chat import ChatCompletionMessageParam

from src.agents.agent_loader import AgentLoader
from src.agents.base_agent import BaseAgent
from src.lib.prisma import prisma
from src.logger import logger
from src.models.message_create import (
    MessageCreateInputFileContent,
    MessageCreateInputImageContent,
    MessageCreateInputTextContent,
)
from src.models.messages import (
    GeneratedMessage,
    MessageContent,
    TextDeltaContent,
    ToolResultContent,
)
from src.services.messages.utils.db_message_to_openai_param import db_message_to_openai_param
from src.services.messages.utils.input_message_to_openai_param import input_content_to_openai_param


class AgentNotFoundError(Exception):
    pass


class MessageService:
    @classmethod
    async def forward_message(
        cls,
        thread_id: str,
        input_content: list[
            MessageCreateInputFileContent | MessageCreateInputImageContent | MessageCreateInputTextContent
        ],
        agent_class: str,
        agent_config: dict,
    ) -> AsyncGenerator[tuple[MessageContent, list[GeneratedMessage]], None]:
        """Forward a message to the agent and yield the individual chunks of the response along with the cumulative list of generated messages. Will also save the user message and the agent response to the database.

        Args:
            thread_id (str): The ID of the thread.
            input_content (list): The content of the user message.
            agent_class (str): The class of the agent.
            agent_config (dict): The config of the agent.

        Raises:
            AgentNotFoundError: The agent class was not found.

        Returns:
            AsyncGenerator[tuple[MessageContent, list[GeneratedMessage]], None]:
                A generator of tuples, each containing a message chunk and the list of all messages generated up to that point.

        Yields:
            Iterator[tuple[MessageContent, list[GeneratedMessage]]]:
                A generator of tuples containing message chunks and the cumulative message list.
        """

        logger.info(f"Loading agent {agent_class}")

        # Try to load the agent
        agent = AgentLoader.get_agent(agent_class, thread_id, agent_config)

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

        try:
            async for content_chunk, current_generated_messages in cls.call_agent(agent, thread_history, []):
                yield content_chunk, current_generated_messages

        except Exception as e:
            logger.error(f"Error forwarding message: {e}", exc_info=e)
            raise e

    @classmethod
    async def call_agent(
        cls,
        agent: BaseAgent,
        thread_history: Iterable[ChatCompletionMessageParam],
        initial_generated_messages: list[GeneratedMessage],
        max_recursion_depth: int = 5,
        current_depth: int = 0,
    ) -> AsyncGenerator[tuple[MessageContent, list[GeneratedMessage]], None]:
        """Call the agent with the thread history and return the response.

        Args:
            agent (BaseAgent): The agent to call.
            thread_history (list[Message]): The thread history.
            initial_generated_messages (list[GeneratedMessage]): Initial generated messages.
            max_recursion_depth (int): Maximum depth for recursive calls.
            current_depth (int): Current recursion depth.

        Returns:
            AsyncGenerator[tuple[MessageContent, list[GeneratedMessage]], None]:
                A generator of message chunks and the current state of generated messages.
        """
        if current_depth >= max_recursion_depth:
            logger.warning(f"Maximum recursion depth ({max_recursion_depth}) reached, stopping recursion")
            return

        generated_messages: list[GeneratedMessage] = initial_generated_messages.copy()

        async for content_chunk in await agent.forward_message(thread_history):
            logger.info(f"Received chunk: {content_chunk.model_dump_json()[:2000]}")

            last_message = generated_messages[-1] if len(generated_messages) > 0 else None

            if isinstance(content_chunk, ToolResultContent):
                generated_messages.append(
                    GeneratedMessage(role="tool", tool_use_id=content_chunk.tool_use_id, content=[content_chunk])
                )
            elif not isinstance(content_chunk, TextDeltaContent):
                if not last_message or last_message.role == "tool":
                    generated_messages.append(GeneratedMessage(role="assistant", content=[]))

                generated_messages[-1].content.append(content_chunk)

            # First yield the current chunk before potential recursive calls
            yield content_chunk, generated_messages.copy()

        if not any(content_chunk.role == "tool" for content_chunk in generated_messages):
            return

        # Recursively call the agent if we have a tool call
        async for nested_chunk, nested_messages in cls.call_agent(
            agent, thread_history, generated_messages.copy(), max_recursion_depth, current_depth + 1
        ):
            # Yield each chunk from the nested call
            yield nested_chunk, nested_messages

        # # Check if the content_chunk is a tool call and recursively call the agent if needed
        # if isinstance(content_chunk, ToolCallContent) and current_depth < max_recursion_depth:
        #     # Construct updated thread history with the current generated messages
        #     updated_thread_history = cls._construct_updated_thread_history(
        #         thread_history,
        #         generated_messages
        #     )

        #     # Recursively call the agent
        #     async for nested_chunk, nested_messages in await cls.call_agent(
        #         agent,
        #         updated_thread_history,
        #         generated_messages.copy(),
        #         max_recursion_depth,
        #         current_depth + 1
        #     ):
        #         # Yield each chunk from the nested call
        #         yield nested_chunk, nested_messages

        #         # Update our messages with the latest state
        #         generated_messages = nested_messages
