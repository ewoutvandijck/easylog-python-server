# Python standard library imports
import time
from collections.abc import AsyncGenerator
from typing import Optional, TypedDict

# Third-party imports
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool

# Laad alle variabelen uit .env
load_dotenv()


class EasylogData(TypedDict):
    """
    Structure for Easylog data focusing on bike information
    """

    statusfiets: Optional[str]  # Status van de fiets (BESCHIKBAAR, GERESERVEERD, etc.)
    actuele_locatie_fiets: Optional[str]  # Locatie van de fiets (HPC, TRUCK, etc.)
    framenummer: Optional[str]  # Uniek nummer van het frame
    merk: Optional[str]  # Merk van de fiets
    type: Optional[str]  # Type fiets
    framehoogte: Optional[str]  # Hoogte van het frame
    kleur: Optional[str]  # Kleur van de fiets


# Configuration class for AnthropicEasylog agent
class AnthropicEasylogAgentConfig(BaseModel):
    max_entries: int = Field(
        default=100,
        description="Maximum number of entries to fetch from the database",
    )
    debug_mode: bool = Field(
        default=False, description="Enable debug mode with additional logging"
    )


# Agent class that integrates with Anthropic's Claude API for EasyLog data analysis
class AnthropicEasylogAgent(AnthropicAgent[AnthropicEasylogAgentConfig]):
    def __init__(self, *args, **kwargs) -> None:
        # Call the parent class init
        super().__init__(*args, **kwargs)

        # Extra logging
        self.available_tools = []
        self.logger.info("EasylogAgent initialized with basic SQL tool")

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Handles messages from the user and returns AI responses
        """
        # Log the incoming message for debugging
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == "user" and isinstance(last_message.content, str):
                self.logger.info(
                    f"Processing user message: {last_message.content[:100]}..."
                )

        # Convert messages to a format Claude understands
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Define the SQL tool to fetch data
        async def tool_fetch_follow_up_entries(limit: int = 20):
            """
            Fetch bike data from follow_up_entries table

            Args:
                limit: Maximum number of entries to retrieve
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            id,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens.merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens.type')) as type,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens.framehoogte')) as framehoogte,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens.kleur')) as kleur,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_EXTRACT(data, '$.statusfiets') IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    entries = cursor.fetchall()

                    if not entries:
                        return "Geen fietsdata gevonden"

                    results = ["🚲 Wielrenfiets Informatie:"]
                    for entry in entries:
                        (
                            entry_id,
                            statusfiets,
                            actuele_locatie,
                            framenummer,
                            merk,
                            type_fiets,
                            framehoogte,
                            kleur,
                            created_at,
                        ) = entry

                        # Format status met emoji's
                        status_formatted = statusfiets
                        if statusfiets == "BESCHIKBAAR":
                            status_formatted = "✅ BESCHIKBAAR"
                        elif statusfiets == "GERESERVEERD":
                            status_formatted = "🕒 GERESERVEERD"
                        elif statusfiets == "IN_GEBRUIK":
                            status_formatted = "🚲 IN GEBRUIK"
                        elif statusfiets == "ELDERS":
                            status_formatted = "🌍 ELDERS"
                        elif statusfiets == "IN_ONDERHOUD":
                            status_formatted = "🔧 IN ONDERHOUD"

                        # Format locatie met emoji's
                        locatie_formatted = actuele_locatie
                        if actuele_locatie == "HPC":
                            locatie_formatted = "🏠 HPC"
                        elif actuele_locatie == "TRUCK":
                            locatie_formatted = "🚛 Truck"
                        elif actuele_locatie == "RENNER":
                            locatie_formatted = "🏃 Bij renner"
                        elif actuele_locatie == "TRANSPORT":
                            locatie_formatted = "🚚 Transport"
                        elif actuele_locatie == "ANDERS":
                            locatie_formatted = "📍 Andere locatie"

                        fiets_info = f"ID: {entry_id}, Status: {status_formatted}, Locatie: {locatie_formatted}"

                        # Voeg fietsgegevens toe als ze beschikbaar zijn
                        specs = []
                        if framenummer and framenummer.lower() != "null":
                            specs.append(f"Framenummer: {framenummer}")
                        if merk and merk.lower() != "null":
                            specs.append(f"Merk: {merk}")
                        if type_fiets and type_fiets.lower() != "null":
                            specs.append(f"Type: {type_fiets}")
                        if framehoogte and framehoogte.lower() != "null":
                            specs.append(f"Framehoogte: {framehoogte}")
                        if kleur and kleur.lower() != "null":
                            specs.append(f"Kleur: {kleur}")

                        if specs:
                            fiets_info += f" | {', '.join(specs)}"

                        results.append(fiets_info)

                    return "\n".join(results)

            except Exception as e:
                self.logger.error(f"Error fetching bike data: {str(e)}")
                return f"Error bij ophalen fietsgegevens: {str(e)}"

        # Define available tools
        tools = [tool_fetch_follow_up_entries]

        # Convert tools to Anthropic format
        anthropic_tools = [function_to_anthropic_tool(tool) for tool in tools]

        # Start time for logging
        start_time = time.time()

        # Create the stream with Claude
        stream = await self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system="""Je bent een vriendelijke en behulpzame data-analist voor EasyLog.
Je taak is om gebruikers te helpen bij het analyseren van bedrijfsgegevens.

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke samenvattingen van de EasyLog data
- Help de gebruiker patronen te ontdekken in de gegevens
- Maak duidelijke en professionele weergaves van de data
- Wees behulpzaam en informatief

### Beschikbare tools:
- tool_fetch_follow_up_entries: Haalt entries op uit de follow_up_entries tabel
            """,
            messages=message_history,
            tools=anthropic_tools,
            stream=True,
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        # Stream the response
        async for content in self.handle_stream(stream, tools):
            yield content
