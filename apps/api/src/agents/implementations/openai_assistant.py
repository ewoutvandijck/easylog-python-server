from typing import AsyncGenerator, List

from pydantic import BaseModel

from src.agents.openai_agent import OpenAIAgent
from src.models.messages import Message, TextContent


class OpenAIAssistantConfig(BaseModel):
    assistant_id: str


class OpenAIAssistant(OpenAIAgent[OpenAIAssistantConfig]):
    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        """An agent that uses OpenAI Assistants to generate responses.

        Args:
            messages (List[Message]): The messages to send to the assistant.
            config (OpenAIAssistantConfig): The configuration for the assistant.

        Yields:
            Generator[TextContent, None, None]: The streamed response from the assistant.
        """

        # First, we retrieve the assistant
        assistant = await self.client.beta.assistants.retrieve(self.config.assistant_id)

        previous_messages = messages[:-1]

        current_message = messages[-1]

        # If we already have a thread ID, we reuse it
        thread_id: str = self.get_metadata("thread_id")
        if thread_id:
            thread = await self.client.beta.threads.retrieve(thread_id=thread_id)
        else:
            # Otherwise, we create a new thread!!!!
            thread = await self.client.beta.threads.create(
                messages=[
                    {
                        "role": message.role,
                        "content": [
                            {
                                "type": content.type,
                                "text": content.content,
                            }
                            for content in message.content
                            if isinstance(content, TextContent)
                        ],
                    }
                    for message in messages
                ]
            )

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

            self.set_metadata("thread_id", thread.id)

        # Add the user messages to the thread
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

        # Then, we create a run for the thread. We stream the response back to the client.
        stream = await self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, stream=True
        )

        async for message in self.handle_stream(stream):
            yield message
