import base64
import glob
import os
import time
from typing import AsyncGenerator, List

from anthropic import AsyncAnthropic
from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from anthropic.types.beta.beta_message_param import BetaMessageParam
from anthropic.types.beta.beta_text_block_param import BetaTextBlockParam
from pydantic import Field

from src.agents.base_agent import AgentConfig, BaseAgent
from src.logger import logger
from src.models.messages import Message, MessageContent


# Configuration class for AnthropicWithPDF agent
# Specifies the directory path where PDF files are stored
class AnthropicWithPDFConfig(AgentConfig):
    pdfs_path: str = Field(default="pdfs")


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class AnthropicWithPDF(BaseAgent):
    # Anthropic client instance for making API calls
    client: AsyncAnthropic

    def __init__(self, *args, **kwargs):
        # Initialize parent BaseAgent class
        super().__init__(*args, **kwargs)

        # Initialize Anthropic client with API key from environment
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    def _load_pdfs(self, path: str = "pdfs") -> list[str]:
        """
        Loads and base64 encodes all PDF files from the specified directory.

        Args:
            path (str): Directory path containing PDF files. Defaults to "./pdfs"

        Returns:
            list[str]: List of base64 encoded PDF contents
        """

        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        path = os.path.join(os.path.dirname(__file__), path)

        # Find all PDF files in directory and encode them
        for file in glob.glob(f"{path}/*.pdf"):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(
        self, messages: List[Message], config: AnthropicWithPDFConfig
    ) -> AsyncGenerator[MessageContent, None]:
        # Load PDFs from the configured path
        pdfs = self._load_pdfs(config.pdfs_path)

        # Get all messages except the most recent one
        previous_messages = messages[:-1]

        # Convert previous messages into Anthropic's BetaMessageParam format
        # Each message contains role (user/assistant) and content blocks
        message_history: list[BetaMessageParam] = [
            {
                "role": message.role,
                "content": [
                    {
                        "type": "text",
                        "text": content.content,
                    }
                    for content in message.content
                    if content.content
                ],
            }
            for message in previous_messages
            if message.content
        ]

        # Get the content of the most recent message
        current_message = messages[-1].content

        # Create PDF content blocks for each loaded PDF
        # These will be sent to Claude as base64-encoded documents
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
            }
            for pdf in pdfs
        ]

        # Convert the current message content into text blocks
        text_content_blocks: list[BetaTextBlockParam] = [
            {
                "type": "text",
                "text": content.content,
            }
            for content in current_message
        ]

        # Print performance
        start_time = time.time()

        # Create a streaming message request to Claude
        # This includes the message history, PDFs, and current message
        stream = await self.client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            betas=["pdfs-2024-09-25"],  # Enable PDF support
            max_tokens=1024,
            messages=[
                *message_history,
                {
                    "role": "user",
                    "content": [
                        *pdf_content_blocks,  # First send PDFs
                        *text_content_blocks,  # Then send text content
                    ],
                },
            ],
            stream=True,
        )

        end_time = time.time()
        logger.info(f"Time taken: {end_time - start_time} seconds")

        # Process the streaming response
        # Yield text content as it arrives from Claude
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield MessageContent(content=event.delta.text)
