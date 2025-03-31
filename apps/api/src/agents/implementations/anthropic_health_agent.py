# Python standard library imports
import io
import json
import re
import time
import base64
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

# Load all variables from .env
load_dotenv()


class HealthData(TypedDict):
    """
    Defines the structure for Health data
    """

    datum: str
    patient: str
    status: str
    behandeling: str


# Configuration class for AnthropicHealth agent
class AnthropicHealthAgentConfig(BaseModel):
    max_report_entries: int = Field(
        default=100,
        description="Maximum number of entries to fetch from the database for reports",
    )
    debug_mode: bool = Field(default=True, description="Enable debug mode with additional logging")
    image_max_width: int = Field(default=1200, description="Maximum width for processed images in pixels")
    image_quality: int = Field(default=90, description="JPEG quality for processed images (1-100)")


# Agent class that integrates with Anthropic's Claude API for Health data analysis
class AnthropicHealthAgent(AnthropicAgent[AnthropicHealthAgentConfig]):
    def __init__(self, *args, **kwargs) -> None:
        # Call the parent class init
        super().__init__(*args, **kwargs)

        # Extra logging for tracking tools
        self.available_tools = []
        self.logger.info("HealthAgent initialized with planning tools")

        # Disable debug mode to avoid loading debug tools
        self.config.debug_mode = False

    def _describe_available_tools(self):
        """Log available tools in the class and filter out debug tools"""
        all_tools = [
            "tool_store_memory",
            "tool_get_health_data",
            "tool_generate_monthly_report",
            "tool_get_patient_history",
            "tool_search_pdf",
            "tool_load_image",
            "tool_clear_memories",
        ]

        self.available_tools = all_tools
        self.logger.info(f"Available tools for HealthAgent: {', '.join(all_tools)}")

    def _extract_user_info(self, message_text: str) -> list[str]:
        """
        Automatically detects important information in the user's message!!

        Args:
            message_text: The text content of the user's message

        Returns:
            A list of detected information
        """
        detected_info = []

        # Detect names
        name_patterns = [
            r"(?i)(?:ik ben|mijn naam is|ik heet|noem mij)\s+([A-Za-z\s]+)",
            r"(?i)naam(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                name = match.strip()
                if name and len(name) > 1:  # Minimum length to avoid false positives
                    detected_info.append(f"Naam: {name}")
                    self.logger.info(f"Detected user name: {name}")

        # Detect healthcare roles
        role_patterns = [
            r"(?i)(?:ik ben|ik werk als)(?:\s+de|een|)?\s+([A-Za-z\s]+arts|[A-Za-z\s]+verpleegkundige|[A-Za-z\s]+fysiotherapeut|[A-Za-z\s]+specialist|[A-Za-z\s]+chirurg)",
            r"(?i)functie(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                role = match.strip()
                if role and len(role) > 3:  # Minimum length to avoid false positives
                    detected_info.append(f"Functie: {role}")
                    self.logger.info(f"Detected user role: {role}")

        # Detect departments
        department_patterns = [
            r"(?i)(?:ik werk bij|ik zit bij)(?:\s+de)?\s+afdeling\s+([A-Za-z\s]+)",
            r"(?i)afdeling(?:\s+is)?\s+([A-Za-z\s]+)",
        ]

        for pattern in department_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                department = match.strip()
                if department and len(department) > 2:  # Minimum length to avoid false positives
                    detected_info.append(f"Afdeling: {department}")
                    self.logger.info(f"Detected user department: {department}")

        # Detect health conditions/interests
        health_patterns = [
            r"(?i)(?:ik heb|lijden aan|last van)\s+([A-Za-z\s]+)",
            r"(?i)(?:interesse in|gespecialiseerd in)\s+([A-Za-z\s]+)",
        ]

        for pattern in health_patterns:
            matches = re.findall(pattern, message_text)
            for match in matches:
                condition = match.strip()
                if condition and len(condition) > 3:  # Minimum length to avoid false positives
                    detected_info.append(f"Gezondheid: {condition}")
                    self.logger.info(f"Detected health condition/interest: {condition}")

        # Detect reporting preferences
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
        Detects and stores important information from the user's message

        Args:
            message_text: The text content of the user's message
        """
        detected_info = self._extract_user_info(message_text)

        if not detected_info:
            return

        # Directly call store_memory_internal for each detected information
        for info in detected_info:
            await self._store_memory_internal(info)

    async def _store_memory_internal(self, memory: str):
        """
        Internal function to store memories with duplicate checking

        Args:
            memory: The memory to be stored
        """
        memory = memory.strip()
        if not memory:
            return

        # Get current memories
        current_memories = self.get_metadata("memories", default=[])

        # Extract type (everything before the first ":")
        memory_type = memory.split(":", 1)[0].strip().lower() if ":" in memory else ""

        # Look for existing memory of the same type
        existing_index = -1
        for i, existing_memory in enumerate(current_memories):
            existing_type = existing_memory.split(":", 1)[0].strip().lower() if ":" in existing_memory else ""
            if memory_type and existing_type == memory_type:
                existing_index = i
                break

        # Update existing or add new
        if existing_index >= 0:
            # Replace existing memory
            current_memories[existing_index] = memory
            self.logger.info(f"Updated existing memory: {memory}")
        else:
            # Add new memory
            current_memories.append(memory)
            self.logger.info(f"Added new memory: {memory}")

        # Save updated memories
        self.set_metadata("memories", current_memories)

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        This function handles each message from the user.
        We now buffer the entire Claude response signal so that base64 images
        come across all at once (and thus not partially) on a slow connection.
        """
        # Remove any debug tools that might be left in the code
        self.logger.info("Removing any debug tools that might still be in code")
        # Remove debug mode debug tools
        self.config.debug_mode = False

        # Describe available tools
        self._describe_available_tools()

        # Log the incoming message for debugging
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == "user" and isinstance(last_message.content, str):
                self.logger.info(f"Processing user message: {last_message.content[:100]}...")
                # Automatically detect and store name
                await self._store_detected_name(last_message.content)

        # Convert messages to a format Claude understands
        message_history = self._convert_messages_to_anthropic_format(messages)

        if self.config.debug_mode:
            self.logger.debug(f"Converted message history: {message_history}")

        # Retrieve memories
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Current memories: {memories}")

        def tool_clear_memories():
            """
            Clear all stored memories and conversation history.
            """
            self.set_metadata("memories", [])
            message_history.clear()
            self.logger.info("Memories and conversation history cleared")
            return "All memories and conversation history have been cleared."

        async def tool_store_memory(memory: str) -> str:
            """
            Store a memory in the database.
            """
            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)
            self.logger.info(f"Storing memory: {memory}")
            self.set_metadata("memories", current_memory)
            return "Memory stored"

        async def tool_get_health_data():
            """
            Haalt de gezondheidsgegevens op en maakt ze leesbaar.
            """
            try:
                self.logger.info("Fetching health data")
                with self.health_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.patient')) as patient,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.status')) as status,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.behandeling')) as behandeling
                        FROM health_entries
                        ORDER BY created_at DESC
                        LIMIT 100
                    """
                    self.logger.debug(f"Executing query: {query}")
                    cursor.execute(query)
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return "Geen gezondheidsgegevens gevonden"

                    results = ["🔍 Laatste gezondheidsgegevens:"]
                    for entry in entries:
                        datum, patient, status, behandeling = entry
                        results.append(f"Datum: {datum}, Patiënt: {patient}, Status: {status}, Behandeling: {behandeling}")
                    return "\n".join(results)

            except Exception as e:
                logger.error(f"Fout bij ophalen gezondheidsgegevens: {str(e)}")
                return f"Er is een fout opgetreden: {str(e)}"

        async def tool_generate_monthly_report(month: int, year: int):
            """
            Genereert een maandrapport voor de opgegeven maand en jaar.
            """
            try:
                self.logger.info(f"Generating monthly health report for {month}/{year}")
                with self.health_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.patient')) as patient,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.status')) as status,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.behandeling')) as behandeling,
                            created_at
                        FROM health_entries
                        WHERE MONTH(created_at) = %s AND YEAR(created_at) = %s
                        ORDER BY created_at DESC
                    """
                    self.logger.debug(f"Executing query with params: {month}, {year}")
                    cursor.execute(query, (month, year))
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return f"Geen gezondheidsgegevens gevonden voor {month}-{year}"

                    # Telling van statusobjecten en behandelingen
                    status_counts = {}
                    behandeling_counts = {}
                    patients = set()

                    for entry in entries:
                        datum, patient, status, behandeling, created_at = entry

                        # Patiënt toevoegen aan set voor unieke telling
                        if patient:
                            patients.add(patient)

                        # Status en behandeling tellen
                        if status:
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        if behandeling:
                            behandeling_counts[behandeling] = behandeling_counts.get(behandeling, 0) + 1

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
                        f"📊 **Gezondheidsrapport {month_name} {year}**",
                        "",
                        "**Samenvatting:**",
                        f"- Totaal aantal patiëntbezoeken: {len(entries)}",
                        f"- Unieke patiënten: {len(patients)}",
                        "",
                        "**Status verdeling:**"
                    ]
                    
                    # Voeg statussen toe aan rapport
                    for status, count in status_counts.items():
                        percentage = round(count / len(entries) * 100)
                        report.append(f"  - {status}: {count} ({percentage}%)")
                    
                    report.append("")
                    report.append("**Meest voorkomende behandelingen:**")
                    
                    # Voeg top 5 behandelingen toe aan rapport
                    sorted_behandelingen = sorted(behandeling_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    for behandeling, count in sorted_behandelingen:
                        percentage = round(count / len(entries) * 100)
                        report.append(f"  - {behandeling}: {count} ({percentage}%)")

                    return "\n".join(report)

            except Exception as e:
                logger.error(f"Fout bij genereren gezondheidsrapport: {str(e)}")
                return f"Er is een fout opgetreden bij het genereren van het rapport: {str(e)}"

        async def tool_get_patient_history(patient_name: str, limit: int = 10):
            """
            Haalt de geschiedenis op van een specifieke patiënt.
            """
            try:
                self.logger.info(f"Fetching history for patient: {patient_name}, limit: {limit}")
                with self.health_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.status')) as status,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.behandeling')) as behandeling,
                            created_at
                        FROM health_entries
                        WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.patient')) = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    self.logger.debug(f"Executing query with params: {patient_name}, {limit}")
                    cursor.execute(query, (patient_name, limit))
                    entries = cursor.fetchall()
                    self.logger.debug(f"Query returned {len(entries)} entries")

                    if not entries:
                        return f"Geen geschiedenis gevonden voor patiënt: {patient_name}"

                    results = [f"📜 **Medische geschiedenis voor {patient_name}:**"]

                    for entry in entries:
                        datum, status, behandeling, created_at = entry
                        results.append(f"Datum: {datum}, Status: {status}, Behandeling: {behandeling}")

                    return "\n".join(results)

            except Exception as e:
                logger.error(f"Fout bij ophalen patiënt geschiedenis: {str(e)}")
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

            # Process images, if available
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

            # Create a complete JSON response with all available information
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
            Load an image from the database and prepare it for display.
            The function accepts both full paths (figures/file.png) and just filenames (file.png).

            Args:
                _id (str): The ID of the PDF file
                file_name (str): The filename of the image (with or without path)

            Returns:
                str: A data URL with the image as base64 encoded data
            """
            self.logger.info(f"[IMAGE] Loading image {file_name} from {_id}")

            try:
                # Simplified path logic: try different path formats until one works
                possible_paths = [
                    file_name,
                    f"figures/{file_name}" if "/" not in file_name else file_name,
                    file_name.replace("figures/", "") if file_name.startswith("figures/") else file_name,
                    file_name.split("/")[-1],  # Just the filename
                ]

                # Try each possible path variant
                image_data = None
                last_error = None

                for path in possible_paths:
                    try:
                        image_data = await self.load_image(_id, path)
                        self.logger.info(f"[IMAGE] Successfully loaded with path: {path}")
                        break
                    except Exception as e:
                        last_error = e
                        continue

                if image_data is None:
                    raise last_error or Exception("Could not load image with available paths")

                # Determine original size
                with io.BytesIO() as buffer:
                    image_data.save(buffer, format=image_data.format or "PNG")
                    buffer.seek(0)
                    original_size = len(buffer.getvalue())
                    original_size_kb = original_size / 1024

                # Simplified compression logic
                original_width, original_height = image_data.size

                # Basic configuration for optimal performance on mobile devices
                max_width = 600
                quality = 60

                # Simple adjustment based on image size
                if original_size < 100 * 1024:  # < 100 KB
                    max_width = min(original_width, 800)
                    quality = 75
                elif original_size > 1 * 1024 * 1024:  # > 1 MB
                    max_width = 450
                    quality = 45

                # Resize if needed
                if original_width > max_width:
                    scale_factor = max_width / original_width
                    new_height = int(original_height * scale_factor)
                    image_data = image_data.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Convert to RGB (for images with transparency)
                if image_data.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", image_data.size, (255, 255, 255))
                    background.paste(
                        image_data,
                        mask=image_data.split()[3] if len(image_data.split()) > 3 else None,
                    )
                    image_data = background

                # Compress the image
                with io.BytesIO() as buffer:
                    image_data.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    compressed_data = buffer.getvalue()
                    compressed_size = len(compressed_data)
                    compressed_size_kb = compressed_size / 1024

                # Extra compression only if really needed (> 150KB)
                if compressed_size > 150 * 1024:
                    # Further reduce and compress
                    new_width = int(image_data.width * 0.7)
                    new_height = int(image_data.height * 0.7)

                    image_data = image_data.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Try blurring for better compression
                    try:
                        from PIL import ImageFilter

                        image_data = image_data.filter(ImageFilter.GaussianBlur(radius=0.6))
                    except Exception:
                        pass

                    with io.BytesIO() as buffer:
                        image_data.save(buffer, format="JPEG", quality=40, optimize=True)

                self.logger.info(
                    f"[IMAGE] Image optimized: {original_size_kb:.1f}KB → {compressed_size_kb:.1f}KB"
                )
                return image_data

            except Exception as e:
                self.logger.error(f"[IMAGE] Error during processing: {str(e)}")
                raise e

        tools = [
            tool_store_memory,
            tool_get_health_data,
            tool_generate_monthly_report,
            tool_get_patient_history,
            tool_search_pdf,
            tool_load_image,
            tool_clear_memories,
        ]

        # Print all tools for debugging
        self.logger.info("All tools before filtering:")
        for tool in tools:
            self.logger.info(f" - {tool.__name__}")

        # Convert all tools to Anthropic format and filter debug tools
        anthropic_tools = []
        for tool in tools:
            if tool.__name__ in [
                "tool_store_memory",
                "tool_get_health_data",
                "tool_generate_monthly_report",
                "tool_get_patient_history",
                "tool_search_pdf",
                "tool_load_image",
                "tool_clear_memories",
            ]:
                anthropic_tools.append(function_to_anthropic_tool(tool))
                self.logger.info(f"Added tool to Anthropic tools: {tool.__name__}")
            else:
                self.logger.warning(f"Skipping tool: {tool.__name__}")

        # Print all tools after filtering for debugging
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

        # Instead of forwarding the stream directly,
        # we buffer the entire response and send it at once.
        buffered_content = []
        stream = await self.client.messages.create(
            # Use Claude 3.7 Sonnet model
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system=f"""Je bent een vriendelijke en motiverende COPD-coach die in het Nederlands communiceert.
Je taak is om patiënten met COPD te helpen een beter, gezonder leven te leiden met korte, duidelijke adviezen en instructies.

