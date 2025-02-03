import base64
import glob
import os
import time
from typing import AsyncGenerator, List

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel, Field

from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, TextContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


class AnthropicFirstConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="GezonderLeven",
                instructions="Help met bewegen en het creeren van een gezonder leven!",
                glob_pattern="pdfs/gezonderleven/*.pdf",
            ),
            Subject(
                name="Dieet",
                instructions="Help met het eten van gezonde voeding en help met afvallen",
                glob_pattern="pdfs/dieet/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="WerkenSnelweg")


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class AnthropicFirst(AnthropicAgent[AnthropicFirstConfig]):
    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[str]:
        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        # Find all PDF files in directory and encode them
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(
        self, messages: List[Message]
    ) -> AsyncGenerator[TextContent, None]:
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

        # The get and set metadata functions are used to store and retrieve information between messages
        current_subject = self.get_metadata("subject")
        if current_subject is None:
            current_subject = self.config.default_subject

        subject = next(
            (s for s in self.config.subjects if s.name == current_subject), None
        )

        if subject is not None:
            current_subject_name = subject.name
            current_subject_instructions = subject.instructions
            current_subject_pdfs = self._load_pdfs(subject.glob_pattern)
        else:
            current_subject_name = current_subject
            current_subject_instructions = ""
            current_subject_pdfs = []

        # Create special blocks for each PDF that Claude can read
        # This is like creating a digital package for each PDF
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
                "cache_control": {
                    "type": "ephemeral"
                },  # Tells Claude this is temporary.
            }
            for pdf in current_subject_pdfs
        ]

        # Claude won't respond to tool results if there is a PDF in the message.
        # So we add the PDF to the last user message that doesn't contain a tool result.
        for message in reversed(message_history):
            if (
                message["role"] == "user"  # Only attach PDFs to user messages
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
                message["content"].extend(pdf_content_blocks)
                break

        # Memories are a way to store important information about a user.
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Memories: {memories}")

        # Define helper tools that Claude can use
        # These are like special commands Claude can run to get extra information

        def tool_switch_subject(subject: str | None = None):
            """
            Switch to a different subject.
            """
            if subject is None:
                self.set_metadata("subject", None)
                return "Je bent nu terug in het algemene onderwerp"

            if subject not in [s.name for s in self.config.subjects]:
                raise ValueError(
                    f"Subject {subject} not found, choose from {', '.join([s.name for s in self.config.subjects])}"
                )

            self.set_metadata("subject", subject)

            return f"Je bent nu overgestapt naar het onderwerp: {subject}"

        # This tool is used to store a memory in the database.
        async def tool_store_memory(memory: str):
            """
            Store a memory in the database.
            """
            # Verwijder eventuele '-' aan het begin van de memory
            memory = memory.lstrip("- ")

            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)

            logger.info(f"Storing memory: {memory}")

            self.set_metadata("memories", current_memory)

            return "Memory stored"

        # Aangepaste tool om memories en thread te wissen
        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()  # Wist de gespreksgeschiedenis
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        # Set up the tools that Claude can use
        tools = [
            tool_switch_subject,
            tool_store_memory,
            tool_clear_memories,  # Voeg de nieuwe tool toe
        ]

        # Start measuring how long the operation takes
        # This is like starting a stopwatch
        start_time = time.time()

        # Create a streaming message request to Claude
        # Think of this like starting a live chat with Claude where responses come in piece by piece
        stream = await self.client.messages.create(
            # Tell Claude which version to use (like choosing which expert to talk to)
            model="claude-3-5-sonnet-20241022",
            # Maximum number of words Claude can respond with
            # This prevents responses from being too long
            max_tokens=1024,
            # Special instructions that tell Claude how to behave
            # This is like giving Claude a job description and rules to follow
            system=f"""Je bent een vriendelijke en behulpzame assistent die helpt met bewust gezonder leven

            ### Onderwerpen
- Als je geen onderwerp hebt geselecteerd, volg de de instructies hierboven, anders hebben de volgende regels voorrang:
- Je bent nu in het onderwerp: {current_subject_name}
- Ik kan je helpen met de volgende onderwerpen: {", ".join([s.name for s in self.config.subjects])}
- Je kunt overstappen naar een ander onderwerp met de tool "switch_subject" zodra je een vraag hebt die niet in het huidige onderwerp past.
- Volg altijd de instructies en documentatie van het onderwerp: {current_subject_instructions}

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, of een belangrijke gebeurtenis heeft meegemaakt, of een belangrijke informatie heeft geleverd, dan moet je die opslaan in de core memories. Ook als die een fout heeft opgelost.

Je huidige core memories zijn:
- Eerste herinnering
- Tweede herinnering
- Derde herinnering
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
        logger.info(f"Time taken: {end_time - start_time} seconds")

        # Process Claude's response piece by piece and send it back
        # This is like receiving a long message one sentence at a time
        async for content in self.handle_stream(
            stream,
            messages,
            tools,
        ):
            yield content
