import base64
import glob
import os
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel, Field

from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class PQIDataHwr(TypedDict):
    """
    Defines the structure for PQI (Product Quality Inspection) data specifically for Tram components
    """

    taak: str
    component: str
    typematerieel: str


# Configuration class for AnthropicNew agent
# Specifies the directory path where PDF files are stored


class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


class AnthropicTramsAssistantConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="Algemeen",
                instructions="Begin met het uitleggen welke onderwerpen/subjects je kent. Je bent een vriendelijke en behulpzame technische assistent voor CAF TRAM monteurs. In dit onderwerp bespreek je het in dienst nemen van de tram op basis van de documentatie. Als er LET OP in de documentatie staat, dan deel deze informatie mee aan de monteur.",
                glob_pattern="pdfs/algemeen/*.pdf",
            ),
            Subject(
                name="Storingen",
                instructions="Help de monteur met het oplossen van TRAM storingen. Vraag of hij een nieuwe storing heeft. Gebruik de documentatie om de monteur te helpen. GEBRUIK HET STORINGSBOEKJE VOOR DE 1E ANALYSE EN BIJ EEN STORING.  Sla de gemelde storingen en storing codes altijd op in jouw geheugen met de tool_store_memory.",
                glob_pattern="pdfs/storingen/*.pdf",
            ),
            Subject(
                name="Pantograaf",
                instructions="Help de monteur met zijn technische TRAM werkzaamheden aan de pantograaf. Werk met de instructies uit de documentatie van de pantograaf.",
                glob_pattern="pdfs/pantograaf/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="Algemeen")


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class AnthropicTrams(AnthropicAgent[AnthropicTramsAssistantConfig]):
    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[str]:
        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        # Find all PDF files in directory and encode them
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        Deze functie handelt elk bericht van de gebruiker af.
        """
        # Convert messages to a format Claude understands
        # This is like translating from one language to another
        message_history = self._convert_messages_to_anthropic_format(messages)

        # The get and set metadata functions are used to store and retrieve information between messages
        current_subject = self.get_metadata("subject")
        if current_subject is None:
            current_subject = self.config.default_subject

        subject = next((s for s in self.config.subjects if s.name == current_subject), None)

        if subject is not None:
            current_subject_name = subject.name
            current_subject_instructions = subject.instructions
            current_subject_pdfs = self._load_pdfs(subject.glob_pattern)
        else:
            current_subject_name = current_subject
            current_subject_instructions = ""
            current_subject_pdfs = []

        # Create special blocks for each PDF that Claude can read
        # This is like creating a digital package for each PDF
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
                "cache_control": {"type": "ephemeral"},  # Tells Claude this is temporary.
                "citations": {"enabled": True},
            }
            for pdf in current_subject_pdfs
        ]

        # Claude won't respond to tool results if there is a PDF in the message.
        # So we add the PDF to the last user message that doesn't contain a tool result.
        for message in reversed(message_history):
            if (
                message["role"] == "user"  # Only attach PDFs to user messages
                and isinstance(message["content"], list)  # Content must be a list to extend
                and not any(
                    isinstance(content, dict) and content.get("type") == "tool_result" for content in message["content"]
                )  # Skip messages that contain tool results
            ):
                # Add PDF content blocks to eligible messages
                # This ensures Claude can reference PDFs when responding to user queries
                message["content"].extend(pdf_content_blocks)
                break

        # Memories ophalen
        memories = self.get_metadata("memories", default=[])

        logger.info(f"Memories: {memories}")

        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        async def tool_get_pqi_data():
            """
            Haalt de PQI data op uit de datasource voor HWR 450.
            """
            pqi_data = await self.backend.get_datasource_entry(
                datasource_slug="pqi-data-tram",
                entry_id="443",
                data_type=PQIDataHwr,
            )

            data = {
                "taak": pqi_data.data["taak"],
                "component": pqi_data.data["component"],
                "typematerieel": pqi_data.data["typematerieel"],
            }

            # Return the pqi data or an error message if it's not found
            return {k: v for k, v in data.items() if v is not None} or "Geen PQI data gevonden"

        async def tool_store_memory(memory: str):
            """
            Sla een geheugen (memory) op in de database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        # NIEUW: Tool toevoegen om van onderwerp te wisselen
        def tool_switch_subject(subject: str | None = None):
            if subject is None:
                self.set_metadata("subject", None)
                return "Terug naar algemeen onderwerp"

            if subject not in [s.name for s in self.config.subjects]:
                raise ValueError(f"Ongeldig onderwerp. Kies uit: {', '.join([s.name for s in self.config.subjects])}")

            self.set_metadata("subject", subject)
            return f"Onderwerp gewijzigd naar: {subject}"

        tools = [
            tool_switch_subject,  # NIEUW
            tool_store_memory,
            tool_get_pqi_data,
            tool_clear_memories,
        ]

        start_time = time.time()

        stream = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=f"""Je bent een vriendelijke en behulpzame technische assistent voor tram monteurs.
Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud.

Alle onderwerpen: {", ".join([s.name for s in self.config.subjects])}
Actueel onderwerp: {current_subject_name}
Huidige instructies: {current_subject_instructions}


### BELANGRIJKE REGELS:
- Vul NOOIT aan met eigen technische kennis
- Spreek alleen over tram onderhoud en storingen
- Stap-voor-stap uitleg geven
- Korte antwoorden voor mobiel gebruik

### Tram Onderhoud Basis ###
- Controleer altijd eerst de veiligheid voordat je begint
- Gebruik de juiste gereedschappen en PBM's 
- Raadpleeg bij twijfel een senior monteur

### Veel voorkomende storingen ###
- Pantograaf storingen: Controleer de pantograaf op slijtage en de afdichtingen

### Core memories
{"\n-".join(memories)}
            """,
            messages=message_history,
            tools=[function_to_anthropic_tool(tool) for tool in tools],
            stream=True,
        )

        end_time = time.time()
        logger.info(f"Time taken: {end_time - start_time} seconds")

        async for content in self.handle_stream(
            stream,
            messages,
            tools,
        ):
            yield content
