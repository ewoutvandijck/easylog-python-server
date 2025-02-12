import base64
import glob
import os
import random
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

from pydantic import BaseModel, Field
from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


class AnthropicMUCConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="GezonderLeven",
                instructions="Begin met het uitleggen welke onderwerpen/subjects je kent. Je bent een vriendelijke en behulpzame assistent die helpt met bewust gezonder leven. In dit onderwerp help je met bewegen en het creëren van een gezonder leven!",
                glob_pattern="pdfs/gezonderleven/*.pdf",
            ),
            Subject(
                name="Dieet",
                instructions="Begin met het uitleggen welke onderwerpen/subjects je kent. Je bent een vriendelijke en behulpzame assistent die helpt met voeding en afvallen. Help met het eten van gezonde voeding en help met afvallen op basis van de documentatie.",
                glob_pattern="pdfs/dieet/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="GezonderLeven")


# Voeg PQI data structuur toe als je die nodig hebt
class PQIDataMuc(TypedDict):
    """
    Defines the structure for PQI data specifically for MUC components.
    """

    # Vul aan met relevante velden voor MUC indien nodig
    pass


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class AnthropicMUC(AnthropicAgent[AnthropicMUCConfig]):
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
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Deze functie handelt elk bericht van de gebruiker af.
        """
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Memories ophalen (aangepaste logging zoals in trams)
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Memories: {memories}")

        # Get and set current subject
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

        # Tools definities updaten
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

        async def tool_store_memory(memory: str):
            """
            Sla een geheugen (memory) op in de database.
            """
            # Verwijder eventuele '-' aan het begin van de memory
            memory = memory.lstrip("- ")
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        # Tools lijst updaten
        tools = [
            tool_store_memory,
            tool_get_random_number,
            tool_clear_memories,
        ]

        # Timing logging toevoegen zoals in trams
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
            system=f"""Je bent een vriendelijke en behulpzame assistent die helpt met bewust gezonder leven.

BELANGRIJKE REGELS:
- Vul NOOIT aan met eigen kennis of tips uit jouw eigen kennis
- Spreek alleen over gezond leven en dieet, ga niet in op andere vraagstukken
- Bij het weergeven van adviezen, doe dit 1 voor 1, stap voor stap
- Als een vraag niet beantwoord kan worden, zeg dit dan duidelijk
- ### De gebruiker gebruikt een mobiel dus geef geen lange antwoorden ###
- Groet alleen aan het begin van het bericht, niet in het midden of aan het einde.

### Onderwerpen
- Als je geen onderwerp hebt geselecteerd, volg de de instructies hierboven, anders hebben de volgende regels voorrang:
- Je bent nu in het onderwerp: {current_subject_name}
- Ik kan je helpen met de volgende onderwerpen: {", ".join([s.name for s in self.config.subjects])}
- Je kunt overstappen naar een ander onderwerp met de tool "switch_subject" zodra je een vraag hebt die niet in het huidige onderwerp past.
- Volg altijd de instructies en documentatie van het onderwerp: {current_subject_instructions}
- Bij onderwerpen die betrekking hebben tot voeding en afvallen, gebruik je het onderwerp "Dieet"

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, of een belangrijke gebeurtenis heeft meegemaakt, of een belangrijke informatie heeft geleverd, dan moet je die opslaan in de core memories.

Je huidige core memories zijn:
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}
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
