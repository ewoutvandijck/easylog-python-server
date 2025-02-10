import json
import os
import random
import time
from typing import AsyncGenerator, List, TypedDict

from pydantic import BaseModel

from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, TextContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class PQIDataHwr(TypedDict):
    """
    Defines the structure for PQI (Product Quality Inspection) data specifically for Tram components.
    """

    taak: str
    component: str
    typematerieel: str


# Vereenvoudigde config class zonder subjects
class AnthropicNewConfig(BaseModel):
    pass


# Nieuwe functie om de PDF JSON data te laden
def load_pdf_knowledge(directory: str) -> str:
    """
    Laad alle PDF JSON data als kennisdocument uit de opgegeven map.

    Args:
        directory (str): Het pad naar de directory met JSON-bestanden.

    Returns:
        str: De gecombineerde kennis tekst van alle JSON-bestanden of een melding als er niets gevonden is.
    """
    kennis_onderdelen = []
    try:
        # Loop door alle bestanden in de opgegeven directory
        for bestandsnaam in os.listdir(directory):
            if bestandsnaam.endswith(".json"):
                pad = os.path.join(directory, bestandsnaam)
                try:
                    with open(pad, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        # Voeg de inhoud toe als 'content' aanwezig is
                        if "content" in data:
                            kennis_onderdelen.append(data["content"])
                        else:
                            kennis_onderdelen.append(
                                f"In {bestandsnaam} is geen 'content' key gevonden."
                            )
                except Exception as e:
                    kennis_onderdelen.append(
                        f"Fout bij verwerken van {bestandsnaam}: {e}"
                    )
    except Exception as e:
        kennis_onderdelen.append(f"Fout bij openen van map '{directory}': {e}")

    return (
        "\n\n".join(kennis_onderdelen)
        if kennis_onderdelen
        else "Geen PDF kennis gevonden."
    )


# Vereenvoudigde agent class zonder PDF functionaliteit
class AnthropicNew(AnthropicAgent[AnthropicNewConfig]):
    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
        """
        This is the main function that handles each message from the user.
        """
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Memories ophalen
        memories = self.get_metadata("memories", default=[])

        # Statistische technische kennis
        static_kennis = """
        ### Tram Onderhoud Basis ###
        - Controleer altijd eerst de veiligheid voordat je begint
        - Gebruik de juiste gereedschappen
        - Raadpleeg bij twijfel een senior monteur
        
        ### Veel voorkomende storingen ###
        - Deuren die niet goed sluiten: Controleer eerst de rubberen afdichtingen
        - Remmen die piepen: Controleer de remblokken op slijtage
        - Airco problemen: Start met filter controle
        """

        # Laad de kennis data van de PDF JSON bestanden via de nieuwe functie
        pdf_kennis = load_pdf_knowledge("/pdfs/jsondata")

        # Combineer de statische kennis met de PDF kennis
        knowledge_base = f"{static_kennis}\n\n### PDF Kennis Document\n{pdf_kennis}"

        logger.info(f"Loaded knowledge base with {len(knowledge_base)} characters")
        logger.info(f"Memories: {memories}")

        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        def tool_get_random_number(start: int = 1, end: int = 100) -> str:
            """
            A simple tool that returns a random number between start and end.
            """
            return f"{random.randint(start, end)} ."

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
            return {
                k: v for k, v in data.items() if v is not None
            } or "Geen PQI data gevonden"

        async def tool_store_memory(memory: str):
            """
            Store a memory in the database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        tools = [
            tool_store_memory,
            tool_get_random_number,
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
