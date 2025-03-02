import base64
import json
import time
import traceback
from collections.abc import AsyncGenerator

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel, Field, ValidationError

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
        self.logger.info("Initializing DebugAnthropicAgent with enhanced logging")
        self._planning_tools = PlanningTools(self.easylog_backend)

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

        # Add debug logging for input messages
        self.logger.info(f"on_message called with {len(messages)} messages")
        try:
            # Convert messages to a format Claude understands
            message_history = self._convert_messages_to_anthropic_format(messages)
            self.logger.debug(f"Converted message history: {json.dumps(message_history, indent=2)}")

            # Create special blocks for each PDF that Claude can read
            # This is like creating a digital package for each PDF
            pdf_content_block: BetaBase64PDFBlockParam | None = (
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(self._active_pdf.file_data).decode("utf-8"),
                    },
                    "cache_control": {"type": "ephemeral"},  # Tells Claude this is temporary.
                }
                if self._active_pdf
                else None
            )

            # Claude won't respond to tool results if there is a PDF in the message.
            # So we add the PDF to the last user message that doesn't contain a tool result.
            for message in reversed(message_history):
                if (
                    pdf_content_block is not None
                    and message["role"] == "user"  # Only attach PDFs to user messages
                    and isinstance(message["content"], list)  # Content must be a list to extend
                    and not any(
                        isinstance(content, dict) and content.get("type") == "tool_result" for content in message["content"]
                    )  # Skip messages that contain tool results
                ):
                    # Add PDF content blocks to eligible messages
                    # This ensures Claude can reference PDFs when responding to user queries
                    message["content"].append(pdf_content_block)
                    break

            # Memories are a way to store important information about a user.
            memories = self.get_metadata("memories", default=[])
            self.logger.info(f"Memories: {memories}")

            # Define helper tools that Claude can use
            # These are like special commands Claude can run to get extra information

            async def tool_search_pdf(query: str) -> str:
                """
                Search for a PDF in the knowledge base.
                """
                knowledge_result = await self.search_knowledge(query)

                if (
                    knowledge_result is None
                    or knowledge_result.object is None
                    or knowledge_result.object.name is None
                    or knowledge_result.object.bucket_id is None
                ):
                    return "Geen PDF gevonden"

                return json.dumps(
                    {
                        "id": knowledge_result.id,
                        "markdown_content": knowledge_result.markdown_content,
                    }
                )

            async def tool_load_image(_id: str, file_name: str) -> str:
                """
                Load an image from the database. Id is the id of the pdf file, and in the markdown you'll find many references to images. Use the exact file path to load the image.
                """

                image_data = await self.load_image(_id, file_name)

                return f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

            async def tool_store_memory(memory: str) -> str:
                """
                Store a memory in the database.
                """

                current_memory = self.get_metadata("memories", default=[])
                current_memory.append(memory)

                self.logger.info(f"Storing memory: {memory}")

                self.set_metadata("memories", current_memory)

                return "Memory stored"

            def tool_clear_memories() -> str:
                """
                Clear all stored memories and the conversation history.
                """
                self.set_metadata("memories", [])
                return "All memories and the conversation history have been cleared."

            # Add more detailed logging for tool setup
            self.logger.info(f"Setting up {len(self._planning_tools.all_tools)} planning tools")
            
            # Wrap the original tools with logging
            original_tools = [
                tool_search_pdf,
                tool_store_memory,
                tool_clear_memories,
                tool_load_image,
                *self._planning_tools.all_tools,
            ]
            
            # Create logging wrappers for each tool
            tools = []
            for tool in original_tools:
                # Create a wrapper that logs before and after each tool execution
                async def logging_wrapper(*args, **kwargs):
                    tool_name = tool.__name__
                    self.logger.info(f"Calling tool '{tool_name}' with args: {args}, kwargs: {kwargs}")
                    try:
                        # For async tools
                        if callable(getattr(tool, "__await__", None)):
                            result = await tool(*args, **kwargs)
                        else:
                            # For non-async tools
                            result = tool(*args, **kwargs)
                        
                        # Log a truncated version of the result to avoid overly large logs
                        result_str = str(result)
                        truncated_result = result_str[:500] + "..." if len(result_str) > 500 else result_str
                        self.logger.info(f"Tool '{tool_name}' completed with result: {truncated_result}")
                        
                        # Log the full raw result at debug level
                        self.logger.debug(f"Full result from tool '{tool_name}': {result}")
                        
                        return result
                    except ValidationError as e:
                        self.logger.error(f"Validation error in tool '{tool_name}': {e}")
                        # Log the detailed error with field locations and values
                        for error in e.errors():
                            self.logger.error(f"Field: {'.'.join(str(loc) for loc in error['loc'])}, Error: {error['msg']}")
                        raise
                    except Exception as e:
                        self.logger.error(f"Error in tool '{tool_name}': {str(e)}")
                        self.logger.error(traceback.format_exc())
                        raise
                
                # Make the wrapper look like the original function for anthropic's tool conversion
                logging_wrapper.__name__ = tool.__name__
                logging_wrapper.__doc__ = tool.__doc__
                logging_wrapper.__annotations__ = tool.__annotations__
                
                tools.append(logging_wrapper)

            # Start measuring how long the operation takes
            start_time = time.time()
            self.logger.info("Creating message stream to Claude")

            try:
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
                
                end_time = time.time()
                self.logger.info(f"Time taken to create message stream: {end_time - start_time} seconds")

                # Process Claude's response piece by piece and send it back
                async for content in self.handle_stream(stream, tools):
                    yield content
            
            except Exception as e:
                self.logger.error(f"Error in Claude API call: {str(e)}")
                self.logger.error(traceback.format_exc())
                # Return error to user
                yield MessageContent(
                    content=f"Er is een fout opgetreden bij het verwerken van uw bericht: {str(e)}",
                    content_type="text",
                    is_error=True,
                )
        
        except Exception as e:
            self.logger.error(f"Unhandled exception in on_message: {str(e)}")
            self.logger.error(traceback.format_exc())
            yield MessageContent(
                content=f"Er is een onverwachte fout opgetreden: {str(e)}",
                content_type="text",
                is_error=True,
            )

    # Add logging to handle_stream as well
    async def handle_stream(self, stream, tools):
        try:
            return await super().handle_stream(stream, tools)
        except Exception as e:
            self.logger.error(f"Error in handle_stream: {str(e)}")
            self.logger.error(traceback.format_exc())
            yield MessageContent(
                content=f"Fout bij het verwerken van de respons: {str(e)}",
                content_type="text",
                is_error=True,
            )
