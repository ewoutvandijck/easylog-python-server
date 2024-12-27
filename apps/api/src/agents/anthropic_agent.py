import base64
from glob import glob
from typing import AsyncGenerator, Callable, List

from anthropic import AsyncAnthropic, AsyncStream
from anthropic.types.raw_message_stream_event import RawMessageStreamEvent

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent


class AnthropicAgent(BaseAgent):
    # Anthropic client instance for making API calls
    client: AsyncAnthropic
    pdfs: list[str] = []

    def __init__(self, *args, **kwargs):
        # Initialize parent BaseAgent class
        super().__init__(*args, **kwargs)

        # Initialize Anthropic client with API key from environment
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    async def handle_stream(
        self,
        stream: AsyncStream[RawMessageStreamEvent],
        messages: List[Message],
        agent_config: AgentConfig,
    ) -> AsyncGenerator[MessageContent, None]:
        current_index = 0
        text_blocks: list[str] = []
        json_blocks: list[tuple[str, str]] = []
        async for event in stream:
            if (
                event.type == "content_block_start"
                and event.content_block.type == "text"
            ):
                text_blocks.append(event.content_block.text)
            elif (
                event.type == "content_block_start"
                and event.content_block.type == "tool_use"
            ):
                json_blocks.append((event.content_block.name, ""))
            elif event.type == "content_block_stop":
                current_index += 1
            elif (
                event.type == "content_block_delta" and event.delta.type == "text_delta"
            ):
                text_blocks[current_index] += event.delta.text
                yield MessageContent(content=event.delta.text, index=current_index)
            elif (
                event.type == "content_block_delta"
                and event.delta.type == "input_json_delta"
            ):
                json_blocks[current_index] = (
                    json_blocks[current_index][0],
                    json_blocks[current_index][1] + event.delta.partial_json,
                )
            elif (
                event.type == "message_delta" and event.delta.stop_reason == "tool_use"
            ):
                function_name, json_str = json_blocks[current_index]
                function = getattr(self, function_name)
                function_result = function(json_str)

                new_messages = messages.copy()
                new_messages.append(
                    Message(
                        role="assistant",
                        content=[
                            MessageContent(content=function_result, index=current_index)
                        ],
                    )
                )

                async for content in self.on_message(new_messages, agent_config):
                    yield content

    def tools(self) -> list[Callable]:
        return [
            self.list_pdfs,
            self.load_pdf,
        ]

    def list_pdfs(self, path: str) -> list[str]:
        """
        List all PDF files in the specified directory
        """
        return glob.glob(f"{path}/*.pdf")

    def load_pdf(self, file: str) -> str:
        """
        Load a PDF file into a base64 encoded string
        """
        with open(file, "rb") as f:
            self.pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))
            return f"PDF loaded successfully: {file}"
