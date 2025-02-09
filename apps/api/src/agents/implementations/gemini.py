import glob
import os
from typing import AsyncGenerator, List, cast

from anthropic import BaseModel
from google import genai
from google.genai.types import (
    Content,
    GenerateContentConfig,
    GenerateContentResponse,
    Part,
)
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

        current_message = messages[-1]
        previous_messages = messages[:-1]

        chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=GenerateContentConfig(
                system_instruction="""
Je bent een vriendelijke en behulpzame technische assistent voor tram en metro monteurs.
Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud.
In het document zie je de instructies die noodzakelijk zijn voor het uitvoeren van onderhoud of probleem oplossingen.
Toon altijd de Veiligheidsinstructies die tegenkomt.
Geef korte antwoorden en geef geen lange uitleg, de monteur gebruikt zijn mobiel.


BELANGRIJKE REGELS:
- Spreek alleen over de onderhoud en reparatie en storingen bij trams, ga niet in op andere vraagstukken

""",
            ),
            history=[
                *[
                    Content(
                        role="user" if message.role == "user" else "model",
                        parts=[
                            Part(
                                text=content.content,
                            )
                            for content in message.content
                            if isinstance(content, TextContent)
                        ],
                    )
                    for message in previous_messages
                ],
            ],
        )

        for chunk in chat.send_message_stream(
            message=[
                *[
                    Part.from_bytes(
                        data=pdf,
                        mime_type="application/pdf",
                    )
                    for pdf in pdfs
                ],
                *[
                    Part(
                        text=content.content,
                    )
                    for content in current_message.content
                    if isinstance(content, TextContent)
                ],
            ],
        ):
            chunk = cast(GenerateContentResponse, chunk)
            if chunk.text:
                yield TextContent(content=chunk.text)