### BELANGRIJKE REGELS:
- Geef ALTIJD antwoord in het Nederlands
- Houd je antwoorden kort en bondig
- Gebruik eenvoudige, directe taal - geen medisch jargon
- Motiveer patiënten om meer naar buiten te gaan en te wandelen
- Wees positief en moedig kleine verbeteringen aan
- Geef praktische tips voor buitenactiviteiten, zelfs bij COPD-klachten
- Vul informatie aan met concrete instructies (bijv. "Loop 10 minuten in uw buurt")
- Vermijd lange uitleg - maak het concreet en direct toepasbaar

### Beschikbare tools:
- tool_store_memory: Slaat belangrijke informatie over de patiënt op
- tool_get_health_data: Haalt de laatste gezondheidsgegevens op uit de database
- tool_generate_monthly_report: Maakt een maandrapport met gezondheidsstatistieken
- tool_get_patient_history: Haalt de geschiedenis van een specifieke patiënt op
- tool_search_pdf: Zoekt in medische literatuur en COPD-richtlijnen
- tool_load_image: Laadt afbeeldingen van oefeningen of instructies
- tool_clear_memories: Wist alle opgeslagen herinneringen

### Gebruik van tool_search_pdf
Gebruik deze tool om informatie te zoeken in medische literatuur en COPD-richtlijnen, vooral voor specifieke vragen over buitenactiviteiten.

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, functie, afdeling of voorkeuren, dan moet je die opslaan in de core memories.

