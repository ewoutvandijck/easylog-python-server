import os
from typing import Generator, List

from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock
from typing_extensions import override

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent


class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str


class OpenAIAssistant(BaseAgent):
    client: OpenAI

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    @override
    def on_message(
        self, messages: List[Message], config: OpenAIAssistantConfig
    ) -> Generator[MessageContent, None, None]:
        """An agent that uses OpenAI Assistants to generate responses.

        Args:
            messages (List[Message]): The messages to send to the assistant.
            config (OpenAIAssistantConfig): The configuration for the assistant.

        Yields:
            Generator[MessageContent, None, None]: The streamed response from the assistant.
        """

        # First, we retrieve the assistant
        assistant = self.client.beta.assistants.retrieve(config.assistant_id)

        # Then, we create a new thread with the messages. We could also reuse an existing thread, but we currently have no way to store those between requests.
        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": message.role,
                    "content": [
                        {
                            "type": content.type,
                            "text": content.content,
                        }
                        for content in message.content
                    ],
                }
                for message in messages
            ]
        )

        # Then, we create a run for the thread. We stream the response back to the client.
        for x in self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, stream=True
        ):
            # We only care about the message deltas
            if isinstance(x.data, MessageDeltaEvent):
                for delta in x.data.delta.content or []:
                    # We only care about text deltas, we ignore any other types of deltas
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        yield MessageContent(
                            content=delta.text.value
                            if isinstance(delta.text.value, str)
                            else "",
                            type="text",
                        )
