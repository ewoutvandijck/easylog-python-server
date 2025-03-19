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
                            data,
                            created_at
                        FROM follow_up_entries
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    entries = cursor.fetchall()

                    if not entries:
                        return "Geen fietsdata gevonden"

                    results = ["🚲 Wielrenfiets Informatie:"]
                    for entry in entries:
                        entry_id, data_json, created_at = entry

                        # Parse the JSON data to extract the fields
                        import json

                        try:
                            data = json.loads(data_json)
                        except:
                            self.logger.error(
                                f"Failed to parse JSON for entry {entry_id}"
                            )
                            continue

                        # Extract fields with safe get operations
                        datum = data.get("datum", "")
                        object_value = data.get("object", "")
                        controle = data.get("controle", [])
                        statusobject = (
                            controle[0].get("statusobject", "") if controle else ""
                        )

                        # Safely extract fiets_gegevens
                        fiets_gegevens = data.get("fiets_gegevens", {})
                        framenummer = fiets_gegevens.get("framenummer", "")
                        merk = fiets_gegevens.get("merk", "")
                        type_fiets = fiets_gegevens.get("type", "")
                        framehoogte = fiets_gegevens.get("framehoogte", "")
                        kleur = fiets_gegevens.get("kleur", "")

                        # Status formatting
                        if "statusfiets" in data:
                            statusfiets = data.get("statusfiets", "")
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
                        else:
                            status_formatted = ""

                        # Format status object
                        if statusobject == "Ja":
                            statusobject = "Akkoord"
                        elif statusobject == "Nee":
                            statusobject = "Niet akkoord"

                        # Location formatting
                        if "actuele_locatie_fiets" in data:
                            actuele_locatie = data.get("actuele_locatie_fiets", "")
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
                        else:
                            locatie_formatted = ""

                        # Build the fiets_info string
                        fiets_info = []
                        if entry_id:
                            fiets_info.append(f"ID: {entry_id}")
                        if datum:
                            fiets_info.append(f"Datum: {datum}")
                        if object_value:
                            fiets_info.append(f"Object: {object_value}")
                        if status_formatted:
                            fiets_info.append(f"Status: {status_formatted}")
                        if locatie_formatted:
                            fiets_info.append(f"Locatie: {locatie_formatted}")
                        if statusobject:
                            fiets_info.append(f"Status object: {statusobject}")

                        # Base info string
                        info_string = ", ".join(fiets_info)

                        # Voeg fietsgegevens toe als ze beschikbaar zijn
                        specs = []
                        if framenummer:
                            specs.append(f"Framenummer: {framenummer}")
                        if merk:
                            specs.append(f"Merk: {merk}")
                        if type_fiets:
                            specs.append(f"Type: {type_fiets}")
                        if framehoogte:
                            specs.append(f"Framehoogte: {framehoogte}")
                        if kleur:
                            specs.append(f"Kleur: {kleur}")

                        if specs:
                            info_string += f" | {', '.join(specs)}"

                        results.append(info_string)

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
