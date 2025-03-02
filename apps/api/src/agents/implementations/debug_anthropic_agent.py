import base64
import json
import time
import traceback  # Toegevoegd voor betere logging
from collections.abc import AsyncGenerator

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel, Field

from src.agents.anthropic_agent import AnthropicAgent
from src.agents.tools.planning_tools import PlanningTools
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class DebugAnthropicAgentConfig(BaseModel):
    tool_result_max_length: int = Field(default=2000)


class ActivePDF(BaseModel):
    file_data: bytes
    summary: str
    long_summary: str
    markdown_content: str


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class DebugAnthropicAgent(AnthropicAgent[DebugAnthropicAgentConfig]):
    _active_pdf: ActivePDF | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger.info("DebugAnthropicAgent initialisatie gestart")
        self._planning_tools = PlanningTools(self.easylog_backend)
        self.logger.info(f"Planning tools geladen: {len(self._planning_tools.all_tools)} tools beschikbaar")

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        This is the main function that handles each message from the user.!
        It processes the message, looks up relevant information, and generates a response.

        Step by step, this function:
        1. Loads all PDFs from the specified folder
        2. Converts previous messages into a format Claude understands
        3. Prepares the PDF contents to be sent to Claude
        4. Sets up helpful tools that Claude can use
        5. Sends everything to Claude and gets back a response

        Example usage:
            agent = AnthropicFirst()
            config = AnthropicFirstConfig(pdfs_path="./pdfs")
            messages = [Message(content="How do I fix the brake system?")]

            async for response in agent.on_message(messages, config):
                print(response)  # Prints each part of the AI's response as it's generated

        Args:
            messages: List of previous messages in the conversation
            config: Settings for the agent, including where to find PDFs

        Returns:
            An async generator that yields parts of the AI's response as they're generated
        """
        self.logger.info(f"on_message aangeroepen met {len(messages)} berichten")

        try:
            # Convert messages to a format Claude understands
            message_history = self._convert_messages_to_anthropic_format(messages)
            self.logger.info(f"Bericht geschiedenis geconverteerd naar Anthropic formaat")

            # Create special blocks for each PDF that Claude can read
            pdf_content_block: BetaBase64PDFBlockParam | None = (
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(self._active_pdf.file_data).decode("utf-8"),
                    },
                    "cache_control": {"type": "ephemeral"},
                }
                if self._active_pdf
                else None
            )

            # Claude won't respond to tool results if there is a PDF in the message.
            for message in reversed(message_history):
                if (
                    pdf_content_block is not None
                    and message["role"] == "user"
                    and isinstance(message["content"], list)
                    and not any(
                        isinstance(content, dict) and content.get("type") == "tool_result" for content in message["content"]
                    )
                ):
                    message["content"].append(pdf_content_block)
                    break

            # Memories 
            memories = self.get_metadata("memories", default=[])
            self.logger.info(f"Memories geladen: {len(memories)}")

            # Define helper tools
            async def tool_search_pdf(query: str) -> str:
                """
                Search for a PDF in the knowledge base.
                """
                self.logger.info(f"PDF zoeken met query: {query}")
                knowledge_result = await self.search_knowledge(query)

                if (
                    knowledge_result is None
                    or knowledge_result.object is None
                    or knowledge_result.object.name is None
                    or knowledge_result.object.bucket_id is None
                ):
                    self.logger.warning(f"Geen PDF gevonden voor query: {query}")
                    return "Geen PDF gevonden"

                self.logger.info(f"PDF gevonden: {knowledge_result.id}")
                return json.dumps(
                    {
                        "id": knowledge_result.id,
                        "markdown_content": knowledge_result.markdown_content,
                    }
                )

            async def tool_load_image(_id: str, file_name: str) -> str:
                """
                Load an image from the database.
                """
                self.logger.info(f"Afbeelding laden: {_id}/{file_name}")
                image_data = await self.load_image(_id, file_name)
                self.logger.info(f"Afbeelding geladen: {len(image_data)} bytes")
                return f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

            async def tool_store_memory(memory: str) -> str:
                """
                Store a memory in the database.
                """
                self.logger.info(f"Memory opslaan: {memory}")
                current_memory = self.get_metadata("memories", default=[])
                current_memory.append(memory)
                self.set_metadata("memories", current_memory)
                return "Memory stored"

            def tool_clear_memories() -> str:
                """
                Clear all stored memories and the conversation history.
                """
                self.logger.info(f"Alle memories wissen")
                self.set_metadata("memories", [])
                return "All memories and the conversation history have been cleared."

            # Speciale wrapper voor planning tools om problemen te loggen
            async def log_planning_tool_errors(tool_func, *args, **kwargs):
                try:
                    return await tool_func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Fout in planning tool {tool_func.__name__}: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return f"Fout bij uitvoeren van {tool_func.__name__}: {str(e)}"

            # Wrap alle planning tools voor betere logging
            wrapped_planning_tools = []
            for tool in self._planning_tools.all_tools:
                # We maken een closure voor elke tool om de referentie vast te leggen
                async def make_wrapped_tool(original_tool=tool):
                    async def wrapped_tool(*args, **kwargs):
                        self.logger.info(f"Planning tool aanroepen: {original_tool.__name__} met args: {args}, kwargs: {kwargs}")
                        try:
                            result = await original_tool(*args, **kwargs)
                            # Log een korte versie van het resultaat
                            result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                            self.logger.info(f"Planning tool {original_tool.__name__} resultaat: {result_preview}")
                            return result
                        except Exception as e:
                            self.logger.error(f"Fout in planning tool {original_tool.__name__}: {str(e)}")
                            self.logger.error(traceback.format_exc())
                            raise  # Laat de fout doorgaan zodat Claude weet dat er iets mis is gegaan
                    
                    # Kopieer de metadata van de originele functie
                    wrapped_tool.__name__ = original_tool.__name__
                    wrapped_tool.__doc__ = original_tool.__doc__
                    wrapped_tool.__annotations__ = original_tool.__annotations__
                    return wrapped_tool
                
                wrapped_planning_tools.append(await make_wrapped_tool())

            tools = [
                tool_search_pdf,
                tool_store_memory,
                tool_clear_memories,
                tool_load_image,
                *wrapped_planning_tools,  # Gebruik de wrapped versies
            ]

            self.logger.info(f"{len(tools)} tools geregistreerd voor Claude")

            # Start measuring how long the operation takes
            start_time = time.time()
            self.logger.info("Claude API aanroepen")

            # Create a streaming message request to Claude
            stream = await self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2048,
                system=f"""Je bent een behulpzame planning assistent die gebruikers helpt bij het beheren van projecten, fases en resources in EasyLog.

