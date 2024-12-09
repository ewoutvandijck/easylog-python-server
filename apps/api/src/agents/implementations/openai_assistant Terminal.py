from typing import Generator, List
import sys
import os

from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent


class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str


class OpenAIAssistant(BaseAgent):
    client: OpenAI

    def __init__(self):
        self.client = OpenAI(
            # Make sure to set the OPENAI_API_KEY environment variable
            api_key=self.get_env("OPENAI_API_KEY"),
        )

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

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    
    if not assistant_id:
        print("Error: OPENAI_ASSISTANT_ID environment variable is required")
        sys.exit(1)
    
    config = OpenAIAssistantConfig(assistant_id=assistant_id)
    agent = OpenAIAssistant()
    messages = []

    print("Chat started (type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break

        # Add user message to history
        messages.append(Message(
            role="user",
            content=[MessageContent(type="text", content=user_input)]
        ))

        # Print assistant response with streaming
        print("\nAssistant: ", end="", flush=True)
        for content in agent.on_message(messages, config):
            print(content.content, end="", flush=True)
        print()  # New line after response

        # Add assistant message to history
        messages.append(Message(
            role="assistant",
            content=[MessageContent(type="text", content="")]  # We don't store the actual content as it was streamed
        ))

if __name__ == "__main__":
    main()
