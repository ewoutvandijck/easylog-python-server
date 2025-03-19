# Python standard library imports
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

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
    Structure for Easylog data focusing on bike status and location
    """

    framenummer: str
    statusfiets: str
    actuele_locatie_fiets: str


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

    # Helper methods to get readable labels
    def _get_status_label(self, status_value):
        """Convert status code to readable label with emoji"""
        status_map = {
            "BESCHIKBAAR": "✅ BESCHIKBAAR",
            "GERESERVEERD": "🕒 GERESERVEERD",
            "IN_GEBRUIK": "🚲 IN GEBRUIK",
            "ELDERS": "🌍 ELDERS",
            "IN_ONDERHOUD": "🔧 IN ONDERHOUD",
        }
        return status_map.get(status_value, status_value)

    def _get_locatie_label(self, locatie_value):
        """Convert location code to readable label with emoji"""
        locatie_map = {
            "HPC": "🏠 HPC",
            "TRUCK": "🚛 Truck",
            "RENNER": "🏃 Bij renner",
            "TRANSPORT": "🚚 Transport",
            "ANDERS": "📍 Andere locatie",
        }
        return locatie_map.get(locatie_value, locatie_value or "Onbekend")

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

        # Define the SQL tool to fetch all bikes data
        async def tool_fetch_all_bikes(limit: int = 20):
            """
            Fetches status and location data for all bikes

            Args:
                limit: Maximum number of entries to retrieve
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) IS NOT NULL
                            AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    entries = cursor.fetchall()

                    if not entries:
                        return "Geen fietsdata gevonden"

                    results = ["🚲 Overzicht Fietsen:"]
                    for entry in entries:
                        framenummer, statusfiets, locatie, created_at = entry
                        status_label = self._get_status_label(statusfiets)
                        locatie_label = self._get_locatie_label(locatie)

                        results.append(
                            f"Framenummer: {framenummer}, Status: {status_label}, Locatie: {locatie_label}, Bijgewerkt: {created_at}"
                        )

                    return "\n".join(results)

            except Exception as e:
                return f"Error bij ophalen fietsdata: {str(e)}"

        # Define SQL tool to fetch data for a specific bike by frame number
        async def tool_fetch_bike_by_frame(framenummer: str):
            """
            Fetches status and location data for a specific bike by frame number

            Args:
                framenummer: The frame number of the bike to look up
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (framenummer,))
                    entry = cursor.fetchone()

                    if not entry:
                        return f"Geen fiets gevonden met framenummer: {framenummer}"

                    framenummer, statusfiets, locatie, created_at = entry
                    status_label = self._get_status_label(statusfiets)
                    locatie_label = self._get_locatie_label(locatie)

                    result = [
                        f"🚲 Fietsgegevens voor framenummer: {framenummer}",
                        f"Status: {status_label}",
                        f"Locatie: {locatie_label}",
                        f"Laatst bijgewerkt: {created_at}",
                    ]

                    # Fetch history for this bike
                    query_history = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                    """
                    cursor.execute(query_history, (framenummer,))
                    history = cursor.fetchall()

                    if len(history) > 1:
                        result.append("\nRecente historie:")
                        for i, hist_entry in enumerate(history):
                            if i == 0:  # Skip current status which we already displayed
                                continue
                            h_status, h_locatie, h_date = hist_entry
                            h_status_label = self._get_status_label(h_status)
                            h_locatie_label = self._get_locatie_label(h_locatie)
                            result.append(
                                f"{h_date}: Status: {h_status_label}, Locatie: {h_locatie_label}"
                            )

                    return "\n".join(result)

            except Exception as e:
                return f"Error bij ophalen fietsgegevens: {str(e)}"

        # Define available tools
        tools = [tool_fetch_all_bikes, tool_fetch_bike_by_frame]

        # Convert tools to Anthropic format
        anthropic_tools = [function_to_anthropic_tool(tool) for tool in tools]

        # Start time for logging
        start_time = time.time()

        # Create the stream with Claude
        stream = await self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system="""Je bent een vriendelijke en behulpzame fiets-beheerder voor EasyLog.
Je taak is om gebruikers te helpen bij het vinden en analyseren van fietsgegevens.

### BELANGRIJKE INFORMATIE:
Elke fiets heeft de volgende eigenschappen:
- Framenummer: Uniek identificatienummer van de fiets
- Status: Huidige status van de fiets (BESCHIKBAAR, GERESERVEERD, IN_GEBRUIK, ELDERS, IN_ONDERHOUD)
- Locatie: Waar de fiets zich nu bevindt (HPC, TRUCK, RENNER, TRANSPORT, ANDERS)

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke informatie over de fietsen
- Help de gebruiker om snel de juiste fiets te vinden
- Maak duidelijke en overzichtelijke weergaves van de data
- Wees behulpzaam en informatief

### Beschikbare tools:
- tool_fetch_all_bikes: Haalt status en locatie op voor alle fietsen
- tool_fetch_bike_by_frame: Haalt gegevens op voor een specifieke fiets op basis van framenummer
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
