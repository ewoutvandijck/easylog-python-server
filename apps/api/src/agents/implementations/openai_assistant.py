from typing import AsyncGenerator, List

from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent


class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str


class OpenAIAssistant(BaseAgent):
    client: OpenAI

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = OpenAI(
            # Make sure to set the OPENAI_API_KEY environment variable
            api_key=self.get_env("OPENAI_API_KEY"),
        )

    async def on_message(
        self, messages: List[Message], config: OpenAIAssistantConfig
    ) -> AsyncGenerator[MessageContent, None]:
        """An agent that uses OpenAI Assistants to generate responses.

        Args:
            messages (List[Message]): The messages to send to the assistant.
            config (OpenAIAssistantConfig): The configuration for the assistant.

        Yields:
            Generator[MessageContent, None, None]: The streamed response from the assistant.
        """

        # First, we retrieve the assistant
        assistant = self.client.beta.assistants.retrieve(config.assistant_id)

        # If we already have a thread ID, we reuse it
        thread_id: str = self.get_metadata("thread_id")
        if thread_id:
            thread = self.client.beta.threads.retrieve(thread_id=thread_id)
        else:
            # Otherwise, we create a new thread
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": message.role,
                        "content": message.content[0].content,
                    }
                    for message in messages
                ]
            )
            self.set_metadata("thread_id", thread.id)

        # Add the user messages to the thread
        for message in messages:
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message.content[0].content,
            )

        # Then!, we create a run for the thread. We stream the response back to the client.
        for x in self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, stream=True
        ):
            # We only care about the message deltas
            if isinstance(x.data, MessageDeltaEvent):
                for delta in x.data.delta.content or []:
                    # We only care about text deltas, we ignore any other types of deltas
                    if (
                        isinstance(delta, TextDeltaBlock)
                        and delta.text
                        and delta.text.value
                    ):
                        yield MessageContent(
                            content=delta.text.value,
                            type="text",
                        )
