import base64
import glob
import os
import time
from typing import AsyncGenerator, List

from anthropic import AsyncAnthropic
from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from anthropic.types.message_param import MessageParam
from anthropic.types.text_block_param import TextBlockParam
from pydantic import Field

from src.agents.base_agent import AgentConfig, BaseAgent
from src.logger import logger
from src.models.messages import Message, MessageContent


# Configuration class for AnthropicNew agent
# Specifies the directory path where PDF files are stored
class AnthropicNewConfig(AgentConfig):
    pdfs_path: str = Field(default="pdfs")


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class AnthropicNew(BaseAgent):
    # Anthropic client instance for making API calls
    client: AsyncAnthropic

    def __init__(self, *args, **kwargs):
        # Initialize parent BaseAgent class
        super().__init__(*args, **kwargs)

        # Initialize Anthropic client with API key from environment
        self.client = AsyncAnthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    def _load_pdfs(self, path: str = "pdfs") -> list[str]:
        """
        Loads and base64 encodes all PDF files from the specified directory.

        Args:
            path (str): Directory path containing PDF files. Defaults to "./pdfs"

        Returns:
            list[str]: List of base64 encoded PDF contents
        """

        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        path = os.path.join(os.path.dirname(__file__), path)

        # Find all PDF files in directory and encode them
        for file in glob.glob(f"{path}/*.pdf"):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(
        self, messages: List[Message], config: AnthropicNewConfig
    ) -> AsyncGenerator[MessageContent, None]:
        # Load PDFs from the configured path
        pdfs = self._load_pdfs(config.pdfs_path)

        # Get all messages except the most recent one
        previous_messages = messages[:-1]

        # Convert previous messages into Anthropic's BetaMessageParam format
        # Each message contains role (user/assistant) and content blocks
        message_history: list[MessageParam] = [
            {
                "role": message.role,
                "content": [
                    {
                        "type": "text",
                        "text": content.content,
                    }
                    for content in message.content
                    if content.content
                ],
            }
            for message in previous_messages
            if message.content
        ]

        # Get the content of the most recent message
        current_message = messages[-1].content

        # Create PDF content blocks for each loaded PDF
        # These will be sent to Claude as base64-encoded documents
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
                "cache_control": {"type": "ephemeral"}, 
            }
            for pdf in pdfs
        ]

        # Convert the current message content into text blocks
        text_content_blocks: list[TextBlockParam] = [
            {
                "type": "text",
                "text": content.content,
                "cache_control": {"type": "ephemeral"}, 
            }
            for content in current_message
        ]

        # Print performance
        start_time = time.time()

        # Create a streaming message request to Claude
        # This includes the message history, PDFs, and current message
        stream = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="""Je bent een vriendelijke en behulpzame technische assistent voor tram monteurs. Je taak is om te helpen bij het oplossen van storingen en het uitvoeren van onderhoud.

BELANGRIJKE REGELS:
- Vul NOOIT aan met eigen technische kennis of tips uit jouw eigen kennis
- Spreek alleen over de onderhoud en reparatie en storingen bij trams, ga niet in op andere vraagstukken 
- Bij het weergeven van probleem oplossingen uit de documentatie, doe dit 1 voor 1 en vraag de monteur altijd eerst om een antwoord
- Als een vraag niet beantwoord kan worden met de informatie uit het document, zeg dit dan duidelijk
- !!!!!!!!! LOOP ALTIJD DE PROBLEEM OPLOSSING, stapsgewijs - vraag per vraag DOOR !!!!!!!!!
- Stel soms een vraag over de documentatie om de kennis van de monteur te verbeteren
- ### De monteur gebruikt een mobiel dus geef geen lange antwoorden ###

### BIJ HET TOEPASSEN VAN EEN STROOMSCHEMA: ###

In het stroomschema zie je de volgende symbolen:
- Hexagon (zeshoeken) - Deze bevatten vragen die aan de monteur gesteld moeten worden, bijvoorbeeld "Is de fout in de andere omvormers opgetreden?"
- Rechthoek - Deze bevatten acties/taken die uitgevoerd moeten worden, bijvoorbeeld "Controleer werking van Vbus-sensor", volg de pijlen daarna voor de bijbehorde vraag in een volgende stap.
- Ovale cirkel - Deze bevatten opmerkingen/toelichtingen die met de monteur gedeeld moeten worden, bijvoorbeeld "De fout is het gevolg van een lage spanning in de kettinglijn. OPGELOST"
- Rode rechthoek - Deze bevat de startconditie/foutmelding 
- Pijlen - Deze geven de stroomrichting aan en verbinden de verschillende onderdelen. Bij sommige pijlen staan "JA" of "NEE" om aan te geven welke route gevolgd moet worden op basis van het antwoord.- 
- Controleer voor je antwoord geeft je de juiste stap in het stroomschema behandeld en geen stap hebt overgeslagen.
- Dit is een typisch diagnostisch stroomschema dat stap voor stap gevolgd moet worden om een storing op te lossen
""",
            messages=[
                *message_history,
                {
                    "role": "user",
                    "content": [
                        *pdf_content_blocks,  # First send PDFs
                        *text_content_blocks,  # Then send text content
                    ],
                },
            ],
            stream=True,
        )

        end_time = time.time()
        logger.info(f"Time taken: {end_time - start_time} seconds")

        # Process the streaming response
        # Yield text content as it arrives from Claude
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield MessageContent(content=event.delta.text)
