from collections.abc import AsyncGenerator
from typing import Generic

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from src.agents.base_agent import BaseAgent, TConfig
from src.models.messages import (
    TextContent,
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
            api_key=self.get_env("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    async def handle_stream(self, stream: AsyncStream[ChatCompletionChunk]) -> AsyncGenerator[TextContent, None]:
        async for event in stream:
            self.logger.info(f"Received completion chunk: {event.choices[0].delta.content}")

            if event.choices[0].delta.content is not None:
                yield TextContent(
                    content=event.choices[0].delta.content or "",
                    type="text",
                )

    async def handle_completion(self, completion: ChatCompletion) -> AsyncGenerator[TextContent, None]:
        yield TextContent(
            content=completion.choices[0].message.content or "",
            type="text",
        )
