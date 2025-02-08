import glob
import os
from typing import AsyncGenerator, List

from anthropic import BaseModel
from google import genai
from google.genai import types
from pydantic import Field

from src.agents.base_agent import BaseAgent
from src.models.messages import Message, TextContent


class GeminiConfig(BaseModel):
    glob_pattern: str = Field(default="pdfs/sneltram_utrecht/*.pdf")


class GeminiAssistant(BaseAgent[GeminiConfig]):
    def __init__(self, *args, **kwargs):
        self.client = genai.Client(api_key=self.get_env("GEMINI_API_KEY"))

        super().__init__(*args, **kwargs)

    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[bytes]:
        pdfs: list[bytes] = []

        # Get absolute path by joining with current file's directory
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        # Find all PDF files in directory and encode them
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(f.read())

        return pdfs

    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        pdfs = self._load_pdfs(self.config.glob_pattern)

        self.logger.info(f"Loaded {len(pdfs)} PDFs")

        last_text_content = next(
            (content for content in messages[-1].content if content.type == "text"),
            None,
        )

        if last_text_content is None:
            yield TextContent(content="")
            return

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                *[
                    types.Part.from_bytes(
                        data=pdf,
                        mime_type="application/pdf",
                    )
                    for pdf in pdfs
                ],
                last_text_content.content,
            ],
        )

        yield TextContent(content=response.text or "")