Voorbeelden van belangrijke herinneringen om op te slaan:
- Naam van de gebruiker (bijv. "Naam: Jan")
- Functie (bijv. "Functie: Cardioloog")
- Afdeling (bijv. "Afdeling: Kindergeneeskunde")
- Voorkeuren voor rapportages (bijv. "Voorkeur: wekelijkse rapportages")
- Specifieke interesses (bijv. "Interesse: hartfalen bij ouderen")

Je huidige core memories zijn:
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}

### Gezondheidsanalyse tips:
- Zoek naar trends over tijd
- Identificeer patiënten die mogelijk extra aandacht nodig hebben
- Wijs op ongewone of afwijkende resultaten
- Geef context bij de cijfers waar mogelijk
- Vat grote datasets bondig samen
- Benadruk de vertrouwelijkheid van de gegevens
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

        # Detect and buffer all messages with images as they are most sensitive
        # to streaming issues on poor internet connections
        has_image_content = False
        image_buffer = []

        async for content in self.handle_stream(stream, tools):
            # Check if we've detected images
            if hasattr(content, "type") and content.type == "image":
                # Image detected, switch to buffer mode
                has_image_content = True
                self.logger.info("Image detected, switching to buffer mode")
                # Add this image to the buffer
                image_buffer.append(content)
            elif has_image_content:
                # We've already seen an image, continue buffering everything
                image_buffer.append(content)
            else:
                # No images detected, pass content directly (smooth streaming)
                yield content

        # If there were images, send the buffered content now
        if has_image_content and image_buffer:
            self.logger.info(f"Sending {len(image_buffer)} buffered messages with images")
            for buffered_chunk in image_buffer:
                yield buffered_chunk 

