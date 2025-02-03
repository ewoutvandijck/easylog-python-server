from typing import AsyncGenerator, List

from openai.types.chat_model import ChatModel
from pydantic import BaseModel, Field
from src.agents.openai_agent import OpenAIAgent
from src.models.messages import Message, TextContent


class OpenAIAssistantConfigWithId(BaseModel):
    assistant_id: str


class OpenAIAssistantConfigWithParams(BaseModel):
    model: ChatModel = Field(default="o1-mini")
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    temperature: float | None = Field(default=None)
    instructions: str | None = Field(default=None)
    top_p: float | None = Field(default=None)


class OpenAIAssistant(
    OpenAIAgent[OpenAIAssistantConfigWithId | OpenAIAssistantConfigWithParams]
):
    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        """An agent that uses OpenAI Assistants to generate responses.
        This class handles all the communication with OpenAI's assistant feature,
        including managing conversations and streaming responses.

        Args:
            messages (List[Message]): All messages in the conversation, including the new one.

        Yields:
            Generator[TextContent, None, None]: Streams back the assistant's response piece by piece.
        """

        # Create a unique identifier (hash) from the config to use for caching
        # This helps us avoid creating duplicate assistants with the same settings
        config_hash = str(hash(self.config.model_dump_json()))

        # STEP 1: Get or create an OpenAI assistant
        # There are three ways to get an assistant:

        # Option 1: Use an existing assistant ID provided in the config
        if isinstance(self.config, OpenAIAssistantConfigWithId):
            self.logger.info("Using existing assistant with provided ID")
            assistant = await self.client.beta.assistants.retrieve(
                self.config.assistant_id
            )
        # Option 2: Use a previously created assistant from our cache
        elif self.get_metadata(config_hash):
            self.logger.info(
                "Found a matching assistant in cache - reusing it to save time and resources",
                extra={"config_hash": config_hash},
            )

            assistant = await self.client.beta.assistants.retrieve(
                assistant_id=self.get_metadata(config_hash)
            )
        # Option 3: Create a new assistant and cache it for future use
        else:
            self.logger.info(
                "No existing assistant found - creating a new one with specified model",
                extra={"config_hash": config_hash},
            )

            assistant = await self.client.beta.assistants.create(
                # Pass all the config parameters to the assistant creation
                # Exclude None values to let OpenAI fill in the defaults
                **self.config.model_dump(exclude_none=True)
            )

            # Save the new assistant's ID in our cache for future use
            self.set_metadata(config_hash, assistant.id)

        # Split messages into previous conversation history and the new message
        previous_messages = messages[:-1]  # All messages except the last one
        current_message = messages[-1]  # The newest message we just received

        # STEP 2: Set up the conversation thread
        # A thread is like a conversation container in OpenAI's system

        # Check if we already have an ongoing conversation (thread)
        thread_id: str = self.get_metadata("thread_id")
        if thread_id:
            self.logger.info("Continuing existing conversation thread")
            thread = await self.client.beta.threads.retrieve(thread_id=thread_id)
        else:
            # Start a new conversation thread with all previous messages
            self.logger.info("Starting a new conversation thread")
            thread = await self.client.beta.threads.create(
                messages=[
                    {
                        "role": message.role,
                        "content": [
                            {
                                "type": content.type,
                                "text": content.content,
                            }
                            # Only include text content, skip other types (like images)
                            for content in message.content
                            if isinstance(content, TextContent)
                        ],
                    }
                    for message in messages
                ]
            )

            # Add all previous messages to the thread to maintain conversation context
            for message in previous_messages:
                await self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=message.role,
                    content=[
                        {
                            "type": content.type,
                            "text": content.content,
                        }
                        for content in message.content
                        if isinstance(content, TextContent)
                    ],
                )

            # Save the thread ID for future messages in this conversation
            self.set_metadata("thread_id", thread.id)

        # STEP 3: Add the new message to the conversation
        self.logger.info("Adding new message to the conversation")
        await self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[
                {
                    "type": content.type,
                    "text": content.content,
                }
                for content in current_message.content
                if isinstance(content, TextContent)
            ],
        )

        # STEP 4: Get the assistant's response
        # Create a run (which is OpenAI's way of getting the assistant to process and respond)
        # We use stream=True to get the response piece by piece instead of waiting for the whole thing
        self.logger.info("Getting assistant's response")
        stream = await self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, stream=True
        )

        # STEP 5: Stream the response back to the user piece by piece
        async for message in self.handle_assistant_stream(stream):
            yield message
