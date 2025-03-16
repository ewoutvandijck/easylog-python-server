import base64
import io
import json
import mimetypes
import time
from collections.abc import AsyncGenerator
from typing import cast

import cairosvg
import httpx
from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from PIL import Image
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

        self._planning_tools = PlanningTools(self.easylog_backend)

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
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

        # Convert messages to a format Claude understands
        # This is like translating from one language to another
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Create special blocks for each PDF that Claude can read
        # This is like creating a digital package for each PDF
        pdf_content_block: BetaBase64PDFBlockParam | None = (
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(
                        self._active_pdf.file_data
                    ).decode("utf-8"),
                },
                "cache_control": {
                    "type": "ephemeral"
                },  # Tells Claude this is temporary.
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
                and isinstance(
                    message["content"], list
                )  # Content must be a list to extend
                and not any(
                    isinstance(content, dict) and content.get("type") == "tool_result"
                    for content in message["content"]
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

        async def tool_load_image(pdf_id: str, file_name: str) -> Image.Image:
            """
            Load an image from the database. Id is the id of the pdf file, and in the markdown you'll find many references to images. Use the exact file path to load the image.
            """

            self.logger.info(f"Loading image: {pdf_id}, {file_name}")

            return await self.load_image(pdf_id, file_name)

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

        async def tool_download_image_from_url(url: str) -> Image.Image:
            """
            Download an image from a URL and return it as a base64-encoded data URL.
            The image will be returned in a format that can be displayed directly in HTML/markdown.

            Args:
                url (str): The URL of the image to download

            Returns:
                str: A data URL containing the base64-encoded image data
            """

            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                image_data = response.content
                mime_type = (
                    response.headers.get("content-type")
                    or mimetypes.guess_type(url)[0]
                    or "image/jpeg"
                )

                self.logger.info(
                    f"Downloaded image from {url} with mime type {mime_type}"
                )

                if "image/svg+xml" in mime_type:
                    # Convert SVG to PNG
                    self.logger.info("Converting SVG to PNG")
                    image_data = cairosvg.svg2png(bytestring=image_data)

                # Convert the downloaded image data to a PIL Image
                return Image.open(io.BytesIO(cast(bytes, image_data)))

        tools = [
            tool_search_pdf,
            tool_store_memory,
            tool_clear_memories,
            tool_load_image,
            tool_download_image_from_url,
            *self._planning_tools.all_tools,
        ]

        # Start measuring how long the operation takes
        # This is like starting a stopwatch
        start_time = time.time()

        # Create a streaming message request to Claude
        # Think of this like starting a live chat with Claude where responses come in piece by piece
        stream = await self.client.messages.create(
            # Tell Claude which version to use (like choosing which expert to talk to)
            model="claude-3-7-sonnet-20250219",
            # Maximum number of words Claude can respond with
            # This prevents responses from being too long
            max_tokens=2048,
            # Special instructions that tell Claude how to behave
            # This is like giving Claude a job description and rules to follow
            system=f"""Je bent een behulpzame planning assistent die gebruikers helpt bij het beheren van projecten, fases en resources in EasyLog.

### Wat je kunt doen ####
- Projecten bekijken, aanmaken en bijwerken
- Projectfases plannen en aanpassen
- Je kunt Voertuigen, medewerkers of objecten toewijzen aan projecten
- Planning visualiseren en optimaliseren
- Conflicten in planning identificeren en oplossen

### Hoe je helpt an antwoord ###
- Gebruik tabellen en symbols in de weergave van planningen
- Gebruik niet de worden ID's, Resources of allocations in jouw antwoorden 
- ID's moet je negeren in jouw antwoorden
- Allocaties zijn planningen die gemaakt zijn voor een resource. Gebruik niet het woord Allocaties in jouw antwoorden.
- Resources zijn objecten, medewerkers of voertuigen.
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
            # Give Claude access to our special tools
            # This is like giving Claude a toolbox to help answer questions
            tools=[function_to_anthropic_tool(tool) for tool in tools],
            # Tell Claude to send responses as they're ready (piece by piece)
            # Instead of waiting for the complete answer
            stream=True,
        )

        # Calculate how long the operation took
        # This is like stopping our stopwatch
        end_time = time.time()
        self.logger.info(f"Time taken: {end_time - start_time} seconds")

        # Process Claude's response piece by piece and send it back
        # This is like receiving a long message one sentence at a time
        async for content in self.handle_stream(
            stream,
            tools,
        ):
            yield content
