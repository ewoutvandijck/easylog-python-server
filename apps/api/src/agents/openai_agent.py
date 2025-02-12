from typing import AsyncGenerator, Generic, List, cast

from openai import AsyncOpenAI, AsyncStream
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

from src.agents.base_agent import BaseAgent, TConfig
from src.models.messages import (
    Message,
    MessageContent,
    TextContent,
    TextDeltaContent,
)


class OpenAIAgent(BaseAgent[TConfig], Generic[TConfig]):
    """
    A friendly AI assistant that talks to OpenAI's AI model.
    Think of this as a translator between your app and OpenAI.

    What can this assistant do?
    1. Connect to OpenAI (like making a phone call to a smart friend)
    2. Send your messages to OpenAI and get responses back
    3. Use special tools when needed (like a calculator or search engine)
    4. Get responses piece by piece (like reading a message as someone types it)

    Simple example:
        # Create your AI assistant
        agent = OpenAIAgent()

        # Ask it a question and wait for the response
        response = await agent.on_message(["What's the weather like?"])
    """

    # Store the connection to Anthropic's API
    client: AsyncOpenAI

    def __init__(self, *args, **kwargs):
        """
        Sets up the agent with necessary connections and settings.

        This is like preparing a workstation:
        1. Set up basic tools (from BaseAgent)
        2. Establish connection to Claude (Anthropic's API)
        """
        # Initialize the basic agent features
        super().__init__(*args, **kwargs)

        # Create a connection to Anthropic using our API key
        # This is like logging into a special service
        self.client = AsyncOpenAI(
            api_key=self.get_env("OPENAI_API_KEY"),
        )

    async def handle_assistant_stream(
        self,
        stream: AsyncStream[AssistantStreamEvent],
    ) -> AsyncGenerator[MessageContent, None]:
        text_content = ""
        async for event in stream:
            if isinstance(event.data, MessageDeltaEvent):
                for delta in event.data.delta.content or []:
                    # We only care about text deltas, we ignore any other types of deltas for now
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        content = (
                            delta.text.value
                            if isinstance(delta.text.value, str)
                            else ""
                        )
                        yield TextDeltaContent(
                            content=content,
                        )
                        text_content += content

        yield TextContent(content=text_content)

    async def handle_completions_stream(
        self, stream: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[TextContent, None]:
        async for event in stream:
            self.logger.info(
                f"Received completion chunk: {event.choices[0].delta.content}"
            )

            if event.choices[0].delta.content is not None:
                yield TextContent(
                    content=event.choices[0].delta.content or "",
                    type="text",
                )

    def _convert_messages_to_openai_messages(
        self, messages: List[Message]
    ) -> List[ChatCompletionMessageParam]:
        return cast(
            List[ChatCompletionMessageParam],
            [
                {
                    "role": message.role,
                    "content": [
                        {
                            "type": "text",
                            "text": content.content,
                        }
                        for content in message.content
                        if isinstance(content, TextContent)
                    ],
                }
                for message in messages
            ],
        )
