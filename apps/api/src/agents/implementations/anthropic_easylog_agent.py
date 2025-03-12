# Python standard library imports
import base64
import io
import json
import mimetypes
import re
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

import httpx

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
            Laad een afbeelding uit de database. Id is het id van het PDF bestand, en in de markdown vind je veel verwijzingen naar afbeeldingen.
            Gebruik het exacte bestandspad om de afbeelding te laden.

            Args:
                _id (str): Het ID van het PDF bestand
                file_name (str): De bestandsnaam van de afbeelding zoals vermeld in de markdown

            Returns:
                str: Een data URL die de afbeelding als base64 gecodeerde data bevat
            """
            self.logger.info("[IMAGE LOADING] ===== START AFBEELDING VERWERKING =====")
            self.logger.info(f"[IMAGE LOADING] ID: {_id}, Bestand: {file_name}")
            self.logger.info(
                f"[IMAGE LOADING] Configuratie: max_width={self.config.image_max_width}px, quality={self.config.image_quality}%"
            )

            try:
                # Originele afbeelding laden
                image_data = await self.load_image(_id, file_name)
                original_size = len(image_data)
                original_size_mb = original_size / (1024 * 1024)
                mime_type = mimetypes.guess_type(file_name)[0] or "image/jpeg"
                self.logger.info(
                    f"[IMAGE LOADING] Afbeelding geladen: {original_size / 1024:.2f} KB ({original_size_mb:.2f} MB), type {mime_type}"
                )

                # Kleinere limiet voor trage verbindingen
                MAX_COMPRESSED_SIZE = 40 * 1024  # Verlaagd naar 40KB voor 5G compatibiliteit

                # Hard streaming limit voor verbindingsproblemen
                MAX_STREAMING_SIZE = 80 * 1024  # Verlaagd naar 80KB voor 5G compatibiliteit
                
                # Direct thumbnail trigger
                FORCE_THUMBNAIL_SIZE = 300 * 1024  # Verlaagd naar 300KB voor 5G compatibiliteit

                # Veilige maximale grootte voor base64 output
                MAX_BASE64_SIZE = 120 * 1024  # Verlaagd naar 120KB voor 5G compatibiliteit

                # 5G optimalisatie logging
                self.logger.info("[IMAGE LOADING] 5G-optimalisatie ingeschakeld: extra kleine afbeeldingen")

                # Voor zeer grote afbeeldingen tonen we een waarschuwing
                is_very_large_image = False
                is_extremely_large_image = False
                needs_streaming_optimization = False
                img = None

                try:
                    # Laad de afbeelding
                    img = Image.open(io.BytesIO(image_data))

                    # Originele afmetingen en grootte
                    original_width, original_height = img.size
                    self.logger.info(f"[IMAGE LOADING] Originele afmetingen: {original_width}x{original_height}")
                    self.logger.info(f"[IMAGE LOADING] Originele bestandsgrootte: {original_size_mb:.2f} MB")

                    # AANGEPAST: Agressievere streaming optimalisatie (vanaf 2MB in plaats van 3MB)
                    if original_size > 1 * 1024 * 1024:  # Verlaagd van 2MB naar 1MB
                        needs_streaming_optimization = True
                        self.logger.warning(
                            f"[IMAGE LOADING] Streaming optimalisatie geactiveerd voor {original_size_mb:.2f} MB afbeelding"
                        )

                    # AANGEPAST: Verlaagde drempel voor extreem grote afbeeldingen
                    if original_size > 2 * 1024 * 1024:  # Verlaagd van 3MB naar 2MB
                        self.logger.warning(
                            f"[IMAGE LOADING] EXTREEM grote afbeelding gedetecteerd: {original_size_mb:.2f} MB - DIRECTE THUMBNAIL"
                        )

                        # NIEUW: Veiligere thumbnail generatie
                        try:
                            thumb_img = img.copy()
                            thumb_width = 120  # Verkleind naar 120px voor 5G compatibiliteit
                            # Zorg voor correcte aspect ratio
                            thumb_height = int(thumb_width * thumb_img.height / thumb_img.width)
                            # Gebruik LANCZOS voor betere kwaliteit met minder artefacten
                            thumb_img = thumb_img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)

                            # NIEUW: Extra optimalisatie voor streaming
                            with io.BytesIO() as thumb_buffer:
                                thumb_img.save(thumb_buffer, format="JPEG", quality=20, optimize=True)  # Verlaagd naar 20% voor 5G
                                thumb_buffer.seek(0)
                                try:
                                    from PIL import ImageFilter
                                    # Lichte blur toepassen voor betere compressie
                                    thumb_img = thumb_img.filter(ImageFilter.GaussianBlur(radius=0.5))  # Verhoogd naar 0.5 voor 5G
                                    thumb_buffer = io.BytesIO()
                                    thumb_img.save(thumb_buffer, format="JPEG", quality=18, optimize=True)  # Verlaagd naar 18% voor 5G
                                    thumb_buffer.seek(0)
                                except Exception as blur_error:
                                    self.logger.warning(f"[IMAGE LOADING] Blur optimalisatie niet mogelijk: {str(blur_error)}")
                                thumb_data = thumb_buffer.getvalue()

                            # NIEUW: Validatie van thumbnail data
                            if len(thumb_data) == 0:
                                raise ValueError("Thumbnail data is leeg")

                            # NIEUW: Controleer thumbnail grootte en comprimeer indien nodig
                            thumb_size = len(thumb_data)
                            if thumb_size > MAX_COMPRESSED_SIZE:
                                self.logger.warning(f"[IMAGE LOADING] Thumbnail te groot: {thumb_size/1024:.2f}KB, extra compressie")
                                with io.BytesIO() as buffer:
                                    # 5G optimalisatie: kleinere thumbs bij overgrootte
                                    resize_width = 100 if USE_5G_OPTIMIZATION else 140  # Verlaagd naar 100px voor 5G
                                    thumb_img = thumb_img.resize((resize_width, int(resize_width * thumb_img.height / thumb_img.width)), 
                                                        Image.Resampling.LANCZOS)
                                    # 5G optimalisatie: extremere compressie
                                    final_quality = 15 if USE_5G_OPTIMIZATION else 20  # Verlaagd naar 15% voor 5G
                                    thumb_img.save(buffer, format="JPEG", quality=final_quality, optimize=True)
                                    buffer.seek(0)
                                    thumb_data = buffer.getvalue()

                            # Veilige base64 encoding
                            try:
                                thumb_data_b64 = base64.b64encode(thumb_data).decode("utf-8")
                                self.logger.info(f"[IMAGE LOADING] Thumbnail grootte: {len(thumb_data)/1024:.2f}KB, Base64: {len(thumb_data_b64)/1024:.2f}KB")
                                return f"data:image/jpeg;base64,{thumb_data_b64}"
                            except Exception as b64_error:
                                self.logger.error(f"[IMAGE LOADING] Base64 encoding fout: {str(b64_error)}")
                                # Ga door naar fallback
                        except Exception as thumb_error:
                            # Als zelfs de thumbnail faalt, log en ga door naar fallback
                            self.logger.error(f"[IMAGE LOADING] Thumbnail fout: {str(thumb_error)}")
                            # Ga door naar aangepaste fallback

                        # NIEUW: Verbeterde fallback voor thumbnail mislukkingen
                        is_extremely_large_image = True
                        is_very_large_image = True
                        # 5G optimalisatie: kleinere targets
                        target_width = 100  # Verkleind naar 100px voor 5G compatibiliteit
                        quality = 18  # Verlaagd naar 18% voor 5G compatibiliteit
                    elif original_size > 1.5 * 1024 * 1024:  # Verlaagd van 2MB naar 1.5MB
                        is_very_large_image = True
                        self.logger.info(
                            f"[IMAGE LOADING] Zeer grote afbeelding gedetecteerd: {original_size_mb:.2f} MB"
                        )
                        target_width = 240  # Verkleind van 320 naar 240
                        quality = 40  # Verlaagd van 50 naar 40
                    elif original_size > 500 * 1024:  # Verlaagd van 800KB naar 500KB
                        target_width = 400  # Verkleind van 500 naar 400
                        quality = 50  # Verlaagd van 60 naar 50
                    else:
                        # Gebruik configuratie voor normale afbeeldingen met wat conservatievere instellingen
                        target_width = min(self.config.image_max_width, 560)  # Verlaagd van 700 naar 560
                        quality = min(60, self.config.image_quality)  # Verlaagd van 70 naar 60

                    self.logger.info(
                        f"[IMAGE LOADING] Target instellingen: {target_width}px breed, {quality}% kwaliteit"
                    )

                    # AANGEPAST: Verbeterde thumbnail generatie voor grote afbeeldingen
                    if needs_streaming_optimization and original_size > FORCE_THUMBNAIL_SIZE:
                        self.logger.warning(
                            f"[IMAGE LOADING] Direct thumbnail genereren voor grote afbeelding ({original_size_mb:.2f} MB)"
                        )
                        # Maak een kleine thumbnail voor directe weergave
                        # 5G optimalisatie: extreem kleine thumbs
                        thumb_width = 100  # Verkleind naar 100px voor 5G compatibiliteit
                        thumb_quality = 20  # Verlaagd naar 20% voor 5G compatibiliteit

                        # NIEUW: Verbeterde thumbnail creatie
                        thumbnail_img = img.copy()
                        thumbnail_img = thumbnail_img.resize(
                            (thumb_width, int(thumb_width * img.height / img.width)), Image.Resampling.LANCZOS
                        )

                        # NIEUW: Converteer naar RGB indien nodig (voor PNG met transparantie)
                        if thumbnail_img.mode in ("RGBA", "LA"):
                            background = Image.new("RGB", thumbnail_img.size, (255, 255, 255))
                            background.paste(thumbnail_img, mask=thumbnail_img.split()[3] if len(thumbnail_img.split()) > 3 else None)
                            thumbnail_img = background

                        with io.BytesIO() as buffer:
                            # 5G optimalisatie: sterkere blur
                            blur_radius = 0.5 if USE_5G_OPTIMIZATION else 0.3  # Verhoogd naar 0.5 voor 5G
                            thumbnail_img = thumbnail_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                            enhancer = ImageEnhance.Contrast(thumbnail_img)
                            # 5G optimalisatie: meer contrast reductie
                            contrast_factor = 0.9 if USE_5G_OPTIMIZATION else 0.95  # Verlaagd naar 0.9 voor 5G
                            thumbnail_img = enhancer.enhance(contrast_factor)
                            buffer = io.BytesIO()
                            # 5G optimalisatie: nog lagere kwaliteit
                            final_quality = thumb_quality-8 if USE_5G_OPTIMIZATION else thumb_quality-5  # Extra -3% voor 5G
                            thumbnail_img.save(buffer, format="JPEG", quality=final_quality, optimize=True)
                            
                            # NIEUW: Validatie en extra compressie indien nodig
                            if len(buffer.getvalue()) > MAX_COMPRESSED_SIZE:
                                # Nog agressievere compressie
                                self.logger.warning(f"[IMAGE LOADING] Thumbnail te groot: {len(buffer.getvalue())/1024:.2f}KB")
                                # 5G optimalisatie: nog kleinere thumbs
                                resize_width = 90 if USE_5G_OPTIMIZATION else 140  # Verlaagd naar 90px voor 5G
                                thumbnail_img = thumbnail_img.resize((resize_width, int(resize_width * thumbnail_img.height / thumbnail_img.width)), 
                                                                        Image.Resampling.LANCZOS)
                                with io.BytesIO() as buffer:
                                    # 5G optimalisatie: extreme compressie
                                    final_quality = 12 if USE_5G_OPTIMIZATION else 20  # Verlaagd naar 12% voor 5G
                                    thumbnail_img.save(buffer, format="JPEG", quality=final_quality, optimize=True)

                            # Veilige base64 encoding
                            try:
                                thumbnail_data_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                                self.logger.info(f"[IMAGE LOADING] Thumbnail grootte: {len(buffer.getvalue())/1024:.2f}KB, Base64: {len(thumbnail_data_b64)/1024:.2f}KB")
                                return f"data:image/jpeg;base64,{thumbnail_data_b64}"
                            except Exception as b64_error:
                                self.logger.error(f"[IMAGE LOADING] Base64 encoding fout: {str(b64_error)}")
                                # Verkleinen en opnieuw proberen
                                img = img.resize((140, int(140 * img.height / img.width)), Image.Resampling.LANCZOS)
                                with io.BytesIO() as buffer:
                                    img.save(buffer, format="JPEG", quality=20, optimize=True)
                                    buffer.seek(0)
                                    image_data = buffer.getvalue()
                                
                                    image_data_b64 = base64.b64encode(image_data).decode("utf-8")
                                    self.logger.info(f"[IMAGE LOADING] Na base64 error herstel: {len(image_data)/1024:.2f}KB, base64: {len(image_data_b64)/1024:.2f}KB")

                            compression_ratio = (original_size - len(buffer.getvalue())) / original_size * 100
                            self.logger.info(f"[IMAGE LOADING] Compressie ratio: {compression_ratio:.2f}% verkleind")
                            self.logger.info(
                                f"[IMAGE LOADING] Uiteindelijke afmetingen: {img.width}x{img.height}, kwaliteit: {quality}%"
                            )

                            # AANGEPAST: Verlaagde drempel voor streaming limiet
                            if needs_streaming_optimization and len(buffer.getvalue()) > 400 * 1024:  # Verlaagd van 500K naar 400K
                                self.logger.warning(
                                    f"[IMAGE LOADING] Streaming limiet overschreden: {len(buffer.getvalue()) / 1024:.2f}KB > 400KB, extra compressie nodig"
                                )
                                # Extra agressieve verkleining voor streaming
                                img = img.resize((140, int(140 * img.height / img.width)), Image.Resampling.LANCZOS)  # Verlaagd van 180 naar 140
                                
                                # NIEUW: Extreme optimalisatie voor streaming
                                try:
                                    from PIL import ImageFilter, ImageEnhance
                                    # Compressie-vriendelijke filters toepassen
                                    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
                                    enhancer = ImageEnhance.Contrast(img)
                                    img = enhancer.enhance(0.9)
                                except Exception as extreme_error:
                                    self.logger.warning(f"[IMAGE LOADING] Extreme optimalisatie niet mogelijk: {str(extreme_error)}")
                                    
                                with io.BytesIO() as buffer:
                                    img.save(buffer, format="JPEG", quality=22, optimize=True)  # Verlaagd van 30 naar 22

                            # AANGEPAST: Verlaagde drempel voor kritische waarschuwing
                            if len(buffer.getvalue()) > 300 * 1024:  # Verlaagd van 500KB naar 300KB
                                self.logger.warning(
                                    f"[IMAGE LOADING] Base64 output is zeer groot ({len(buffer.getvalue()) / 1024 / 1024:.2f} MB)"
                                )
                                # NIEUW: Extra fallback voor zeer grote base64 data
                                img = img.resize((120, int(120 * img.height / img.width)), Image.Resampling.LANCZOS)  # Verlaagd van 140 naar 120
                                
                                # NIEUW: Extreme compressie voor chat streaming
                                try:
                                    from PIL import ImageFilter, ImageEnhance
                                    # Meer blur en contrast reductie voor extreme compressie
                                    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
                                    enhancer = ImageEnhance.Contrast(img)
                                    img = enhancer.enhance(0.85)
                                    # Lichte vermindering van scherpte
                                    enhancer = ImageEnhance.Sharpness(img)
                                    img = enhancer.enhance(0.8)
                                except Exception as extreme_error:
                                    self.logger.warning(f"[IMAGE LOADING] Extreme compressie filters niet mogelijk: {str(extreme_error)}")
                                    
                                with io.BytesIO() as buffer:
                                    img.save(buffer, format="JPEG", quality=15, optimize=True)  # Verlaagd van 20 naar 15
                                    buffer.seek(0)
                                    image_data = buffer.getvalue()

                            # Check of base64 misschien te groot is voor chat interface
                            data_url = f"data:image/jpeg;base64,{image_data_b64}"

                            # Waarschuwing voor trage verbindingen zonder de afbeelding te vervangen
                            if needs_streaming_optimization:
                                self.logger.info(
                                    "[IMAGE LOADING] ===== EINDE AFBEELDING VERWERKING (STREAMING GEOPTIMALISEERD) ====="
                                )
                                self.logger.info(
                                    f"[IMAGE LOADING] GROOTTE SAMENVATTING: Origineel: {original_size_mb:.2f} MB, Verwerkt: {len(buffer.getvalue()) / 1024:.2f} MB, Base64: {len(image_data_b64) / 1024:.2f} KB"
                                )
                                if not is_very_large_image:
                                    return data_url

                            # AANGEPAST: Verlaagde drempel voor kritische waarschuwing
                            if len(buffer.getvalue()) > 500 * 1024:  # Verlaagd van 600KB naar 500KB
                                self.logger.warning(
                                    f"[IMAGE LOADING] Base64 output is zeer groot ({len(buffer.getvalue()) / 1024 / 1024:.2f} MB)"
                                )
                                # NIEUW: Extra fallback voor zeer grote base64 data
                                img = img.resize((140, int(140 * img.height / img.width)), Image.Resampling.LANCZOS)  # Verlaagd van 160 naar 140
                                
                                # NIEUW: Extreme compressie voor chat streaming
                                try:
                                    from PIL import ImageFilter, ImageEnhance
                                    # Meer blur en contrast reductie voor extreme compressie
                                    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
                                    enhancer = ImageEnhance.Contrast(img)
                                    img = enhancer.enhance(0.85)
                                except Exception as extreme_error:
                                    self.logger.warning(f"[IMAGE LOADING] Extreme compressie filters niet mogelijk: {str(extreme_error)}")
                                    
                                with io.BytesIO() as buffer:
                                    img.save(buffer, format="JPEG", quality=15, optimize=True)  # Verlaagd van 20 naar 15
                                    buffer.seek(0)
                                    image_data = buffer.getvalue()

                            if is_very_large_image:
                                self.logger.info("[IMAGE LOADING] ===== EINDE AFBEELDING VERWERKING (GROOT) =====")
                                self.logger.info(
                                    f"[IMAGE LOADING] GROOTTE SAMENVATTING: Origineel: {original_size_mb:.2f} MB, Verwerkt: {len(buffer.getvalue()) / 1024:.2f} MB, Base64: {len(image_data_b64) / 1024:.2f} KB"
                                )
                                return data_url

                            self.logger.info("[IMAGE LOADING] ===== EINDE AFBEELDING VERWERKING (SUCCES) =====")
                            self.logger.info(
                                f"[IMAGE LOADING] GROOTTE SAMENVATTING: Origineel: {original_size_mb:.2f} MB, Verwerkt: {len(buffer.getvalue()) / 1024:.2f} MB, Base64: {len(image_data_b64) / 1024:.2f} KB"
                            )
                            return data_url

                        except Exception as img_error:
                            self.logger.error(f"[IMAGE LOADING] Fout bij verkleinen afbeelding: {str(img_error)}")
                            import traceback

                            self.logger.error(f"[IMAGE LOADING] Details fout: {traceback.format_exc()}")

                            # AANGEPAST: Verbeterde fallback voor fouten
                            try:
                                if img is not None:
                                    # Creëer de meest eenvoudige versie mogelijk
                                    img = img.resize((140, int(140 * img.height / img.width)), Image.Resampling.LANCZOS)  # Verlaagd van 160 naar 140
                                    
                                    # NIEUW: Zorg dat de afbeelding in RGB-modus is
                                    if img.mode in ("RGBA", "LA"):
                                        background = Image.new("RGB", img.size, (255, 255, 255))
                                        background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                                        img = background
                                    
                                    with io.BytesIO() as buffer:
                                        img.save(buffer, format="JPEG", quality=25, optimize=True)  # Verlaagd van 30 naar 25
                                        buffer.seek(0)
                                        image_data = buffer.getvalue()
                                    
                                    # NIEUW: Valideer base64 encoding
                                    try:
                                        image_data_b64 = base64.b64encode(image_data).decode("utf-8")
                                        data_url = f"data:image/jpeg;base64,{image_data_b64}"
                                        return data_url
                                    except Exception as b64_error:
                                        self.logger.error(f"[IMAGE LOADING] Base64 encoding fout in foutfallback: {str(b64_error)}")
                            except Exception as second_error:
                                self.logger.error(f"[IMAGE LOADING] Fallback ook mislukt: {str(second_error)}")

                            return f"Er is een fout opgetreden bij het verwerken van de afbeelding. De afbeelding is waarschijnlijk te groot of ongeldig."

                    except Exception as e:
                        self.logger.error(f"[IMAGE LOADING] Onverwachte fout bij laden afbeelding: {str(e)}")
                        import traceback

                        self.logger.error(f"[IMAGE LOADING] Stacktrace: {traceback.format_exc()}")
                        return f"Fout bij laden afbeelding: {str(e)}"

                except Exception as img_error:
                    self.logger.error(f"[IMAGE LOADING] Fout bij verkleinen afbeelding: {str(img_error)}")
                    import traceback

                    self.logger.error(f"[IMAGE LOADING] Details fout: {traceback.format_exc()}")

                    # AANGEPAST: Verbeterde fallback voor fouten
                    try:
                        if img is not None:
                            # Creëer de meest eenvoudige versie mogelijk
                            img = img.resize((140, int(140 * img.height / img.width)), Image.Resampling.LANCZOS)  # Verlaagd van 160 naar 140
                            
                            # NIEUW: Zorg dat de afbeelding in RGB-modus is
                            if img.mode in ("RGBA", "LA"):
                                background = Image.new("RGB", img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                                img = background
                            
                            with io.BytesIO() as buffer:
                                img.save(buffer, format="JPEG", quality=25, optimize=True)  # Verlaagd van 30 naar 25
                                buffer.seek(0)
                                image_data = buffer.getvalue()
                            
                            # NIEUW: Valideer base64 encoding
                            try:
                                image_data_b64 = base64.b64encode(image_data).decode("utf-8")
                                data_url = f"data:image/jpeg;base64,{image_data_b64}"
                                return data_url
                            except Exception as b64_error:
                                self.logger.error(f"[IMAGE LOADING] Base64 encoding fout in foutfallback: {str(b64_error)}")
                    except Exception as second_error:
                        self.logger.error(f"[IMAGE LOADING] Fallback ook mislukt: {str(second_error)}")

                    return f"Er is een fout opgetreden bij het verwerken van de afbeelding. De afbeelding is waarschijnlijk te groot of ongeldig."

            except Exception as e:
                self.logger.error(f"[IMAGE LOADING] Onverwachte fout bij laden afbeelding: {str(e)}")
                import traceback

                self.logger.error(f"[IMAGE LOADING] Stacktrace: {traceback.format_exc()}")
                return f"Fout bij laden afbeelding: {str(e)}"

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
            # Expliciet alle tool-namen die we willen behouden
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
                # Probeer de naam op beide manieren te krijgen (als object met function attribuut of als dict)
                if hasattr(tool, "function") and hasattr(tool.function, "name"):
                    self.logger.info(f" - {i + 1}: {tool.function.name}")
                elif isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                    self.logger.info(f" - {i + 1}: {tool['function']['name']}")
                else:
                    self.logger.info(f" - {i + 1}: {str(tool)[:50]}")  # Log een deel van het object als fallback
            except Exception as e:
                self.logger.warning(f" - {i + 1}: Error logging tool: {str(e)}")

        start_time = time.time()

        stream = await self.client.messages.create(
            # Gebruik Claude 3.7 Sonnet model
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            system=f"""Je bent een vriendelijke en behulpzame data-analist voor EasyLog.
Je taak is om gebruikers te helpen bij het analyseren van bedrijfsgegevens en het maken van overzichtelijke verslagen.

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke samenvattingen van de EasyLog data!
- Help de gebruiker patronen te ontdekken in de controlegegevens
- Maak verslagen in tabellen end uidelijk en professioneel met goede opmaak
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
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        if execution_time > 5.0:
            logger.warning(f"API call took longer than expected: {execution_time:.2f} seconds")

        async for content in self.handle_stream(
            stream,
            tools,
        ):
            if self.config.debug_mode:
                self.logger.debug(f"Streaming content: {str(content)[:100]}...")
            yield content
