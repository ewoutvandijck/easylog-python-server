from typing import Generator, List, Optional, Dict
from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent

class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str
    conversation_id: str  # Added to track conversations

class OpenAIAssistant(BaseAgent):
    client: OpenAI
    threads: Dict[str, str] = {}  # Store conversation_id -> thread_id mapping

    def __init__(self):
        self.client = OpenAI(
            api_key=self.get_env("OPENAI_API_KEY"),
        )

    def on_message(
        self, messages: List[Message], config: OpenAIAssistantConfig
    ) -> Generator[MessageContent, None, None]:
        assistant = self.client.beta.assistants.retrieve(config.assistant_id)
        
        # Reuse existing thread or create new one
        thread_id = self.threads.get(config.conversation_id)
        if not thread_id:
            thread = self.client.beta.threads.create(messages=[])
            self.threads[config.conversation_id] = thread.id
            thread_id = thread.id

        # Add new message to thread
        latest_message = messages[-1]
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=latest_message.role,
            content=[
                {
                    "type": content.type,
                    "text": content.content,
                }
                for content in latest_message.content
            ],
        )

        # Stream response
        for x in self.client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant.id, stream=True
        ):
            if isinstance(x.data, MessageDeltaEvent):
                for delta in x.data.delta.content or []:
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        yield MessageContent(
                            content=delta.text.value
                            if isinstance(delta.text.value, str)
                            else "",
                            type="text",
                        )