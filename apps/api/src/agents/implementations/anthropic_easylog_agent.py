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
        Detecteert automatisch belangrijke informatie in het bericht van de gebruiker!!

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

        async def _load_image_data(self, _id: str, file_name: str, timeout: float = 15.0) -> Image.Image | None:
            """
            Attempts to load image data using various possible paths with timeout protection.
            
            Args:
                _id: The ID of the associated knowledge object
                file_name: The filename of the image
                timeout: Maximum time in seconds to wait for image loading
                
            Returns:
                The loaded image or None if loading failed
                
            Raises:
                Exception: If image loading fails with all paths or times out
            """
            import asyncio
            from concurrent.futures import TimeoutError
            
            possible_paths = [
                file_name,
                f"figures/{file_name}" if "/" not in file_name else file_name,
                file_name.replace("figures/", "") if file_name.startswith("figures/") else file_name,
                file_name.split("/")[-1],  # Just the filename
            ]

            self.logger.debug(f"[IMAGE_DEBUG] Attempting to load image with timeout {timeout}s")
            start_time = time.time()
            
            image_data = None
            last_error = None
            
            for path in possible_paths:
                # Check if we've exceeded our overall timeout
                if time.time() - start_time > timeout:
                    self.logger.warning(f"[IMAGE_DEBUG] Overall image loading timeout exceeded ({timeout}s)")
                    break
                    
                try:
                    # Set a timeout for this specific path attempt
                    path_timeout = min(5.0, timeout - (time.time() - start_time))
                    if path_timeout <= 0:
                        break
                        
                    self.logger.debug(f"[IMAGE_DEBUG] Trying path '{path}' with {path_timeout:.1f}s timeout")
                    
                    # Use asyncio.wait_for to implement the timeout
                    try:
                        image_data = await asyncio.wait_for(
                            self.load_image(_id, path),
                            timeout=path_timeout
                        )
                        load_time = time.time() - start_time
                        self.logger.info(f"[IMAGE] Successfully loaded with path: {path} in {load_time:.2f}s")
                        return image_data  # Return as soon as loaded
                    except TimeoutError:
                        self.logger.warning(f"[IMAGE_DEBUG] Timeout loading image with path: {path}")
                        last_error = TimeoutError(f"Timeout loading image with path: {path}")
                        continue
                        
                except Exception as e:
                    last_error = e
                    self.logger.debug(f"[IMAGE] Failed to load with path {path}: {e}")
                    continue

            total_time = time.time() - start_time
            if image_data is None:
                self.logger.error(f"[IMAGE] Could not load image {_id}/{file_name} with any path in {total_time:.2f}s. Last error: {last_error}")
                raise last_error or Exception("Kon afbeelding niet laden met beschikbare paden")
            return None # Should not be reached if exception is raised, but satisfies linter

        def _convert_heic_to_jpeg(self, image_data: Image.Image) -> Image.Image:
            """Converts HEIC images to JPEG format."""
            if hasattr(image_data, 'format') and image_data.format == 'HEIC':
                try:
                    with io.BytesIO() as buffer:
                        # Use a reasonable quality for conversion
                        image_data.save(buffer, format="JPEG", quality=85)
                        buffer.seek(0)
                        converted_image = Image.open(buffer)
                        # Important: Make a copy to avoid issues with the buffer closing
                        image_data = converted_image.copy()
                        self.logger.info("[IMAGE] Converted HEIC to JPEG format")
                        return image_data
                except Exception as e:
                    self.logger.error(f"[IMAGE] Error converting HEIC: {str(e)}")
                    # Return original image if conversion fails
                    return image_data
            return image_data

        def _get_image_size_kb(self, image: Image.Image, format: str = "JPEG") -> float:
            """Calculates the size of the image in kilobytes."""
            with io.BytesIO() as buffer:
                save_format = format if format else image.format or "PNG"
                try:
                    self.logger.debug(f"[IMAGE_DEBUG] Calculating size for image mode={image.mode}, format={save_format}")
                    image.save(buffer, format=save_format)
                    size_bytes = len(buffer.getvalue())
                    self.logger.debug(f"[IMAGE_DEBUG] Raw image size: {size_bytes} bytes ({size_bytes/1024:.2f} KB)")
                    return size_bytes / 1024
                except Exception as e:
                    self.logger.warning(f"[IMAGE] Could not determine image size for format {save_format}: {e}")
                    # Fallback for modes like 'P' that might not save directly to JPEG without conversion
                    if image.mode != "RGB":
                        self.logger.info(f"[IMAGE] Converting {image.mode} to RGB for size calculation")
                        rgb_image = image.convert("RGB")
                        return self._get_image_size_kb(rgb_image, format="JPEG")
                    return 0.0


        def _compress_image(self, image_data: Image.Image, target_kb: int = 150) -> tuple[Image.Image, float]:
            """Compresses the image to be below a target size in KB."""
            original_width, original_height = image_data.size
            original_size_kb = self._get_image_size_kb(image_data)
            self.logger.info(f"[IMAGE] Original size: {original_size_kb:.1f} KB ({original_width}x{original_height})")
            self.logger.debug(f"[IMAGE_DEBUG] Image mode: {image_data.mode}, format: {getattr(image_data, 'format', 'Unknown')}")

            # Ensure image is in RGB format for JPEG saving
            if image_data.mode in ("RGBA", "LA", "P"):
                self.logger.debug(f"[IMAGE_DEBUG] Converting from {image_data.mode} mode to RGB")
                # Preserve transparency by pasting onto a white background
                if image_data.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", image_data.size, (255, 255, 255))
                    mask = image_data.split()[3] if len(image_data.split()) > 3 else None
                    background.paste(image_data, mask=mask)
                    image_data = background
                    self.logger.debug("[IMAGE_DEBUG] Applied transparency handling with white background")
                else: # Handle 'P' mode (palette-based)
                    image_data = image_data.convert("RGB")
                    self.logger.debug("[IMAGE_DEBUG] Converted palette-based image to RGB")


            # --- Step 1: Initial Resize and Quality Adjustment ---
            current_image = image_data.copy()
            max_width = self.config.image_max_width
            quality = self.config.image_quality

            if current_image.width > max_width:
                scale_factor = max_width / current_image.width
                new_height = int(current_image.height * scale_factor)
                self.logger.info(f"[IMAGE] Resizing to {max_width}x{new_height}")
                current_image = current_image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            with io.BytesIO() as buffer:
                current_image.save(buffer, format="JPEG", quality=quality, optimize=True)
                compressed_data = buffer.getvalue()
                current_size_kb = len(compressed_data) / 1024

            self.logger.info(f"[IMAGE] After initial compression (Q={quality}, W<={max_width}): {current_size_kb:.1f} KB")

            # --- Step 2: Multi-stage Compression for Poor Connections ---
            if current_size_kb > target_kb:
                self.logger.info(f"[IMAGE] Size ({current_size_kb:.1f} KB) exceeds target ({target_kb} KB). Applying aggressive compression.")
                
                # Define compression stages with increasingly aggressive settings
                compression_stages = [
                    # Stage 1: Moderate compression
                    {"scale": 0.8, "quality": max(50, quality - 15), "blur": 0.3},
                    # Stage 2: More aggressive
                    {"scale": 0.7, "quality": max(40, quality - 25), "blur": 0.5},
                    # Stage 3: Very aggressive (last resort)
                    {"scale": 0.6, "quality": max(30, quality - 35), "blur": 0.8}
                ]
                
                # Try each compression stage until target is met or all stages exhausted
                for stage_num, stage in enumerate(compression_stages, 1):
                    # Apply stage settings
                    agg_width = int(current_image.width * stage["scale"])
                    agg_height = int(current_image.height * stage["scale"])
                    agg_quality = stage["quality"]
                    
                    self.logger.debug(f"[IMAGE_DEBUG] Compression stage {stage_num}: scale={stage['scale']}, " +
                                     f"quality={agg_quality}, dimensions={agg_width}x{agg_height}")
                    
                    # Resize image
                    current_image = current_image.resize((agg_width, agg_height), Image.Resampling.LANCZOS)
                    
                    # Apply blur if available (helps JPEG compression)
                    try:
                        from PIL import ImageFilter
                        current_image = current_image.filter(ImageFilter.GaussianBlur(radius=stage["blur"]))
                        self.logger.debug(f"[IMAGE_DEBUG] Applied Gaussian blur with radius {stage['blur']}")
                    except (ImportError, Exception) as e:
                        self.logger.debug(f"[IMAGE_DEBUG] Skipping blur: {str(e)}")
                    
                    # Check size after this stage
                    with io.BytesIO() as buffer:
                        current_image.save(buffer, format="JPEG", quality=agg_quality, optimize=True)
                        current_size_kb = len(buffer.getvalue()) / 1024
                    
                    self.logger.info(f"[IMAGE] After compression stage {stage_num}: {current_size_kb:.1f} KB")
                    
                    # If we're under target, stop compression
                    if current_size_kb <= target_kb * 1.1:  # Allow 10% over target
                        self.logger.info(f"[IMAGE] Target size achieved at stage {stage_num}")
                        break
                
                # Apply additional JPEG optimization techniques for stubborn images
                if current_size_kb > target_kb * 1.2:
                    self.logger.warning(f"[IMAGE] Still over target after all compression stages: {current_size_kb:.1f} KB")
                    
                    try:
                        # Convert to grayscale as last resort if still too large
                        if current_size_kb > target_kb * 1.5:
                            self.logger.warning("[IMAGE_DEBUG] Converting to grayscale as last resort")
                            current_image = current_image.convert("L")
                            
                            with io.BytesIO() as buffer:
                                current_image.save(buffer, format="JPEG", quality=40, optimize=True)
                                current_size_kb = len(buffer.getvalue()) / 1024
                            
                            self.logger.info(f"[IMAGE] After grayscale conversion: {current_size_kb:.1f} KB")
                    except Exception as e:
                        self.logger.error(f"[IMAGE_DEBUG] Error in last-resort compression: {str(e)}")

            # --- Final Check ---
            if current_size_kb > target_kb * 1.2: # Allow slightly over target
                 self.logger.warning(f"[IMAGE] Final size {current_size_kb:.1f} KB still significantly over target {target_kb} KB.")
                 self.logger.warning("[IMAGE_DEBUG] Image may have issues on poor connections")


            final_size_kb = current_size_kb
            return current_image, final_size_kb

        def _verify_image_integrity(self, image_data: Image.Image) -> bool:
            """
            Verifies that the image data is valid and can be properly encoded/decoded.
            This helps catch corrupted images before attempting to send them.
            
            Args:
                image_data (Image.Image): The image to verify
                
            Returns:
                bool: True if the image passes integrity checks, False otherwise
            """
            try:
                # Test if we can encode and decode the image without errors
                with io.BytesIO() as buffer:
                    # Try to save the image to the buffer
                    image_data.save(buffer, format="JPEG", quality=85)
                    buffer_size = len(buffer.getvalue())
                    
                    # Check if the buffer has reasonable content
                    if buffer_size < 100:  # Suspiciously small
                        self.logger.warning(f"[IMAGE_DEBUG] Image verification failed: suspiciously small size ({buffer_size} bytes)")
                        return False
                    
                    # Try to reload the image from the buffer
                    buffer.seek(0)
                    test_image = Image.open(buffer)
                    test_image.load()  # Force load the image data
                    
                    # Check dimensions match
                    if test_image.size != image_data.size:
                        self.logger.warning(f"[IMAGE_DEBUG] Image verification failed: size mismatch after reload")
                        return False
                        
                    self.logger.debug(f"[IMAGE_DEBUG] Image passed integrity verification: {buffer_size} bytes")
                    return True
                    
            except Exception as e:
                self.logger.error(f"[IMAGE_DEBUG] Image verification failed with error: {str(e)}")
                return False
        
        def _add_assistant_identifier(self, image_data: Image.Image) -> Image.Image:
            """Adds a subtle pixel pattern to identify the image as assistant-generated."""
            try:
                if image_data.width > 5 and image_data.height > 5 and image_data.mode == "RGB":
                    pixels = image_data.load()
                    if pixels:
                         # Specific pattern: 3 pixels in bottom-right corner with specific RGB values
                         pixels[image_data.width-1, image_data.height-1] = (250, 250, 253) # Bottom-right
                         pixels[image_data.width-2, image_data.height-1] = (250, 250, 252) # One left
                         pixels[image_data.width-1, image_data.height-2] = (250, 250, 251) # One up
                         self.logger.info("[IMAGE] Added assistant image identifier pattern.")
            except Exception as e:
                 # Log error but don't fail the whole process if identifier can't be added
                self.logger.error(f"[IMAGE] Error adding assistant identifier: {str(e)}")
            return image_data


        async def tool_load_image(self, _id: str, file_name: str) -> Image.Image:
            """
            Loads, processes (converts, compresses), and returns an image from the database.
            It attempts various paths, converts HEIC, compresses to a target size,
            and adds an identifier for client-side detection.

            Args:
                _id (str): The ID of the associated knowledge object (e.g., PDF).
                file_name (str): The filename of the image (potentially including path).

            Returns:
                Image.Image: The processed PIL Image object.

            Raises:
                Exception: If the image cannot be loaded or processed.
            """
            start_time = time.time()
            self.logger.info(f"[IMAGE] Processing request for image: {_id}/{file_name}")
            self.logger.debug(f"[IMAGE_DEBUG] Image processing started at: {start_time}")

            try:
                # 1. Load Image Data
                image_data = await self._load_image_data(_id, file_name)
                if not image_data: # Should have raised in helper, but check defensively
                    raise ValueError("Failed to load image data.")

                # 2. Convert HEIC if necessary
                image_data = self._convert_heic_to_jpeg(image_data)
                
                # --- Start Processing for Output ---
                # Keep track of original size for logging comparison
                original_size_kb = self._get_image_size_kb(image_data)

                # 3. Compress Image
                # Target size set significantly below typical network limits for safety margin
                target_kb = 100  # Reduced from 140 to be more conservative
                self.logger.debug(f"[IMAGE_DEBUG] Using more aggressive target size: {target_kb}KB for compression")
                processed_image, compressed_size_kb = self._compress_image(image_data, target_kb=target_kb)

                # 4. Add Identifier Pattern
                processed_image = self._add_assistant_identifier(processed_image)
                
                # 5. Verify image integrity
                if not self._verify_image_integrity(processed_image):
                    self.logger.warning("[IMAGE_DEBUG] Image failed integrity check, attempting recovery...")
                    # Try more aggressive compression as recovery
                    recovery_target_kb = 80
                    self.logger.debug(f"[IMAGE_DEBUG] Recovery compression with target: {recovery_target_kb}KB")
                    processed_image, compressed_size_kb = self._compress_image(processed_image, target_kb=recovery_target_kb)
                    
                    # Verify again
                    if not self._verify_image_integrity(processed_image):
                        self.logger.error("[IMAGE_DEBUG] Image still fails integrity check after recovery attempt")
                        # Continue anyway, but log the issue
                
                # Extra verification of final image size
                final_size_kb = self._get_image_size_kb(processed_image)
                self.logger.debug(f"[IMAGE_DEBUG] Verified final image size: {final_size_kb:.2f}KB")

                # 5. Final Logging
                self.logger.info(

                     f"[IMAGE] Final processed size: {compressed_size_kb:.1f} KB "
                     f"(Original: {original_size_kb:.1f} KB). Returning image."
                 )
                end_time = time.time()
                processing_time = end_time - start_time
                self.logger.info(f"[IMAGE] ASSISTANT IMAGE CREATED: {file_name}")
                self.logger.info(f"[IMAGE_DEBUG] Total image processing time: {processing_time:.2f} seconds")

                return processed_image

            except Exception as e:
                self.logger.error(f"[IMAGE] Critical error processing image {_id}/{file_name}: {str(e)}")
                self.logger.error(f"[IMAGE_DEBUG] Exception type: {type(e).__name__}, traceback: {e.__traceback__}")
                # Re-raise the exception so the calling code knows something went wrong
                raise e


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
        
        # Configure network resilience settings
        retry_attempts = 3
        retry_delay = 2.0  # seconds
        
        # In plaats van de stream direct door te geven,
        # bufferen we het volledige antwoord en sturen het dan in één keer.
        buffered_content = []
        
        # Add retry logic for API calls to handle network instability
        stream = None
        for attempt in range(1, retry_attempts + 1):
            try:
                self.logger.info(f"[NETWORK] API call attempt {attempt}/{retry_attempts}")
                stream = await self.client.messages.create(
                    # Gebruik Claude 3.7 Sonnet model
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=2048,
                    # Add timeout parameter to prevent hanging on network issues
                    timeout=60.0,  # 60 second timeout for API call
                    system=f"""Je bent een vriendelijke en behulpzame data-analist voor EasyLog.
Je taak is om gebruikers te helpen bij het analyseren van bedrijfsgegevens en het maken van overzichtelijke verslagen.

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke samenvattingen van de EasyLog data!!
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
                )
                
                # Break out of retry loop on success
                self.logger.info("[NETWORK] API call successful")
                break
                
            except Exception as e:
                self.logger.error(f"[NETWORK] API call failed (attempt {attempt}/{retry_attempts}): {str(e)}")
                
                if attempt < retry_attempts:
                    # Wait before retrying with exponential backoff
                    import asyncio
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    self.logger.info(f"[NETWORK] Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    # Last attempt failed, re-raise the exception
                    self.logger.error("[NETWORK] All API call attempts failed")
                    raise

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")
        logger.info(f"[NETWORK] API call completed after {attempt} attempt(s)")

        if execution_time > 5.0:
            logger.warning(f"API call took longer than expected: {execution_time:.2f} seconds")

        # Detecteer en buffer alle berichten met afbeeldingen omdat die het meest gevoelig zijn
        # voor streaming problemen bij slechte internetverbindingen
        has_image_content = False
        image_buffer = []

        # Assert that the stream is not None, satisfying the type checker
        assert stream is not None, "Stream should have been initialized or an exception raised."

        # Initialize variables for buffering and timeout handling
        buffer_start_time = None
        max_buffer_time = 30  # Maximum seconds to buffer before sending anyway
        image_content_complete = False
        current_image_chunks = []
        
        async for content in self.handle_stream(stream, tools):
            # Controleer of we afbeeldingen hebben gedetecteerd
            if hasattr(content, "type") and content.type == "image":
                # Afbeelding gedetecteerd, schakel over naar buffermodus
                has_image_content = True
                if buffer_start_time is None:
                    buffer_start_time = time.time()
                self.logger.info("Afbeelding gedetecteerd, schakelen naar buffer modus")
                self.logger.debug(f"[IMAGE_DEBUG] Image content detected: {getattr(content, 'type', 'unknown')}, " +
                                 f"size: {len(str(content))}")
                # Start collecting chunks for this image
                current_image_chunks = [content]
                image_buffer.append(content)
            elif has_image_content:
                # We hebben al een afbeelding gezien, blijf alles bufferen
                image_buffer.append(content)
                
                # Check if we've been buffering too long and should send anyway
                if buffer_start_time and (time.time() - buffer_start_time) > max_buffer_time:
                    self.logger.warning(f"[IMAGE_DEBUG] Buffer timeout reached ({max_buffer_time}s), sending buffered content")
                    buffer_time = time.time() - buffer_start_time
                    self.logger.info(f"[IMAGE_DEBUG] Forced buffer flush after {buffer_time:.2f} seconds")
                    
                    # Send all buffered content
                    for chunk in image_buffer:
                        yield chunk
                    
                    # Reset buffer
                    image_buffer = []
                    has_image_content = False
                    buffer_start_time = None
                    continue
                
                self.logger.debug(f"[IMAGE_DEBUG] Buffering additional content chunk: {type(content)}")
            else:
                # Geen afbeeldingen gedetecteerd, stuur content direct door (smooth streaming)
                yield content

        # Als er afbeeldingen waren, stuur de gebufferde content nu
        if has_image_content and image_buffer:
            buffer_time = time.time() - buffer_start_time if buffer_start_time else 0
            self.logger.info(f"Verzenden van {len(image_buffer)} gebufferde berichten met afbeeldingen")
            self.logger.info(f"[IMAGE_DEBUG] Total buffering time: {buffer_time:.2f} seconds")
            self.logger.info(f"[IMAGE_DEBUG] Total buffer size: {sum(len(str(chunk)) for chunk in image_buffer)} characters")
            
            # Send each chunk with logging and error handling
            for i, buffered_chunk in enumerate(image_buffer):
                try:
                    self.logger.debug(f"[IMAGE_DEBUG] Yielding buffer chunk {i+1}/{len(image_buffer)}, " +
                                     f"type: {type(buffered_chunk)}")
                    yield buffered_chunk
                except Exception as e:
                    self.logger.error(f"[IMAGE_DEBUG] Error yielding buffer chunk {i+1}: {str(e)}")
                    # Continue with next chunk instead of failing completely

        # Check if the stream was successfully created (it should always be at this point,
        # or an exception would have been raised)
        if stream is None:
            # This should be unreachable due to the raise in the loop's else block
            self.logger.error("[CRITICAL] Stream is None after retry loop, this should not happen!")
            # Raise an error or handle appropriately if this unexpected state occurs
            raise RuntimeError("Failed to establish stream after retries.")
