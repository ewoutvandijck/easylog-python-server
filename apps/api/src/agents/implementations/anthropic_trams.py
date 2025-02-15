mport base64
import glob
import os
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

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
class AnthropicTramsAssistant(AnthropicAgent[AnthropicTramsAssistantConfig]):
    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[str]:
        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        # Find all PDF files in directory and encode them
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Deze functie handelt elk bericht van de gebruiker af.
        """
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Memories ophalen
        memories = self.get_metadata("memories", default=[])

        # Statistische technische kennis
        static_kennis = """
        ### Tram Onderhoud Basis ###
        - Controleer altijd eerst de veiligheid voordat je begint
        - Gebruik de juiste gereedschappen en PBM's 
        - Raadpleeg bij twijfel een senior monteur

        ### Veel voorkomende storingen ###
        - Pantograaf storingen: Controleer de pantograaf op slijtage en de afdichtingen
        """

        # Aangezien de PDF/JSON kennis functionaliteit verwijderd is, gebruiken we alleen de statische kennis.
        knowledge_base = static_kennis
        logger.info(
            f"Loaded static knowledge base with {len(knowledge_base)} characters"
        )
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
            return {
                k: v for k, v in data.items() if v is not None
            } or "Geen PQI data gevonden"

        async def tool_store_memory(memory: str):
            """
            Sla een geheugen (memory) op in de database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        tools = [
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

BELANGRIJKE REGELS:
- Vul NOOIT aan met eigen technische kennis of tips uit jouw eigen kennis
- Spreek alleen over de onderhoud en reparatie en storingen bij trams, ga niet in op andere vraagstukken
- Bij het weergeven van probleem oplossingen, doe dit 1 voor 1, stap voor stap, en vraag de monteur altijd eerst om een antwoord voor je de volgende stap bespreekt
- Als een vraag niet beantwoord kan worden, zeg dit dan duidelijk
- ### De monteur is een leerling en gebruikt een mobiel dus geef geen lange antwoorden ###
- Groet alleen aan het begin van het bericht, niet in het midden of aan het einde.

### Technische kennis
{knowledge_base}

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