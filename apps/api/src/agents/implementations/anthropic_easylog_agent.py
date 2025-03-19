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
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.object')) as object,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.controle[0].statusobject')) as statusobject,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens[0].framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens[0].merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens[0].type')) as type,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens[0].framehoogte')) as framehoogte,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.fiets_gegevens[0].kleur')) as kleur
                        FROM follow_up_entries
                        ORDER BY created_at DESC
                        LIMIT 100
                    """
                    self.logger.debug(f"Executing query: {query}")
                    cursor.execute(query)
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return "Geen controles gevonden"

                    results = ["🔍 Laatste controles:"]
                    for entry in entries:
                        (
                            datum,
                            object_value,
                            statusobject,
                            framenummer,
                            merk,
                            type_fiets,
                            framehoogte,
                            kleur,
                        ) = entry
                        # Pas de statusobject waarde aan
                        if statusobject == "Ja":
                            statusobject = "Akkoord"
                        elif statusobject == "Nee":
                            statusobject = "Niet akkoord"

                        # Bouw de fiets informatie op
                        fiets_info = f"Datum: {datum}, Object: {object_value}, Status object: {statusobject}"

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
