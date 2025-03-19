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
    Simple structure for Easylog data focusing on bike status
    """

    statusfiets: str


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
            Simple tool to fetch basic data from follow_up_entries table

            Args:
                limit: Maximum number of entries to retrieve
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            id,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            created_at
                        FROM follow_up_entries
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    entries = cursor.fetchall()

                    if not entries:
                        return "Geen data gevonden"

                    results = ["EasyLog Data (statusfiets):"]
                    for entry in entries:
                        entry_id, statusfiets, created_at = entry
                        results.append(
                            f"ID: {entry_id}, Statusfiets: {statusfiets}, Created: {created_at}"
                        )

                    return "\n".join(results)

            except Exception as e:
                return f"Error: {str(e)}"

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
