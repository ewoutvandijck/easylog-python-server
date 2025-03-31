# Python standard library imports
import io
import json
import re
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

# Third-party imports
from dotenv import load_dotenv
from PIL import Image
from pydantic import BaseModel, Field

from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool

# Laad alle variabelen uit .env
load_dotenv()


class HealthData(TypedDict):
    """
    Defines the structure for Health data
    """
    status: str
    date: str
    patient: str
    condition: str


class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


# Configuration class for AnthropicHealth agent
class AnthropicHealthConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="Onboarding",
                instructions="Welkom bij de COPD app. Laten we elkaar eerst leren kennen. Hoe mag ik je noemen? #ALTIJD KORTE VRAGEN EN ANTWOORDEN",
                glob_pattern="pdfs/onboarding/*.pdf",
            ),
            Subject(
                name="Coach",
                instructions="Ik ben je persoonlijke COPD coach en help je met adviezen voor een beter leven met COPD.",
                glob_pattern="pdfs/coach/*.pdf",
            ),
            Subject(
                name="Anamnist",
                instructions="Laten we je gezondheid in kaart brengen. Ik stel je enkele vragen over je COPD en je dagelijks leven.",
                glob_pattern="pdfs/anamnist/*.pdf",
            ),
            Subject(
                name="Bewegen",
                instructions="Samen maken we een persoonlijk beweegplan dat past bij jouw situatie en mogelijkheden.",
                glob_pattern="pdfs/bewegen/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="Onboarding")
    max_report_entries: int = Field(
        default=100,
        description="Maximum number of entries to fetch from the database for reports",
    )
    debug_mode: bool = Field(default=True, description="Enable debug mode with additional logging")
    image_max_width: int = Field(default=1200, description="Maximum width for processed images in pixels")
    image_quality: int = Field(default=90, description="JPEG quality for processed images (1-100)")


# Agent class that integrates with Anthropic's Claude API for Health data analysis
class AnthropicHealthAgent(AnthropicAgent[AnthropicHealthConfig]):
    def __init__(self, *args, **kwargs) -> None:
        # Call the parent class init
        super().__init__(*args, **kwargs)

        # Extra logging om tools bij te houden
        self.available_tools = []
        self.logger.info("HealthAgent initialized with planning tools")

        # Disable debug mode to avoid loading debug tools
        self.config.debug_mode = False

    def _describe_available_tools(self):
        """Log beschikbare tools in de class en filter debug tools uit"""
        all_tools = [
            "tool_store_memory",
            "tool_search_pdf",
            "tool_load_image",
            "tool_clear_memories",
            "tool_switch_subject",
        ]

        self.available_tools = all_tools
        self.logger.info(f"Beschikbare tools voor HealthAgent: {', '.join(all_tools)}")

    def _extract_user_info(self, message_text: str) -> tuple[list[str], str | None]:
        """
        Detecteert automatisch belangrijke informatie in het bericht van de gebruiker!!
        Na elke detectie van informatie, stelt de agent de volgende vraag in de reeks:
        1. Naam
        2. Leeftijd
        3. Medicatie (met foto tip)
        4. Aantal pufjes
        5. Reddingsmedicatie

        Args:
            message_text: De tekstinhoud van het bericht van de gebruiker

        Returns:
            tuple: (lijst met gedetecteerde informatie, volgende vraag of None)
        """
        detected_info = []
        next_question = None

        # Namen detecteren
        name_detected = False
        name_patterns = [
            r"(?i)(?:ik ben|mijn naam is|ik heet|noem mij|je mag (?:me|mij) (?:noemen|zeggen))\s+([A-Za-z\s]+)",
            r"(?i)naam(?:\s+is)?\s+([A-Za-z\s]+)",
            r"(?i)(?:zeg maar|noem me maar)\s+([A-Za-z\s]+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                name = match.strip()
                if name and len(name) > 1:
                    detected_info.append(f"Naam: {name}")
                    self.logger.info(f"Detected user name: {name}")
                    name_detected = True
                    next_question = "Wat is je leeftijd?"
                    break
            if name_detected:
                break

        # Leeftijd detecteren als naam al bekend is
        if not next_question:
            age_detected = False
            age_patterns = [
                r"(?i)(?:ik ben|leeftijd is|leeftijd:?)\s*(\d{1,3})\s*(?:jaar)?",
                r"(?i)(\d{1,3})\s*jaar\s*(?:oud)?",
            ]

            for pattern in age_patterns:
                matches = re.findall(pattern, message_text)
                for match in matches:
                    age = int(match)
                    if 0 < age < 120:
                        detected_info.append(f"Leeftijd: {age} jaar")
                        self.logger.info(f"Detected user age: {age}")
                        age_detected = True
                        next_question = "Welke medicatie gebruik je voor je COPD? Je kunt ook een foto maken van de verpakking of het recept, dat helpt mij om je beter te adviseren."
                        break
                if age_detected:
                    break

        # Medicatie detecteren als leeftijd al bekend is
        if not next_question:
            medication_detected = False
            medication_patterns = [
                r"(?i)(?:ik gebruik|neem)\s+([A-Za-z0-9\s]+(?:puffer|medicijn|medicatie)(?:[A-Za-z0-9\s]+)?)",
                r"(?i)(?:mijn medicatie is|medicatie:?)\s+([A-Za-z0-9\s]+)",
            ]

            for pattern in medication_patterns:
                matches = re.findall(pattern, message_text)
                for match in matches:
                    medication = match.strip()
                    if medication:
                        detected_info.append(f"Medicatie: {medication}")
                        self.logger.info(f"Detected medication: {medication}")
                        medication_detected = True
                        next_question = "Hoeveel pufjes per dag zijn er voorgeschreven?"
                        break
                if medication_detected:
                    break

        # Pufjes detecteren als medicatie al bekend is
        if not next_question:
            puffs_detected = False
            puffs_patterns = [
                r"(?i)(\d+)\s*(?:pufjes|puf(?:jes)?)\s*(?:per|aan|in de)\s*dag",
                r"(?i)(?:per dag|dagelijks)\s*(\d+)\s*(?:pufjes|puf(?:jes)?)",
            ]

            for pattern in puffs_patterns:
                matches = re.findall(pattern, message_text)
                for match in matches:
                    puffs = int(match)
                    if 0 < puffs < 20:
                        detected_info.append(f"Pufjes per dag: {puffs}")
                        self.logger.info(f"Detected puffs per day: {puffs}")
                        puffs_detected = True
                        next_question = "Gebruik je ook reddingsmedicatie als dat nodig is?"
                        break
                if puffs_detected:
                    break

        # Reddingsmedicatie detecteren als laatste stap
        if not next_question:
            rescue_patterns = [
                r"(?i)(ja|nee),?\s*(?:ik gebruik)?\s*(?:ook)?\s*reddingsmedicatie",
                r"(?i)reddingsmedicatie:?\s*(ja|nee)",
                r"(?i)(?:gebruik|neem)\s+(?:ook)?\s*reddingsmedicatie\s*(?:als|indien|wanneer)?",
            ]

            for pattern in rescue_patterns:
                matches = re.findall(pattern, message_text)
                for match in matches:
                    rescue = match.strip().lower()
                    if rescue in ['ja', 'nee']:
                        detected_info.append(f"Reddingsmedicatie: {rescue}")
                        self.logger.info(f"Detected rescue medication: {rescue}")
                        next_question = "Bedankt voor deze informatie. Ik ga je nu doorverwijzen naar je persoonlijke COPD coach."
                        break

        if detected_info:
            return detected_info, next_question
        return [], None

    async def _store_detected_name(self, message_text: str):
        """
        Detecteert en slaat belangrijke informatie op uit het bericht van de gebruiker

        Args:
            message_text: De tekstinhoud van het bericht van de gebruiker
        """
        detected_info, next_question = self._extract_user_info(message_text)

        if detected_info:
            # Direct store_memory aanroepen voor elke gedetecteerde informatie
            for info in detected_info:
                await self._store_memory_internal(info)
            
            # Als er een volgende vraag is, sla deze op als laatste vraag
            if next_question:
                await self._store_memory_internal(f"Laatste vraag: {next_question}")

    async def _store_memory_internal(self, memory: str):
        """
        Interne functie om herinneringen op te slaan met controle op duplicaten

        Args:
            memory: De herinnering die moet worden opgeslagen
        """
        memory = memory.strip()
        if not memory:
            return

        # Haal huidige herinneringen op
        current_memories = self.get_metadata("memories", default=[])

        # Extract type (alles voor de eerste ":")
        memory_type = memory.split(":", 1)[0].strip().lower() if ":" in memory else ""

        # Zoek naar bestaande herinnering van hetzelfde type
        existing_index = -1
        for i, existing_memory in enumerate(current_memories):
            existing_type = existing_memory.split(":", 1)[0].strip().lower() if ":" in existing_memory else ""
            if memory_type and existing_type == memory_type:
                existing_index = i
                break

        # Update bestaande of voeg nieuwe toe
        if existing_index >= 0:
            # Vervang bestaande herinnering
            current_memories[existing_index] = memory
            self.logger.info(f"Updated existing memory: {memory}")
        else:
            # Voeg nieuwe herinnering toe
            current_memories.append(memory)
            self.logger.info(f"Added new memory: {memory}")

        # Sla bijgewerkte herinneringen op
        self.set_metadata("memories", current_memories)

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        Deze functie handelt elk bericht van de gebruiker af.
        We bufferen nu het volledige Claude-antwoordsignaal, zodat base64-afbeeldingen
        in één keer overkomen (en dus niet gedeeltelijk) bij een trage verbinding.
        """
        # Verwijder eventuele debug tools die in de code zijn overgebleven
        self.logger.info("Removing any debug tools that might still be in code")
        # Debug mode debug tools verwijderen
        self.config.debug_mode = False

        # Beschrijf beschikbare tools
        self._describe_available_tools()

        # Log the incoming message for debugging
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == "user" and isinstance(last_message.content, str):
                self.logger.info(f"Processing user message: {last_message.content[:100]}...")
                # Automatisch naam detecteren en opslaan
                await self._store_detected_name(last_message.content)

        # Convert messages to a format Claude understands
        message_history = self._convert_messages_to_anthropic_format(messages)

        if self.config.debug_mode:
            self.logger.debug(f"Converted message history: {message_history}")

        # Memories ophalen
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Current memories: {memories}")

        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()
            self.logger.info("Memories and conversation history cleared")
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        async def tool_store_memory(memory: str) -> str:
            """
            Store a memory in the database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            self.logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        async def tool_search_pdf(query: str) -> str:
            """
            Search for information in PDFs stored in the knowledge base.

            Args:
                query (str): The search query to find relevant information in PDF documents

            Returns:
                str: JSON string containing the search results with PDF content or a message indicating no results were found
            """
            self.logger.info(f"[PDF SEARCH] Searching for: {query}")
            knowledge_result = await self.search_knowledge(query)

            if (
                knowledge_result is None
                or knowledge_result.object is None
                or knowledge_result.object.name is None
                or knowledge_result.object.bucket_id is None
            ):
                self.logger.warning(f"[PDF SEARCH] No results found for query: {query}")
                return "Geen PDF gevonden"

            self.logger.info(f"[PDF SEARCH] Found PDF: {knowledge_result.object.name}")

            # Verwerk de afbeeldingen, als die beschikbaar zijn
            images_data = []
            if hasattr(knowledge_result, "images") and knowledge_result.images:
                self.logger.info(f"[PDF SEARCH] Found {len(knowledge_result.images)} images in PDF")
                for img in knowledge_result.images:
                    images_data.append(
                        {
                            "id": img.id,
                            "object_id": img.object_id,
                            "summary": img.summary,
                            "file_name": img.original_file_name,
                            "page": img.page,
                        }
                    )

            # Maak een volledige JSON respons met alle beschikbare informatie
            return json.dumps(
                {
                    "id": knowledge_result.id,
                    "markdown_content": knowledge_result.markdown_content,
                    "title": knowledge_result.object.name,
                    "summary": knowledge_result.short_summary,
                    "long_summary": knowledge_result.long_summary,
                    "images": images_data,
                }
            )

        async def tool_load_image(_id: str, file_name: str) -> Image.Image:
            """
            Laad een afbeelding uit de database en bereid deze voor op weergave.
            De functie accepteert zowel volledige paden (figures/bestand.png) als alleen bestandsnamen (bestand.png).

            Args:
                _id (str): Het ID van het PDF bestand
                file_name (str): De bestandsnaam van de afbeelding (met of zonder pad)

            Returns:
                str: Een data URL met de afbeelding als base64 gecodeerde data
            """
            self.logger.info(f"[IMAGE] Laden afbeelding {file_name} uit {_id}")

            try:
                # Vereenvoudigde pad-logica: probeer verschillende padformaten tot er een werkt
                possible_paths = [
                    file_name,
                    f"figures/{file_name}" if "/" not in file_name else file_name,
                    file_name.replace("figures/", "") if file_name.startswith("figures/") else file_name,
                    file_name.split("/")[-1],  # Alleen de bestandsnaam
                ]

                # Probeer elke mogelijke padvariant
                image_data = None
                last_error = None

                for path in possible_paths:
                    try:
                        image_data = await self.load_image(_id, path)
                        self.logger.info(f"[IMAGE] Succesvol geladen met pad: {path}")
                        break
                    except Exception as e:
                        last_error = e
                        continue

                if image_data is None:
                    raise last_error or Exception("Kon afbeelding niet laden met beschikbare paden")

                # Bepaal originele grootte
                with io.BytesIO() as buffer:
                    image_data.save(buffer, format=image_data.format or "PNG")
                    buffer.seek(0)
                    original_size = len(buffer.getvalue())
                    original_size_kb = original_size / 1024

                # Vereenvoudigde compressielogica
                original_width, original_height = image_data.size

                # Basisconfiguratie voor optimale prestaties op mobiele apparaten
                max_width = 600
                quality = 60

                # Eenvoudige aanpassing op basis van afbeeldingsgrootte
                if original_size < 100 * 1024:  # < 100 KB
                    max_width = min(original_width, 800)
                    quality = 75
                elif original_size > 1 * 1024 * 1024:  # > 1 MB
                    max_width = 450
                    quality = 45

                # Resize indien nodig
                if original_width > max_width:
                    scale_factor = max_width / original_width
                    new_height = int(original_height * scale_factor)
                    image_data = image_data.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Converteer naar RGB (voor afbeeldingen met transparantie)
                if image_data.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", image_data.size, (255, 255, 255))
                    background.paste(
                        image_data,
                        mask=image_data.split()[3] if len(image_data.split()) > 3 else None,
                    )
                    image_data = background

                # Comprimeer de afbeelding
                with io.BytesIO() as buffer:
                    image_data.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    compressed_data = buffer.getvalue()
                    compressed_size = len(compressed_data)
                    compressed_size_kb = compressed_size / 1024

                # Extra compressie alleen als echt nodig (> 150KB)
                if compressed_size > 150 * 1024:
                    # Verder verkleinen en comprimeren
                    new_width = int(image_data.width * 0.7)
                    new_height = int(image_data.height * 0.7)

                    image_data = image_data.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Probeer blurren voor betere compressie
                    try:
                        from PIL import ImageFilter

                        image_data = image_data.filter(ImageFilter.GaussianBlur(radius=0.6))
                    except Exception:
                        pass

                    with io.BytesIO() as buffer:
                        image_data.save(buffer, format="JPEG", quality=40, optimize=True)

                self.logger.info(
                    f"[IMAGE] Beeld geoptimaliseerd: {original_size_kb:.1f}KB → {compressed_size_kb:.1f}KB"
                )
                return image_data

            except Exception as e:
                self.logger.error(f"[IMAGE] Fout bij verwerken: {str(e)}")
                raise e

        def tool_switch_subject(subject: str | None = None):
            """
            Wissel van onderwerp voor de conversatie.
            """
            if subject is None:
                # Als we uit Onboarding komen, ga naar Coach
                current = self.get_metadata("subject")
                if current == "Onboarding":
                    self.set_metadata("subject", "Coach")
                    return "Onboarding voltooid. Je gaat nu verder met je persoonlijke COPD coach."
                # Anders terug naar Coach als default
                self.set_metadata("subject", "Coach")
                return "Terug naar je persoonlijke COPD coach"

            if subject not in [s.name for s in self.config.subjects]:
                raise ValueError(f"Ongeldig onderwerp. Kies uit: {', '.join([s.name for s in self.config.subjects])}")

            self.set_metadata("subject", subject)
            return f"Onderwerp gewijzigd naar: {subject}"

        tools = [
            tool_store_memory,
            tool_search_pdf,
            tool_load_image,
            tool_clear_memories,
            tool_switch_subject,
        ]

        # Get current subject
        current_subject = self.get_metadata("subject")
        if current_subject is None:
            current_subject = self.config.default_subject

        subject = next((s for s in self.config.subjects if s.name == current_subject), None)

        if subject is not None:
            current_subject_name = subject.name
            current_subject_instructions = subject.instructions
        else:
            current_subject_name = current_subject
            current_subject_instructions = ""

        # Print alle tools om te debuggen
        self.logger.info("All tools before filtering:")
        for tool in tools:
            self.logger.info(f" - {tool.__name__}")

        # Zet alle tools om naar het Anthropic formaat en filter debug tools
        anthropic_tools = []
        for tool in tools:
            if tool.__name__ in [
                "tool_store_memory",
                "tool_search_pdf",
                "tool_load_image",
                "tool_clear_memories",
                "tool_switch_subject",
            ]:
                anthropic_tools.append(function_to_anthropic_tool(tool))
                self.logger.info(f"Added tool to Anthropic tools: {tool.__name__}")
            else:
                self.logger.warning(f"Skipping tool: {tool.__name__}")

        # Print alle tools na filtering om te debuggen
        self.logger.info("All tools after filtering:")
        for i, tool in enumerate(anthropic_tools):
            try:
                if hasattr(tool, "function") and hasattr(tool.function, "name"):
                    self.logger.info(f" - {i + 1}: {tool.function.name}")
                elif isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                    self.logger.info(f" - {i + 1}: {tool['function']['name']}")
                else:
                    self.logger.info(f" - {i + 1}: {str(tool)[:50]}")
            except Exception as e:
                self.logger.warning(f" - {i + 1}: Error logging tool: {str(e)}")

        start_time = time.time()

        # In plaats van de stream direct door te geven,
        # bufferen we het volledige antwoord en sturen het dan in één keer.
        buffered_content = []
        stream = await self.client.messages.create(
            # Gebruik Claude 3.7 Sonnet model
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system=f"""Je bent een vriendelijke assistent die COPD patienten help met een beter leven en informatie over hun ziekte. Bewegen en gezond leven is belangrijk.

### BELANGRIJKE REGELS VOOR GESPREK:
### STEL KORTE VRAGEBN EN GEEF KORTE ANTWOORDEN
- Stel één vraag tegelijk en wacht op antwoord
- Volg de vaste volgorde van vragen tijdens Onboarding:
  1. Naam
  2. Leeftijd
  3. Medicatie (met foto-optie)
  4. Aantal pufjes per dag
  5. Reddingsmedicatie
- Reageer op het antwoord van de patient en stel dan pas de volgende vraag
- Bij medicatie, herinner de patient dat ze een foto kunnen maken van de verpakking/recept
- Na alle vragen, ga automatisch door naar Coach

Actueel onderwerp: {current_subject_name}
Huidige instructies: {current_subject_instructions}

### Beschikbare onderwerpen:
{", ".join([s.name for s in self.config.subjects])}

### Core memories
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}""",
            messages=message_history,
            tools=anthropic_tools,
            stream=True,
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        if execution_time > 5.0:
            logger.warning(f"API call took longer than expected: {execution_time:.2f} seconds")

        # Detecteer en buffer alle berichten met afbeeldingen omdat die het meest gevoelig zijn
        # voor streaming problemen bij slechte internetverbindingen
        has_image_content = False
        image_buffer = []

        async for content in self.handle_stream(stream, tools):
            # Controleer of we afbeeldingen hebben gedetecteerd
            if hasattr(content, "type") and content.type == "image":
                # Afbeelding gedetecteerd, schakel over naar buffermodus
                has_image_content = True
                self.logger.info("Afbeelding gedetecteerd, schakelen naar buffer modus")
                # Voeg deze afbeelding toe aan de buffer
                image_buffer.append(content)
            elif has_image_content:
                # We hebben al een afbeelding gezien, blijf alles bufferen
                image_buffer.append(content)
            else:
                # Geen afbeeldingen gedetecteerd, stuur content direct door (smooth streaming)
                yield content

        # Als er afbeeldingen waren, stuur de gebufferde content nu
        if has_image_content and image_buffer:
            self.logger.info(f"Verzenden van {len(image_buffer)} gebufferde berichten met afbeeldingen")
            for buffered_chunk in image_buffer:
                yield buffered_chunk
