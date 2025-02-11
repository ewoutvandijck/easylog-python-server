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


# De functie voor het laden van PDF JSON data is verwijderd omdat we geen PDF/JSON functionaliteit meer willen.


# Vereenvoudigde agent class zonder PDF functionaliteit
class AnthropicNew(AnthropicAgent[AnthropicNewConfig]):
    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
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
        - Gebruik de juiste gereedschappen
        - Raadpleeg bij twijfel een senior monteur
        
        ### Veel voorkomende storingen ###
        - Deuren die niet goed sluiten: Controleer eerst de rubberen afdichtingen
        - Remmen die piepen: Controleer de remblokken op slijtage
        - Airco problemen: Start met filter controle
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

        def tool_get_random_number(start: int = 1, end: int = 100) -> str:
            """
            Een eenvoudige tool die een willekeurig getal retourneert tussen start en end.
            """
            return f"{random.randint(start, end)}."

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
            Sla een geheugen (memory) op in de database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        async def tool_get_pdf_data():
            """
            Haalt PDF data op en formatteert deze leesbaar voor de assistant.
            """
            try:
                pdf_data = await self.backend.get_datasource_entry(
                    datasource_slug="pdf-extracts",
                    entry_id="hwr-doc-12",
                    data_type=dict,
                )

                formatted_text = []
                current_section = ""

                for element in pdf_data.get("elements", []):
                    # Filter alleen Nederlandse tekst
                    if element.get("Lang") != "nl":
                        continue

                    text = element.get("Text", "").strip()
                    if not text:
                        continue

                    # Herken titels op basis van lettergrootte en vetgedrukt
                    if element["Font"]["weight"] > 600 and element["TextSize"] > 12:
                        if current_section:
                            formatted_text.append(current_section)
                        current_section = f"\n# {text}\n"
                    else:
                        current_section += f"{text}\n"

                return "\n".join(formatted_text) or "Geen leesbare PDF data gevonden"

            except Exception as e:
                logger.error(f"PDF parse error: {str(e)}")
                return "Kon PDF document niet laden"

        tools = [
            tool_store_memory,
            tool_get_random_number,
            tool_get_pqi_data,
            tool_clear_memories,
            tool_get_pdf_data,
        ]

        start_time = time.time()

        stream = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=f"""Je bent een vriendelijke en behulpzame technische assistent voor tram monteurs.
Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud.

BELANGRIJKE REGELS:
- Combineer de technische kennis met informatie uit de PDF documentatie waar relevant
- Verwijs naar hoofdstuknummers en sectietitels uit de PDF waar mogelijk

### Technische kennis
{knowledge_base}

### PDF Documentatie (Hoofdstuk 12):
{await tool_get_pdf_data()}

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