### Wat je kunt doen ####
- Projecten bekijken, aanmaken en bijwerken
- Projectfases plannen en aanpassen
- Je kunt Voertuigen, medewerkers of objecten toewijzen aan projecten
- Planning visualiseren en optimaliseren
- Conflicten in planning identificeren en oplossen

### Hoe je helpt an antwoord ###
- Gebruik tabellen en symbols in de weergave van planningen
- Gebruik niet de wprden ID's, Resources of allocations in jouw antwoorden 
- ID's mag je negeren
- Resources zijn objecten, medewerkers of voertuigen.
- Allocaties zijn planningen die gemaakt zijn voor een resource.
- Doorlopende projecten zijn losse dagen die gepland worden, geef deze niet weer in het project overzicht maar bij Verlof en Service en Maintenance dagen.
- Geef praktische suggesties voor efficiënte resourceallocatie
- Assisteer bij het organiseren van projectfases
- Bied inzicht in beschikbare resources en hun capaciteiten

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, of een belangrijke gebeurtenis heeft meegemaakt, of een belangrijke informatie heeft geleverd, dan moet je die opslaan in de core memories.

Je huidige core memories zijn:
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}

Gebruik de tool "search_pdf" om een PDF te zoeken in de kennisbasis.

G
            """,
                messages=message_history,
                tools=[function_to_anthropic_tool(tool) for tool in tools],
                stream=True,
            )

            # Calculate how long the operation took
            end_time = time.time()
            self.logger.info(f"Claude API stream aangemaakt in {end_time - start_time:.2f} seconden")

            # Process Claude's response piece by piece and send it back
            self.logger.info("Start verwerken van Claude's antwoord")
            async for content in self.handle_stream(stream, tools):
                self.logger.debug(f"Deel van Claude's antwoord: {str(content)[:100]}...")
                yield content
            self.logger.info("Claude's antwoord volledig verwerkt")
        
        except Exception as e:
            self.logger.error(f"Onverwachte fout in on_message: {str(e)}")
            self.logger.error(traceback.format_exc())
            yield MessageContent(
                content=f"Er is een fout opgetreden: {str(e)}",
                content_type="text",
                is_error=True,
            )
