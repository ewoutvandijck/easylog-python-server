# Python standard library imports
import base64
import io
import json
import mimetypes
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
            self.logger.info(f"[IMAGE LOADING] Start verwerking voor afbeelding {_id}, {file_name}")

            try:
                # Laad de originele afbeelding
                image_data = await self.load_image(_id, file_name)
                original_size = len(image_data)
                original_size_mb = original_size / (1024 * 1024)
                mime_type = mimetypes.guess_type(file_name)[0] or "image/jpeg"
                self.logger.info(f"[IMAGE LOADING] Afbeelding geladen: {original_size / 1024:.2f} KB, type {mime_type}")

                # Constanten voor compressielimieten
                IMAGE_SIZE_THRESHOLDS = {
                    "THUMBNAIL": 500 * 1024,  # 500KB - Directe thumbnail trigger
                    "VERY_LARGE": 1.5 * 1024 * 1024,  # 1.5MB - Zeer grote afbeelding
                    "STREAMING": 1 * 1024 * 1024,  # 1MB - Streaming optimalisatie
                    "MAX_OUTPUT": 80 * 1024,  # 80KB - Max gecomprimeerde grootte
                    "MAX_STREAMING": 160 * 1024,  # 160KB - Hard streaming limit
                }

                try:
                    # Laad de afbeelding in PIL
                    img = Image.open(io.BytesIO(image_data))
                    original_width, original_height = img.size
                    self.logger.info(f"[IMAGE LOADING] Originele afmetingen: {original_width}x{original_height}")

                    # Bepaal optimalisatiestrategie op basis van afbeeldingsgrootte
                    needs_streaming = original_size > IMAGE_SIZE_THRESHOLDS["STREAMING"]
                    is_very_large = original_size > IMAGE_SIZE_THRESHOLDS["VERY_LARGE"]
                    force_thumbnail = original_size > IMAGE_SIZE_THRESHOLDS["THUMBNAIL"]

                    # Directe thumbnail voor zeer grote afbeeldingen
                    if original_size > 2 * 1024 * 1024:
                        self.logger.warning(
                            f"[IMAGE LOADING] Extreem grote afbeelding ({original_size_mb:.2f} MB), directe thumbnail genereren"
                        )
                        return self._create_thumbnail(img, width=140, quality=25)

                    # Voor grote afbeeldingen die thumbnails vereisen
                    if needs_streaming and force_thumbnail:
                        self.logger.info(
                            f"[IMAGE LOADING] Grote afbeelding ({original_size_mb:.2f} MB), thumbnail genereren"
                        )
                        return self._create_thumbnail(img, width=160, quality=30)

                    # Bepaal doelinstellingen voor compressie gebaseerd op grootte
                    if is_very_large:
                        target_width = 240
                        quality = 40
                    elif original_size > 500 * 1024:
                        target_width = 400
                        quality = 50
                    else:
                        target_width = min(self.config.image_max_width, 560)
                        quality = min(60, self.config.image_quality)

                    self.logger.info(f"[IMAGE LOADING] Doelinstellingen: {target_width}px breed, {quality}% kwaliteit")

                    # Verwerk en comprimeer de afbeelding
                    return self._process_and_compress_image(
                        img, target_width, quality, original_size, needs_streaming, is_very_large, IMAGE_SIZE_THRESHOLDS
                    )

                except Exception as img_error:
                    self.logger.error(f"[IMAGE LOADING] Fout bij verwerken afbeelding: {str(img_error)}")
                    import traceback

                    self.logger.error(f"[IMAGE LOADING] Stacktrace: {traceback.format_exc()}")

                    # Vang op zijn minst op als we een img hebben kunnen laden
                    if "img" in locals() and img is not None:
                        return self._create_thumbnail(img, width=140, quality=20)

                    return "Er is een fout opgetreden bij het verwerken van de afbeelding."

            except Exception as e:
                self.logger.error(f"[IMAGE LOADING] Onverwachte fout: {str(e)}")
                return f"Fout bij laden afbeelding: {str(e)}"

        def _create_thumbnail(self, img, width=160, quality=30):
            """Helper functie om een kleine thumbnail te maken van een afbeelding"""
            try:
                # Maak een kopie en resize
                thumb_img = img.copy()
                thumb_height = int(width * thumb_img.height / thumb_img.width)
                thumb_img = thumb_img.resize((width, thumb_height), Image.Resampling.LANCZOS)

                # Zorg dat het RGB is (voor afbeeldingen met transparantie)
                if thumb_img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", thumb_img.size, (255, 255, 255))
                    background.paste(thumb_img, mask=thumb_img.split()[3] if len(thumb_img.split()) > 3 else None)
                    thumb_img = background

                # Probeer extra compressie met filters toe te passen
                try:
                    from PIL import ImageEnhance, ImageFilter

                    thumb_img = thumb_img.filter(ImageFilter.GaussianBlur(radius=0.3))
                    enhancer = ImageEnhance.Contrast(thumb_img)
                    thumb_img = enhancer.enhance(0.95)
                except Exception:
                    self.logger.warning("[IMAGE LOADING] Extra filters niet toegepast")

                # Sla op naar buffer
                with io.BytesIO() as buffer:
                    thumb_img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    thumb_data = buffer.getvalue()

                # Encodeer naar base64
                thumb_data_b64 = base64.b64encode(thumb_data).decode("utf-8")
                self.logger.info(
                    f"[IMAGE LOADING] Thumbnail: {len(thumb_data) / 1024:.2f}KB, Base64: {len(thumb_data_b64) / 1024:.2f}KB"
                )
                return f"data:image/jpeg;base64,{thumb_data_b64}"
            except Exception as e:
                self.logger.error(f"[IMAGE LOADING] Thumbnail error: {str(e)}")
                return "Er is een fout opgetreden bij het maken van de thumbnail."

        def _process_and_compress_image(
            self, img, target_width, quality, original_size, needs_streaming, is_very_large, thresholds
        ):
            """Verwerkt en comprimeert een afbeelding naar de gewenste specificaties"""

            # Resize indien nodig
            if img.width > target_width:
                scale_factor = target_width / img.width
                new_height = int(img.height * scale_factor)
                img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"[IMAGE LOADING] Verkleind naar: {img.width}x{img.height}")

            # Converteer naar RGB indien nodig
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                img = background

            # Extra verkleining voor zeer grote afbeeldingen
            if is_very_large:
                img = img.resize((220, int(220 * img.height / img.width)), Image.Resampling.LANCZOS)
                quality = 35
                self.logger.info("[IMAGE LOADING] Zeer grote afbeelding extra verkleind naar 220px")

                try:
                    from PIL import ImageFilter

                    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
                except Exception:
                    pass

            # Eerste compressiepoging
            with io.BytesIO() as buffer:
                img.save(buffer, format="JPEG", quality=quality, optimize=True)
                buffer.seek(0)
                image_data = buffer.getvalue()
            image_size = len(image_data)

            # Streaming optimalisatie indien nodig
            if needs_streaming and image_size > thresholds["MAX_STREAMING"]:
                img = img.resize((160, int(160 * img.height / img.width)), Image.Resampling.LANCZOS)
                with io.BytesIO() as buffer:
                    img.save(buffer, format="JPEG", quality=30, optimize=True)
                    buffer.seek(0)
                    image_data = buffer.getvalue()
                image_size = len(image_data)

            # Iteratieve compressie indien nog steeds te groot
            if image_size > thresholds["MAX_OUTPUT"]:
                image_data = self._iterative_compression(img, image_size, thresholds["MAX_OUTPUT"])

            # Encodeer naar base64
            image_data_b64 = base64.b64encode(image_data).decode("utf-8")
            base64_size = len(image_data_b64)

            # Extra optimalisatie indien base64 te groot voor streaming
            if needs_streaming and base64_size > 400 * 1024:
                return self._create_thumbnail(img, width=140, quality=20)

            # Logging van eindresultaten
            self.logger.info(
                f"[IMAGE LOADING] Compressie resultaat: {image_size / 1024:.2f}KB -> {base64_size / 1024:.2f}KB base64"
            )
            compression_ratio = (original_size - image_size) / original_size * 100
            self.logger.info(f"[IMAGE LOADING] Compressie ratio: {compression_ratio:.2f}% verkleind")

            return f"data:image/jpeg;base64,{image_data_b64}"

        def _iterative_compression(self, img, current_size, target_size, max_attempts=5):
            """Stapsgewijze compressie om de afbeelding onder de doelgrootte te krijgen"""
            img_copy = img.copy()
            image_data = None
            quality = 60
            attempt = 0

            while current_size > target_size and attempt < max_attempts:
                attempt += 1

                # Verlaag kwaliteit met grotere stappen bij latere pogingen
                quality = max(18, quality - (15 if attempt <= 2 else 10))

                # Kleinere afbeelding als kwaliteitsverlaging niet voldoende is
                if attempt > 1:
                    resize_factor = 0.65 if attempt == 2 else 0.5
                    new_width = int(img_copy.width * resize_factor)
                    new_height = int(img_copy.height * resize_factor)
                    img_copy = img_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Extra filters bij latere iteraties
                if attempt > 2:
                    try:
                        from PIL import ImageEnhance, ImageFilter

                        blur_radius = min(0.5, 0.2 + (attempt - 2) * 0.1)
                        img_copy = img_copy.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                        if attempt > 3:
                            enhancer = ImageEnhance.Contrast(img_copy)
                            img_copy = enhancer.enhance(0.9)
                    except Exception:
                        pass

                # Opnieuw opslaan met nieuwe instellingen
                with io.BytesIO() as buffer:
                    img_copy.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    image_data = buffer.getvalue()

                current_size = len(image_data)
                self.logger.info(
                    f"[IMAGE LOADING] Iteratie {attempt}: {img_copy.width}x{img_copy.height}, kwaliteit {quality}%, grootte {current_size / 1024:.2f}KB"
                )

            return image_data

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
