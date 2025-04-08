from collections.abc import AsyncGenerator
from typing import Any, Generic

from litellm import CustomStreamWrapper
from litellm import Message as LiteLlmMessage
from litellm.types.utils import ModelResponse

from src.agents.base_agent import BaseAgent, TConfig
from src.models.messages import (
    Message,
    MessageContent,
)


class MultiAgent(BaseAgent[TConfig], Generic[TConfig]):
    """
    An abstract base class for agents that use LiteLLM to interact with various LLM providers.
    This class handles the conversion between internal message formats and LiteLLM formats,
    but leaves the actual handle_message implementation to subclasses.

    Subclasses must implement:
    - handle_message: Send messages to the LLM provider and get the response

    Example usage:
    ```python
    class MyCustomAgent(MultiAgent[MyConfig]):
        async def handle_message(self, messages: List[LiteLlmMessage]) -> Union[ModelResponse, CustomStreamWrapper]:
            # Call LiteLLM with the appropriate model and parameters
            return await litellm.acompletion(model=self.config.model, messages=messages, stream=True)
    ```
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the MultiAgent with the provided arguments."""
        super().__init__(*args, **kwargs)
        self.logger.info(f"Initialized {self.__class__.__name__} with LiteLLM integration")

    async def on_message(self, messages: List[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        Process a list of messages and generate a response using LiteLLM.

        Args:
            messages: A list of Message objects representing the conversation history.

        Yields:
            MessageContent: The generated response content, which can be text, tool use, etc.
        """
        # Convert internal messages to LiteLLM format
        self.logger.debug(f"Converting {len(messages)} messages to LiteLLM format")
        litellm_messages = [LiteLlmMessage(**message.model_dump()) for message in messages]

        # Get the response from LiteLLM via the handle_message method (implemented by subclasses)
        self.logger.debug("Calling handle_message to get response")
        response = await self.handle_message(litellm_messages)

        # Process the response based on its type
        if isinstance(response, CustomStreamWrapper):
            # For streaming responses, yield each chunk as it arrives
            self.logger.debug("Received streaming response, processing chunks")
            async for chunk in response:
                yield chunk
        else:
            # For non-streaming responses, yield the complete response
            self.logger.debug("Received non-streaming response")
            yield response

    async def handle_message(self, messages: list[LiteLlmMessage]) -> ModelResponse | CustomStreamWrapper:
        """
        Send messages to the LLM provider using LiteLLM and get the response.

        This method must be implemented by subclasses to provide the specific logic
        for interacting with the desired LLM provider through LiteLLM.

        Args:
            messages: A list of LiteLLM Message objects.

        Returns:
            Either a ModelResponse for non-streaming responses or a CustomStreamWrapper for streaming responses.
        """
        raise NotImplementedError("handle_message must be implemented by subclasses")

    def get_litellm_params(self) -> dict[str, Any]:
        """
        Extract parameters from the agent configuration to pass to LiteLLM.

        This is a utility method that subclasses can use to extract common parameters
        from their configuration for use with LiteLLM.

        Returns:
            A dictionary of parameters for LiteLLM.
        """
        params = {}

        # Extract common parameters if they exist in the config
        if hasattr(self.config, "temperature"):
            params["temperature"] = self.config.temperature

        if hasattr(self.config, "max_tokens"):
            params["max_tokens"] = self.config.max_tokens

        if hasattr(self.config, "stream"):
            params["stream"] = self.config.stream
        else:
            # Default to streaming for better user experience
            params["stream"] = True

        # Add tools if available
        tools = self.get_tools()
        if tools:
            params["tools"] = tools

        # Add any additional parameters from the config
        if hasattr(self.config, "litellm_params") and isinstance(self.config.litellm_params, dict):
            params.update(self.config.litellm_params)

        return params
