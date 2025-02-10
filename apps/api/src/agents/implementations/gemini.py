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
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        try:
            # Find all PDF files in directory and encode them
            for file in glob.glob(glob_with_path):
                try:
                    with open(file, "rb") as f:
                        pdfs.append(f.read())
                except IOError as e:
                    self.logger.error(f"Kon PDF bestand niet lezen: {file}. Fout: {e}")

            if not pdfs:
                self.logger.warning(f"Geen PDF bestanden gevonden in: {glob_with_path}")

            return pdfs
        except Exception as e:
            self.logger.error(f"Fout bij het laden van PDFs: {e}")
            return []

    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        """
        Verwerkt berichten en genereert antwoorden.

        Args:
            messages (List[Message]): Lijst van berichten om te verwerken

        Yields:
            TextContent: Gegenereerde tekst antwoorden
        """
        pdfs = self._load_pdfs(self.config.glob_pattern)

        self.logger.info(f"Loaded {len(pdfs)} PDFs")

        # Beter structureren van de message history
        history = []
        for message in messages[:-1]:  # Alle berichten behalve het laatste
            role = "user" if message.role == "user" else "model"
            text_contents = [
                content.content
                for content in message.content
                if isinstance(content, TextContent)
            ]

            if text_contents:  # Alleen toevoegen als er tekst content is
                history.append(
                    Content(
                        role=role, parts=[Part(text=text) for text in text_contents]
                    )
                )

        current_message = messages[-1]

        chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=GenerateContentConfig(
                system_instruction="""
Je bent een vriendelijke en behulpzame technische assistent voor metro monteurs.
Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud van Metro's.
In de documentem zie je de instructies die noodzakelijk zijn voor het uitvoeren van de onderhoudswerkzaamheden.
Begin met een overzicht van de documenten en het hoofdonderwerp.
Geef korte antwoorden en geef geen lange uitleg, de monteur gebruikt zijn mobiel.


BELANGRIJKE REGELS:
- Spreek alleen over de onderhoud, reparaties en storingen, ga niet in op andere vraagstukken
- Toon altijd de Veiligheidsinstructies die tegenkomt bij de instructies
""",
            ),
            history=history,
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
