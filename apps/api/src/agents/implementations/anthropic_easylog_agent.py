# Python standard library imports
import base64
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


class EasylogData(TypedDict):
    """
    Defines the structure for Easylog data
    """

    status: str
    datum: str
    object: str
    statusobject: str


# Configuration class for AnthropicEasylog agent
class AnthropicEasylogAgentConfig(BaseModel):
    max_report_entries: int = Field(
        default=100,
        description="Maximum number of entries to fetch from the database for reports",
    )
    debug_mode: bool = Field(default=True, description="Enable debug mode with additional logging")
    image_max_width: int = Field(default=1200, description="Maximum width for processed images in pixels")
    image_quality: int = Field(default=90, description="JPEG quality for processed images (1-100)")


# Agent class that integrates with Anthropic's Claude API for EasyLog data analysis
class AnthropicEasylogAgent(AnthropicAgent[AnthropicEasylogAgentConfig]):
    def __init__(self, *args, **kwargs) -> None:
        # Call the parent class init
        super().__init__(*args, **kwargs)

        # Extra logging om tools bij te houden
        self.available_tools = []
        self.logger.info("EasylogAgent initialized with planning tools")

        # Disable debug mode to avoid loading debug tools
        self.config.debug_mode = False

    def _describe_available_tools(self):
        """Log beschikbare tools in de class en filter debug tools uit"""
        all_tools = [
            "tool_store_memory",
            "tool_get_easylog_data",
            "tool_generate_monthly_report",
            "tool_get_object_history",
            "tool_search_pdf",
            "tool_load_image",
            "tool_clear_memories",
        ]

        self.available_tools = all_tools
        self.logger.info(f"Beschikbare tools voor EasylogAgent: {', '.join(all_tools)}")

    def _extract_user_info(self, message_text: str) -> list[str]:
        """
        Detecteert automatisch belangrijke informatie in het bericht van de gebruiker

        Args:
            message_text: De tekstinhoud van het bericht van de gebruiker

        Returns:
            Een lijst met gedetecteerde informatie
        """
        detected_info = []

        # Namen detecteren
        name_patterns = [
            r"(?i)(?:ik ben|mijn naam is|ik heet|noem mij)\s+([A-Za-z\s]+)",
            r"(?i)naam(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                name = match.strip()
                if name and len(name) > 1:  # Minimale lengte om valse positieven te vermijden
                    detected_info.append(f"Naam: {name}")
                    self.logger.info(f"Detected user name: {name}")

        # Functietitels detecteren
        role_patterns = [
            r"(?i)(?:ik ben|ik werk als)(?:\s+de|een|)?\s+([A-Za-z\s]+manager|[A-Za-z\s]+directeur|[A-Za-z\s]+analist|[A-Za-z\s]+medewerker|[A-Za-z\s]+monteur)",
            r"(?i)functie(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                role = match.strip()
                if role and len(role) > 3:  # Minimale lengte om valse positieven te vermijden
                    detected_info.append(f"Functie: {role}")
                    self.logger.info(f"Detected user role: {role}")

        # Afdelingen detecteren
        department_patterns = [
            r"(?i)(?:ik werk bij|ik zit bij)(?:\s+de)?\s+afdeling\s+([A-Za-z\s]+)",
            r"(?i)afdeling(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in department_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                department = match.strip()
                if department and len(department) > 2:  # Minimale lengte om valse positieven te vermijden
                    detected_info.append(f"Afdeling: {department}")
                    self.logger.info(f"Detected user department: {department}")

        # Rapportagevoorkeuren detecteren
        report_patterns = [
            r"(?i)(?:ik wil|graag|liefst)(?:\s+\w+)?\s+(dagelijks|wekelijks|maandelijks|kwartaal|jaarlijks)e?\s+rapport",
            r"(?i)rapport(?:en|ages)?(?:\s+graag)?\s+(dagelijks|wekelijks|maandelijks|kwartaal|jaarlijks)",
        ]

        for pattern in report_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                frequency = match.strip().lower()
                detected_info.append(f"Voorkeur: {frequency}e rapportages")
                self.logger.info(f"Detected reporting preference: {frequency}")

        return detected_info

    async def _store_detected_name(self, message_text: str):
        """
        Detecteert en slaat belangrijke informatie op uit het bericht van de gebruiker

        Args:
            message_text: De tekstinhoud van het bericht van de gebruiker
        """
        detected_info = self._extract_user_info(message_text)

        if not detected_info:
            return

        # Direct store_memory aanroepen voor elke gedetecteerde informatie
        for info in detected_info:
            await self._store_memory_internal(info)

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

        async def tool_get_easylog_data():
            """
            Haalt de controles op uit EasyLog en maakt ze leesbaar.
            """
            try:
                self.logger.info("Fetching EasyLog data")
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.object')) as object,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.controle[0].statusobject')) as statusobject
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
                        datum, object_value, statusobject = entry
                        # Pas de statusobject waarde aan
                        if statusobject == "Ja":
                            statusobject = "Akkoord"
                        elif statusobject == "Nee":
                            statusobject = "Niet akkoord"

                        results.append(f"Datum: {datum}, Object: {object_value}, Status object: {statusobject}")
                    return "\n".join(results)

            except Exception as e:
                logger.error(f"Fout bij ophalen follow-up entries: {str(e)}")
                return f"Er is een fout opgetreden: {str(e)}"

        async def tool_generate_monthly_report(month: int, year: int):
            """
            Genereert een maandrapport voor de opgegeven maand en jaar.
            """
            try:
                self.logger.info(f"Generating monthly report for {month}/{year}")
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.object')) as object,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.controle[0].statusobject')) as statusobject,
                            created_at
                        FROM follow_up_entries
                        WHERE MONTH(created_at) = %s AND YEAR(created_at) = %s
                        ORDER BY created_at DESC
                    """
                    self.logger.debug(f"Executing query with params: {month}, {year}")
                    cursor.execute(query, (month, year))
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return f"Geen controles gevonden voor {month}-{year}"

                    # Telling van statusobjecten
                    status_counts = {"Akkoord": 0, "Niet akkoord": 0, "Anders": 0}
                    objects = set()

                    for entry in entries:
                        datum, object_value, statusobject, created_at = entry

                        # Object toevoegen aan set voor unieke telling
                        if object_value:
                            objects.add(object_value)

                        # Status tellen
                        if statusobject == "Ja":
                            status_counts["Akkoord"] += 1
                        elif statusobject == "Nee":
                            status_counts["Niet akkoord"] += 1
                        else:
                            status_counts["Anders"] += 1

                    # Maandnamen in Nederlands
                    month_names = {
                        1: "januari",
                        2: "februari",
                        3: "maart",
                        4: "april",
                        5: "mei",
                        6: "juni",
                        7: "juli",
                        8: "augustus",
                        9: "september",
                        10: "oktober",
                        11: "november",
                        12: "december",
                    }

                    month_name = month_names.get(month, str(month))

                    # Rapportopbouw
                    report = [
                        f"📊 **Maandrapport {month_name} {year}**",
                        "",
                        "**Samenvatting:**",
                        f"- Totaal aantal controles: {len(entries)}",
                        f"- Unieke objecten gecontroleerd: {len(objects)}",
                        "- Status verdeling:",
                        f"  - Akkoord: {status_counts['Akkoord']} ({round(status_counts['Akkoord'] / len(entries) * 100)}%)",
                        f"  - Niet akkoord: {status_counts['Niet akkoord']} ({round(status_counts['Niet akkoord'] / len(entries) * 100)}%)",
                        f"  - Anders: {status_counts['Anders']} ({round(status_counts['Anders'] / len(entries) * 100)}%)",
                    ]

                    return "\n".join(report)

            except Exception as e:
                logger.error(f"Fout bij genereren maandrapport: {str(e)}")
                return f"Er is een fout opgetreden bij het genereren van het rapport: {str(e)}"

        async def tool_get_object_history(object_name: str, limit: int = 10):
            """
            Haalt de geschiedenis op van een specifiek object.
            """
            try:
                self.logger.info(f"Fetching history for object: {object_name}, limit: {limit}")
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.controle[0].statusobject')) as statusobject,
                            created_at
                        FROM follow_up_entries
                        WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.object')) = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    self.logger.debug(f"Executing query with params: {object_name}, {limit}")
                    cursor.execute(query, (object_name, limit))
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return f"Geen geschiedenis gevonden voor object: {object_name}"

                    results = [f"📜 **Geschiedenis voor {object_name}:**"]

                    for entry in entries:
                        datum, statusobject, created_at = entry

                        if statusobject == "Ja":
                            statusobject = "Akkoord"
                        elif statusobject == "Nee":
                            statusobject = "Niet akkoord"

                        results.append(f"Datum: {datum}, Status: {statusobject}")

                    return "\n".join(results)

            except Exception as e:
                logger.error(f"Fout bij ophalen object geschiedenis: {str(e)}")
                return f"Er is een fout opgetreden: {str(e)}"

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

        async def tool_load_image(_id: str, file_name: str) -> str:
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
                # Controleer en corrigeer pad indien nodig
                if not file_name.startswith("figures/") and "/" not in file_name:
                    original_file_name = file_name
                    file_name = f"figures/{file_name}"
                    self.logger.info(f"[IMAGE] Pad gecorrigeerd: {original_file_name} -> {file_name}")

                # Laad de originele afbeelding
                try:
                    image_data = await self.load_image(_id, file_name)
                except Exception as e:
                    # Als het laden mislukt met figures/ pad, probeer alternatieve paden
                    self.logger.warning(f"[IMAGE] Kon afbeelding niet laden met pad {file_name}: {str(e)}")

                    # Probeer zonder figures/ als dat was toegevoegd
                    if file_name.startswith("figures/"):
                        alt_file_name = file_name.replace("figures/", "")
                        self.logger.info(f"[IMAGE] Probeer alternatief pad zonder figures/: {alt_file_name}")
                        try:
                            image_data = await self.load_image(_id, alt_file_name)
                            self.logger.info(f"[IMAGE] Succesvol geladen met alternatief pad: {alt_file_name}")
                        except Exception:
                            # Probeer met alleen de bestandsnaam (zonder pad)
                            base_name = file_name.split("/")[-1]
                            self.logger.info(f"[IMAGE] Probeer met alleen bestandsnaam: {base_name}")
                            image_data = await self.load_image(_id, base_name)
                    else:
                        # Als het geen figures/ bevat, probeer het toe te voegen
                        alt_file_name = f"figures/{file_name}"
                        self.logger.info(f"[IMAGE] Probeer alternatief pad met figures/: {alt_file_name}")
                        image_data = await self.load_image(_id, alt_file_name)

                original_size = len(image_data)
                original_size_kb = original_size / 1024
                self.logger.info(f"[IMAGE] Originele grootte: {original_size_kb:.1f} KB")

                # Open de afbeelding met PIL
                img = Image.open(io.BytesIO(image_data))
                original_width, original_height = img.size
                self.logger.info(f"[IMAGE] Afmetingen: {original_width}x{original_height}")

                # Basisparameters voor verwerking - sterk verlaagd voor trage verbindingen
                max_width = 600  # Verlaagd van 800 naar 600
                quality = 60  # Verlaagd van 75 naar 60

                # Eenvoudige grootte-classificatie
                is_tiny = original_size < 100 * 1024  # < 100 KB
                is_small = original_size < 500 * 1024  # < 500 KB
                is_large = original_size > 1 * 1024 * 1024  # > 1 MB
                is_huge = original_size > 3 * 1024 * 1024  # > 3 MB

                # Pas verwerkingsparameters aan op basis van grootte
                if is_tiny:
                    max_width = min(original_width, 800)
                    quality = 75
                elif is_small:
                    max_width = min(original_width, 700)
                    quality = 65
                elif is_large:
                    max_width = 500
                    quality = 50
                elif is_huge:
                    max_width = 350
                    quality = 40

                # Resize indien nodig
                if original_width > max_width:
                    scale_factor = max_width / original_width
                    new_height = int(original_height * scale_factor)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    self.logger.info(f"[IMAGE] Resized naar {max_width}x{new_height}")

                # Converteer naar RGB (voor afbeeldingen met transparantie)
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                    img = background

                # Comprimeer de afbeelding
                with io.BytesIO() as buffer:
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    compressed_data = buffer.getvalue()

                # Check de gecomprimeerde grootte
                compressed_size = len(compressed_data)
                compressed_size_kb = compressed_size / 1024

                # Verbeterd twee-staps compressieproces voor trage verbindingen
                max_size_kb = 150  # Doelgrootte ~150 KB

                # Extra compressie indien nodig (max 2 pogingen)
                if compressed_size > max_size_kb * 1024:
                    self.logger.info(f"[IMAGE] Extra compressie nodig: {compressed_size_kb:.1f} KB > {max_size_kb} KB")

                    # 1e extra poging
                    new_width = int(img.width * 0.6)
                    new_quality = max(35, quality - 20)

                    img = img.resize((new_width, int(img.height * 0.6)), Image.Resampling.LANCZOS)

                    # Lichte blur
                    try:
                        from PIL import ImageFilter

                        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
                    except Exception:
                        pass

                    with io.BytesIO() as buffer:
                        img.save(buffer, format="JPEG", quality=new_quality, optimize=True)
                        buffer.seek(0)
                        compressed_data = buffer.getvalue()
                        compressed_size = len(compressed_data)
                        compressed_size_kb = compressed_size / 1024
                        self.logger.info(f"[IMAGE] Na extra compressie: {compressed_size_kb:.1f} KB")

                    # 2e extra poging
                    if compressed_size > 100 * 1024:  # >100KB
                        self.logger.info(f"[IMAGE] Derde compressie nodig: {compressed_size_kb:.1f} KB > 100 KB")
                        final_width = int(new_width * 0.7)
                        final_quality = max(25, new_quality - 10)

                        img = img.resize((final_width, int(img.height * 0.7)), Image.Resampling.LANCZOS)

                        try:
                            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
                        except Exception:
                            pass

                        with io.BytesIO() as buffer:
                            img.save(buffer, format="JPEG", quality=final_quality, optimize=True)
                            buffer.seek(0)
                            compressed_data = buffer.getvalue()
                            compressed_size = len(compressed_data)
                            compressed_size_kb = compressed_size / 1024
                            self.logger.info(f"[IMAGE] Na derde compressie: {compressed_size_kb:.1f} KB")

                # Base64 encoding
                base64_data = base64.b64encode(compressed_data).decode("utf-8")

                # Log compressieresultaat
                compression_ratio = (original_size - compressed_size) / original_size * 100
                self.logger.info(
                    f"[IMAGE] Compressie: {original_size_kb:.1f} KB → {compressed_size_kb:.1f} KB ({compression_ratio:.1f}% reductie)"
                )

                return f"data:image/jpeg;base64,{base64_data}"

            except Exception as e:
                import traceback

                self.logger.error(f"[IMAGE] Fout bij verwerken: {str(e)}")
                self.logger.error(traceback.format_exc())
                return f"Er is een fout opgetreden bij het laden van de afbeelding: {str(e)}"

        tools = [
            tool_store_memory,
            tool_get_easylog_data,
            tool_generate_monthly_report,
            tool_get_object_history,
            tool_search_pdf,
            tool_load_image,
            tool_clear_memories,
        ]

        # Print alle tools om te debuggen
        self.logger.info("All tools before filtering:")
        for tool in tools:
            self.logger.info(f" - {tool.__name__}")

        # Zet alle tools om naar het Anthropic formaat en filter debug tools
        anthropic_tools = []
        for tool in tools:
            if tool.__name__ in [
                "tool_store_memory",
                "tool_get_easylog_data",
                "tool_generate_monthly_report",
                "tool_get_object_history",
                "tool_search_pdf",
                "tool_load_image",
                "tool_clear_memories",
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
            max_tokens=1024,
            system=f"""Je bent een vriendelijke en behulpzame data-analist voor EasyLog.
