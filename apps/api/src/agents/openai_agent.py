from typing import AsyncGenerator, Generic

from openai import AsyncOpenAI, AsyncStream
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock

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
            api_key=self.get_env("OPENAI_API_KEY"),
        )

    async def handle_stream(
        self,
        stream: AsyncStream[AssistantStreamEvent],
    ) -> AsyncGenerator[TextContent, None]:
        async for event in stream:
            if isinstance(event.data, MessageDeltaEvent):
                for delta in event.data.delta.content or []:
                    # We only care about text deltas, we ignore any other types of deltas for now
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        yield TextContent(
                            content=delta.text.value
                            if isinstance(delta.text.value, str)
                            else "",
                            type="text",
                        )
