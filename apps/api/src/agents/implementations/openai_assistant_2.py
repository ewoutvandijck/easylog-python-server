from typing import List, Generator
from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock
from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent

class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str

class OpenAIAssistant2(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = OpenAI(api_key=self.get_env("OPENAI_API_KEY"))

    def _create_message_content(self, message: Message) -> List[dict]:
        return [
            {"type": content.type, "text": content.content}
            for content in message.content
        ]

    def _get_or_create_thread(self, messages: List[Message]) -> str:
        thread_id = self.get_metadata("thread_id")
        if thread_id:
            return thread_id

        thread = self.client.beta.threads.create(messages=[
            {
                "role": message.role,
                "content": self._create_message_content(message)
            }
            for message in messages
        ])
        self.set_metadata("thread_id", thread.id)
        return thread.id

    def _add_messages_to_thread(self, thread_id: str, messages: List[Message]) -> None:
        for message in messages:
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=self._create_message_content(message)
            )

    def _stream_response(self, thread_id: str, assistant_id: str) -> Generator[MessageContent, None, None]:
        stream = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=True
        )

        for event in stream:
            if isinstance(event.data, MessageDeltaEvent):
                for delta in event.data.delta.content or []:
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        text = delta.text.value if isinstance(delta.text.value, str) else ""
                        yield MessageContent(content=text, type="text")

    def on_message(self, messages: List[Message], config: OpenAIAssistantConfig) -> Generator[MessageContent, None, None]:
        """Process messages using OpenAI Assistants API and stream responses.

        Args:
            messages: List of messages to process
            config: Assistant configuration

        Yields:
            Streamed response content
        """
        assistant = self.client.beta.assistants.retrieve(config.assistant_id)
        thread_id = self._get_or_create_thread(messages)
        self._add_messages_to_thread(thread_id, messages)
        
        yield from self._stream_response(thread_id, assistant.id)