Je taak is om gebruikers te helpen bij het analyseren van bedrijfsgegevens en het maken van overzichtelijke verslagen.

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke samenvattingen van de EasyLog data!
- Help de gebruiker patronen te ontdekken in de controlegegevens
- Maak verslagen in tabellen en duidelijk en professioneel met goede opmaak
- Gebruik grafieken en tabellen waar mogelijk (markdown)
- Wees proactief in het suggereren van analyses die nuttig kunnen zijn

### Beschikbare tools:
- tool_get_easylog_data: Haalt de laatste controles op uit de EasyLog database
- tool_generate_monthly_report: Maakt een maandrapport met statistieken
- tool_get_object_history: Haalt de geschiedenis van een specifiek object op
- tool_store_memory: Slaat belangrijke informatie op voor later gebruik
- tool_clear_memories: Wist alle opgeslagen herinneringen
- tool_search_pdf: Zoek een PDF in de kennisbank

### Gebruik van de tool_search_pdf
Je kunt de tool_search_pdf gebruiken om te zoeken in PDF-documenten die zijn opgeslagen in de kennisbank. Gebruik deze tool wanneer een gebruiker vraagt naar informatie die mogelijk in een handboek, rapport of ander PDF-document staat.

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, of een belangrijke gebeurtenis heeft meegemaakt, of een belangrijke informatie heeft geleverd, dan moet je die opslaan in de core memories.

Voorbeelden van belangrijke herinneringen om op te slaan:
- Naam van de gebruiker (bijv. "Naam: Jan")
- Functie (bijv. "Functie: Data Analist")
- Afdeling (bijv. "Afdeling: Financiën")
- Voorkeuren voor rapportages (bijv. "Voorkeur: wekelijkse rapportages")
- Specifieke behoeften voor data-analyse (bijv. "Behoefte: focus op niet-conforme objecten")

Je huidige core memories zijn:
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}

### Data analyse tips:
- Zoek naar trends over tijd
- Identificeer objecten met hoog risico (veel 'niet akkoord' statussen)
- Wijs op ongewone of afwijkende resultaten
- Geef context bij de cijfers waar mogelijk
- Vat grote datasets bondig samen
            """,
            messages=message_history,
            tools=anthropic_tools,
            stream=True,
            # Nieuwe parameter voor extended thinking
            thinking={"type": "enabled", "budget_tokens": 12000},
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        if execution_time > 5.0:
            logger.warning(f"API call took longer than expected: {execution_time:.2f} seconds")

        # Direct streaming without buffering
        async for content in self.handle_stream(stream, tools):
            yield content

