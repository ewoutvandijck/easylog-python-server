# Python standard library imports
import base64
import io
import json
import re
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

import httpx
import requests

# Third-party imports
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from src.agents.anthropic_agent import AnthropicAgent
from src.agents.tools.planning_tools import PlanningTools
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool
from PIL import Image

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
    debug_mode: bool = Field(
        default=True, description="Enable debug mode with additional logging"
    )
    image_max_width: int = Field(
        default=1200, 
        description="Maximum width for processed images in pixels"
    )
    image_quality: int = Field(
        default=90,
        description="JPEG quality for processed images (1-100)"
    )


# Agent class that integrates with Anthropic's Claude API for EasyLog data analysis
class AnthropicEasylogAgent(AnthropicAgent[AnthropicEasylogAgentConfig]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._planning_tools = PlanningTools(self.easylog_backend)
        self.logger.info("EasylogAgent initialized with planning tools")
        
        # Extra debug logging
        self.logger.info(f"[DEBUG] EasylogAgent initialized with debug_mode: {self.config.debug_mode}")
        self.logger.info(f"[DEBUG] Image processing settings: max_width={self.config.image_max_width}, quality={self.config.image_quality}")

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
                if (
                    name and len(name) > 1
                ):  # Minimale lengte om valse positieven te vermijden
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
                if (
                    role and len(role) > 3
                ):  # Minimale lengte om valse positieven te vermijden
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
                if (
                    department and len(department) > 2
                ):  # Minimale lengte om valse positieven te vermijden
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
            existing_type = (
                existing_memory.split(":", 1)[0].strip().lower()
                if ":" in existing_memory
                else ""
            )
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

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Deze functie handelt elk bericht van de gebruiker af.
        """
        # Log the incoming message for debugging
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == "user" and isinstance(last_message.content, str):
                self.logger.info(
                    f"Processing user message: {last_message.content[:100]}..."
                )
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

                        results.append(
                            f"Datum: {datum}, Object: {object_value}, Status object: {statusobject}"
                        )
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
                self.logger.info(
                    f"Fetching history for object: {object_name}, limit: {limit}"
                )
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.datum')) as datum,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.controle[0].statusobject')) as statusobject,
                            created_at
                        FROM follow_up_entries
                        WHERE JSON_UNQUOTE(JSON_EXTRACT(data, '$.object')) = %s
                        ORDER BY created_at DESC
                        LIMIT %
                    """
                    self.logger.debug(
                        f"Executing query with params: {object_name}, {limit}"
                    )
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

        def tool_download_image_from_url(url: str) -> str:
            """
            Download een afbeelding van een URL en geef deze terug als base64-gecodeerde data-URL.
            De afbeelding kan dan direct in HTML/markdown weergegeven worden.
            """
            try:
                # DEBUG-logs: start
                self.logger.info(f"[DEBUG] Start downloaden afbeelding vanaf: {url}")
                self.logger.info(f"[DEBUG] Debug mode is: {self.config.debug_mode}")
                self.logger.info(f"[DEBUG] Image max width: {self.config.image_max_width}")
                self.logger.info(f"[DEBUG] Image quality: {self.config.image_quality}")

                response = httpx.get(url)
                content_length = len(response.content)
                self.logger.info(f"[DEBUG] Status code: {response.status_code}")
                self.logger.info(f"[DEBUG] Ontvangen bytes: {content_length}")

                # Check of de response OK is
                if response.status_code != 200:
                    self.logger.error(
                        f"[DEBUG] Fout bij downloaden afbeelding: {response.status_code}"
                    )
                    return "Fout: kon afbeelding niet downloaden"
                
                # Voor zeer grote afbeeldingen tonen we een waarschuwing
                is_very_large_image = False
                
                # Verklein de afbeelding voor betere performance en streaming
                try:
                    # Importeer PIL alleen als nodig
                    import io
                    from PIL import Image

                    # Laad de afbeelding
                    img = Image.open(io.BytesIO(response.content))

                    # Originele afmetingen en grootte
                    original_width, original_height = img.size
                    original_size = len(response.content)
                    self.logger.info(
                        f"[DEBUG] Originele afmetingen: {original_width}x{original_height}"
                    )
                    self.logger.info(
                        f"[DEBUG] Originele bestandsgrootte: {original_size/1024/1024:.2f} MB"
                    )
                    
                    # Voor zeer grote afbeeldingen, maak een speciale behandeling
                    if original_size > 8 * 1024 * 1024:  # > 8MB
                        is_very_large_image = True
                        self.logger.info(f"[DEBUG] Zeer grote afbeelding gedetecteerd: {original_size/1024/1024:.2f} MB")
                    
                    # Maximum gecomprimeerde grootte in bytes (kleinere waarde voor betere streaming)
                    MAX_COMPRESSED_SIZE = 400 * 1024  # 400KB maximum voor betere streaming
                    
                    # Bepaal de doelgrootte op basis van bestandsgrootte
                    if original_size > 8 * 1024 * 1024:  # >8MB
                        target_width = 600  # Veel kleiner voor zeer grote afbeeldingen
                        quality = 70  # Lagere kwaliteit voor betere compressie
                        self.logger.info(f"[DEBUG] Zeer grote afbeelding (>8MB): target {target_width}px, kwaliteit {quality}%")
                    elif original_size > 3 * 1024 * 1024:  # >3MB
                        target_width = 800
                        quality = 75
                        self.logger.info(f"[DEBUG] Grote afbeelding (>3MB): target {target_width}px, kwaliteit {quality}%")
                    else:
                        # Gebruik configuratie voor normale afbeeldingen
                        target_width = self.config.image_max_width
                        quality = self.config.image_quality
                        self.logger.info(f"[DEBUG] Normale afbeelding: target {target_width}px, kwaliteit {quality}%")
                    
                    # Bereken schaalfactor en nieuwe afmetingen
                    if original_width > target_width:
                        scale_factor = target_width / original_width
                        new_width = target_width
                        new_height = int(original_height * scale_factor)
                        
                        # Verklein afbeelding - gebruik thumbnail methode voor betere prestaties met grote afbeeldingen
                        img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                        self.logger.info(
                            f"[DEBUG] Verkleind naar: {img.width}x{img.height}"
                        )
                    else:
                        self.logger.info(
                            "[DEBUG] Afbeelding is kleiner dan max breedte, geen resize nodig"
                        )
                    
                    # Converteer naar RGB indien nodig (voor PNG met transparantie)
                    if img.mode in ("RGBA", "LA"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                        img = background
                    
                    # Sla op in buffer met optimize=True voor betere compressie
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    image_data = buffer.getvalue()
                    image_size = len(image_data)
                    self.logger.info(
                        f"[DEBUG] Gecomprimeerde grootte: {image_size/1024:.2f} KB"
                    )
                    
                    # Controleer of de afbeelding nog steeds te groot is voor efficiënte streaming
                    # Zo ja, pas dan iteratief aan tot we onder het maximum blijven
                    attempt = 1
                    while image_size > MAX_COMPRESSED_SIZE and attempt <= 3:
                        attempt += 1
                        
                        # Elke keer verkleinen we verder met 40% in breedte en hoogte
                        # en verlagen we de kwaliteit met 10% per iteratie
                        new_width = int(img.width * 0.6)
                        new_height = int(img.height * 0.6)
                        quality = max(40, quality - 15)  # Nog lagere kwaliteit, maar niet onder 40%
                        
                        self.logger.info(f"[DEBUG] Iteratie {attempt}: Nieuwe afmetingen {new_width}x{new_height}, kwaliteit {quality}%")
                        
                        # Maak een nieuwe thumbnail
                        img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Converteer naar RGB indien nodig
                        if img.mode in ("RGBA", "LA"):
                            background = Image.new("RGB", img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                            img = background
                        
                        # Opnieuw opslaan met nieuwe instellingen
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=quality, optimize=True)
                        buffer.seek(0)
                        image_data = buffer.getvalue()
                        image_size = len(image_data)
                        
                        self.logger.info(f"[DEBUG] Na iteratie {attempt}: {image_size/1024:.2f} KB")
                    
                    # Rapporteer eindresultaat
                    compression_ratio = (original_size - image_size) / original_size * 100
                    self.logger.info(f"[DEBUG] Uiteindelijke compressie: {image_size/1024:.2f} KB")
                    self.logger.info(f"[DEBUG] Compressie ratio: {compression_ratio:.2f}% verkleind")
                    
                except ImportError:
                    self.logger.warning(
                        "[DEBUG] PIL niet beschikbaar, kan afbeelding niet verkleinen"
                    )
                    image_data = response.content
                except Exception as e:
                    self.logger.error(
                        f"[DEBUG] Fout bij verkleinen afbeelding: {str(e)}"
                    )
                    image_data = response.content

                # Base64 encoderen
                image_data_b64 = base64.b64encode(image_data).decode("utf-8")
                data_url = f"data:image/jpeg;base64,{image_data_b64}"
                
                # DEBUG-logs: einde
                base64_size = len(image_data_b64)
                self.logger.info(f"[DEBUG] Lengte base64-string: {base64_size/1024:.2f} KB")
                self.logger.info(
                    "[DEBUG] Afbeelding is succesvol gedownload en gecodeerd."
                )
                
                # Voor zeer grote afbeeldingen, voeg waarschuwing toe
                if is_very_large_image:
                    return f"⚠️ Dit is een grote afbeelding (>8MB). Als deze niet direct zichtbaar is, kun je de chat sluiten en opnieuw openen om de afbeelding te zien.\n\n{data_url}"
                
                return data_url

            except Exception as e:
                self.logger.error(
                    f"[DEBUG] Onverwachte fout bij afbeeldingsverwerking: {str(e)}"
                )
                return f"Fout bij verwerken afbeelding: {str(e)}"

        def tool_debug_info():
            """
            Geeft debug informatie over de huidige staat van de agent.
            """
            memories = self.get_metadata("memories", [])
            return json.dumps(
                {
                    "agent_type": "AnthropicEasylogAgent",
                    "config": {
                        "max_report_entries": self.config.max_report_entries,
                        "debug_mode": self.config.debug_mode,
                        "image_max_width": self.config.image_max_width,
                        "image_quality": self.config.image_quality
                    },
                    "memory_count": len(memories),
                    "message_history_length": len(messages),
                },
                indent=2,
            )

        def tool_set_debug_mode(enable: bool = True):
            """
            Schakelt debug modus aan of uit.
            
            Args:
                enable: True om debug modus aan te zetten, False om uit te zetten
            """
            self.config.debug_mode = enable
            self.logger.info(f"[CONFIG] Debug mode is now {'enabled' if enable else 'disabled'}")
            return f"Debug modus is nu {'ingeschakeld' if enable else 'uitgeschakeld'}."

        tools = [
            tool_store_memory,
            tool_get_easylog_data,
            tool_generate_monthly_report,
            tool_get_object_history,
            tool_clear_memories,
            tool_debug_info,
            tool_set_debug_mode,
            tool_download_image_from_url,
            *self._planning_tools.all_tools,
        ]

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
- tool_debug_info: Toon debug informatie (alleen voor ontwikkelaars)
- tool_set_debug_mode: Schakelt debug modus aan of uit
- tool_download_image_from_url: Download een afbeelding van een URL en geef deze terug als base64-gecodeerde data-URL

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
            tools=[function_to_anthropic_tool(tool) for tool in tools],
            stream=True,
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        if execution_time > 5.0:
            logger.warning(
                f"API call took longer than expected: {execution_time:.2f} seconds"
            )

        async for content in self.handle_stream(
            stream,
            tools,
        ):
            if self.config.debug_mode:
                self.logger.debug(f"Streaming content: {str(content)[:100]}...")
            yield content
