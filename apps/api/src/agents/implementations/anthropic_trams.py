import base64
import glob
import os
import time
from collections.abc import AsyncGenerator
from typing import List, TypedDict

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel, Field
from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


# Definieer een TypedDict voor PQI data specifiek voor tramonderdelen
class PQIDataHwr(TypedDict):
    taak: str
    component: str
    typematerieel: str


# Definieer de structuur voor een onderwerp (subject)
class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


# Nieuwe configuratie-klasse voor de tram assistant in debug-modus.
# Hier gebruiken we de onderwerpen en instructies zoals in anthropic_trams.py.
class AnthropicTramsDebugConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="Algemeen",
                instructions=(
                    "Begin met het uitleggen welke onderwerpen/subjects je kent. Je bent een vriendelijke "
                    "en behulpzame technische assistent voor CAF TRAM monteurs. In dit onderwerp bespreek je "
                    "het in dienst nemen van de tram op basis van de documentatie. Als er LET OP in de documentatie "
                    "staat, dan deel deze informatie mee aan de monteur."
                ),
                glob_pattern="pdfs/algemeen/*.pdf",
            ),
            Subject(
                name="Storingen",
                instructions=(
                    "Help de monteur met het oplossen van TRAM storingen. Vraag of hij een nieuwe storing heeft. "
                    "Gebruik de documentatie om de monteur te helpen. GEBRUIK HET STORINGSBOEKJE VOOR DE 1E ANALYSE EN "
                    "BIJ EEN STORING. Sla de gemelde storingen en storing codes altijd op in jouw geheugen met de "
                    "tool_store_memory."
                ),
                glob_pattern="pdfs/storingen/*.pdf",
            ),
            Subject(
                name="Pantograaf",
                instructions=(
                    "Help de monteur met zijn technische TRAM werkzaamheden aan de pantograaf. Werk met de "
                    "instructies uit de documentatie van de pantograaf."
                ),
                glob_pattern="pdfs/pantograaf/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="Algemeen")


# Nieuwe agent-klasse die de debug-functionaliteit koppelt aan de tram-specifieke onderwerpen en prompt.
class AnthropicTramsDebug(AnthropicAgent[AnthropicTramsDebugConfig]):
    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[str]:
        """
        Laadt PDF-bestanden uit de gegeven glob pattern.
        """
        pdfs: list[str] = []
        # Bepaal absoluut pad t.o.v. de huidige directory van dit bestand
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)
        # Zoek alle PDF-bestanden en encodeer ze naar base64
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))
        return pdfs

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Verwerkt elk ontvangen bericht door:
          1. De berichten om te zetten naar een formaat dat Claude begrijpt.
          2. Het ophalen van het huidige onderwerp en laden van de bijbehorende PDF-bestanden.
          3. Het toevoegen van PDF-blokken aan een user-bericht (zodat Claude de documentatie kan raadplegen).
          4. Het definiëren van handige tools (zoals wisselen van onderwerp, het opslaan van core memories, enz.).
          5. Het opstellen van een systeem prompt die zowel de technische instructies als debuginformatie bevat.
        """
        # Converteer de berichten naar het Anthropic-formaat
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Ophalen van het huidige onderwerp uit metadata of gebruik het default subject
        current_subject = self.get_metadata("subject")
        if current_subject is None:
            current_subject = self.config.default_subject

        # Zoek het onderwerp in de configuratie
        subject = next(
            (s for s in self.config.subjects if s.name == current_subject), None
        )
        if subject is not None:
            current_subject_name = subject.name
            current_subject_instructions = subject.instructions
            current_subject_pdfs = self._load_pdfs(subject.glob_pattern)
        else:
            current_subject_name = current_subject
            current_subject_instructions = ""
            current_subject_pdfs = []

        # Maak PDF content blocks zodat Claude de documenten kan inlezen
        pdf_content_blocks: List[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
                "cache_control": {
                    "type": "ephemeral"
                },  # Geeft aan dat de content tijdelijk is
            }
            for pdf in current_subject_pdfs
        ]

        # Voeg de PDF-blokken toe aan het laatste user-bericht dat geen tool-resultaat bevat
        for message in reversed(message_history):
            if (
                message["role"] == "user"
                and isinstance(message["content"], list)
                and not any(
                    isinstance(content, dict) and content.get("type") == "tool_result"
                    for content in message["content"]
                )
            ):
                message["content"].extend(pdf_content_blocks)
                break

        # Haal de core memories (belangrijke opgeslagen informatie) op
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Memories: {memories}")

        # Definieer tool(s) voor het wisselen van onderwerp
        def tool_switch_subject(subject: str | None = None):
            """
            Wissel van onderwerp. Geeft een foutmelding als het onderwerp niet bestaat.
            """
            if subject is None:
                self.set_metadata("subject", None)
                return "Je bent nu terug in het algemene onderwerp."
            if subject not in [s.name for s in self.config.subjects]:
                raise ValueError(
                    f"Subject '{subject}' niet gevonden. Kies uit: {', '.join([s.name for s in self.config.subjects])}"
                )
            self.set_metadata("subject", subject)
            return f"Je bent nu overgestapt naar het onderwerp: {subject}"

        # Tool om een geheugen op te slaan
        async def tool_store_memory(memory: str):
            """
            Sla een geheugen (memory) op in de database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        # Tool om alle gespreksgeschiedenis en opgeslagen memories te wissen
        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen (core memories) en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        # Tool om PQI data op te halen
        async def tool_get_pqi_data():
            """
            Haal informatie op over het te onderhouden materieel.
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
            return {
                k: v for k, v in data.items() if v is not None
            } or "Geen PQI data gevonden"

        # Stel de tools samen die aan Claude worden aangeboden
        tools = [
            tool_switch_subject,
            tool_store_memory,
            tool_get_pqi_data,
            tool_clear_memories,
        ]

        # Meet de starttijd van de operatie
        start_time = time.time()

        # Stel de systeem prompt samen waarbij we de technische instructies, core memories en het huidige onderwerp vermelden.
        system_prompt = f"""Je bent een vriendelijke en behulpzame technische assistent voor tram monteurs.
Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud.

### BELANGRIJKE REGELS ###
- Vul NOOIT aan met eigen technische kennis of tips uit jouw eigen kennis.
- Spreek alleen over onderhoud, reparatie en storingen bij trams.
- Als een vraag niet beantwoord kan worden vanuit de documentatie, geef dit dan duidelijk aan.
- De monteur is een leerling en gebruikt een mobiel, dus geef geen lange antwoorden.

### Technische kennis
- Controleer altijd eerst de veiligheid voordat je begint.
- Gebruik de juiste gereedschappen en PBM's.
- Raadpleeg bij twijfel een senior monteur.

### Core memories
{"\n- " + "\n- ".join(memories) if memories else "Geen core memories opgeslagen"}

### Subject
Je bent nu in het onderwerp: {current_subject_name}
{current_subject_instructions}
"""

        # Start een stream met de AI (Claude) en geef de tools mee
        stream = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=message_history,
            tools=[function_to_anthropic_tool(tool) for tool in tools],
            stream=True,
        )

        # Log de verbruikte tijd
        end_time = time.time()
        logger.info(f"Time taken: {end_time - start_time} seconds")

        # Geef het antwoord van Claude stukje voor stukje terug
        async for content in self.handle_stream(stream, messages, tools):
            yield content
