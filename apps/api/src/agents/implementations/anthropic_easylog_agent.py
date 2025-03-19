# Python standard library imports
import time
from collections.abc import AsyncGenerator
from typing import TypedDict

# Third-party imports
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool

# Laad alle variabelen uit .env
load_dotenv()


class EasylogData(TypedDict):
    """
    Structure for Easylog data focusing on bike status and location
    """

    framenummer: str
    statusfiets: str
    actuele_locatie_fiets: str
    merk: str
    type: str
    framehoogte: str
    kleur: str


class RennerHistorie(TypedDict):
    """
    Structure for data about bike assignments to riders
    """

    datum_toewijzing: str
    renner: str
    team_klant: str
    toegewezen_door: str
    offerte_nummer: str
    opmerkingen_toewijzing: str


# Configuration class for AnthropicEasylog agent
class AnthropicEasylogAgentConfig(BaseModel):
    max_entries: int = Field(
        default=100,
        description="Maximum number of entries to fetch from the database",
    )
    debug_mode: bool = Field(
        default=False, description="Enable debug mode with additional logging"
    )


# Agent class that integrates with Anthropic's Claude API for EasyLog data analysis
class AnthropicEasylogAgent(AnthropicAgent[AnthropicEasylogAgentConfig]):
    def __init__(self, *args, **kwargs) -> None:
        # Call the parent class init
        super().__init__(*args, **kwargs)

        # Extra logging
        self.available_tools = []
        self.logger.info("EasylogAgent initialized with basic SQL tool")

    # Helper methods to get readable labels
    def _get_status_label(self, status_value):
        """Convert status code to readable label with emoji"""
        status_map = {
            "BESCHIKBAAR": "✅ BESCHIKBAAR",
            "GERESERVEERD": "🕒 GERESERVEERD",
            "IN_GEBRUIK": "🚲 IN GEBRUIK",
            "ELDERS": "🌍 ELDERS",
            "IN_ONDERHOUD": "🔧 IN ONDERHOUD",
        }
        return status_map.get(status_value, status_value)

    def _get_locatie_label(self, locatie_value):
        """Convert location code to readable label with emoji"""
        locatie_map = {
            "HPC": "🏠 HPC",
            "TRUCK": "🚛 Truck",
            "RENNER": "🏃 Bij renner",
            "TRANSPORT": "🚚 Transport",
            "ANDERS": "📍 Andere locatie",
        }
        return locatie_map.get(locatie_value, locatie_value or "Onbekend")

    async def on_message(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Handles messages from the user and returns AI responses
        """
        # Log the incoming message for debugging
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.role == "user" and isinstance(last_message.content, str):
                self.logger.info(
                    f"Processing user message: {last_message.content[:100]}..."
                )

        # Convert messages to a format Claude understands
        message_history = self._convert_messages_to_anthropic_format(messages)

        # Define the SQL tool to fetch all bikes data
        async def tool_fetch_all_bikes(limit: int = 20):
            """
            Fetches status and location data for all bikes

            Args:
                limit: Maximum number of entries to retrieve
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.type')) as type,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framehoogte')) as framehoogte,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.kleur')) as kleur,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) IS NOT NULL
                            AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    entries = cursor.fetchall()

                    if not entries:
                        return "Geen fietsdata gevonden"

                    results = ["🚲 Overzicht Fietsen:"]
                    for entry in entries:
                        (
                            framenummer,
                            statusfiets,
                            locatie,
                            merk,
                            type_fiets,
                            framehoogte,
                            kleur,
                            created_at,
                        ) = entry
                        status_label = self._get_status_label(statusfiets)
                        locatie_label = self._get_locatie_label(locatie)

                        fiets_info = []
                        fiets_info.append(f"Framenummer: {framenummer}")
                        fiets_info.append(f"Status: {status_label}")
                        fiets_info.append(f"Locatie: {locatie_label}")

                        if merk:
                            fiets_info.append(f"Merk: {merk}")
                        if type_fiets:
                            fiets_info.append(f"Type: {type_fiets}")
                        if framehoogte:
                            fiets_info.append(f"Framehoogte: {framehoogte}")
                        if kleur:
                            fiets_info.append(f"Kleur: {kleur}")

                        fiets_info.append(f"Bijgewerkt: {created_at}")

                        results.append(" | ".join(fiets_info))

                    return "\n".join(results)

            except Exception as e:
                return f"Error bij ophalen fietsdata: {str(e)}"

        # Define SQL tool to fetch data for a specific bike by frame number
        async def tool_fetch_bike_by_frame(framenummer: str):
            """
            Fetches status and location data for a specific bike by frame number

            Args:
                framenummer: The frame number of the bike to look up
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.type')) as type,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framehoogte')) as framehoogte,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.kleur')) as kleur,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (framenummer,))
                    entry = cursor.fetchone()

                    if not entry:
                        return f"Geen fiets gevonden met framenummer: {framenummer}"

                    (
                        framenummer,
                        statusfiets,
                        locatie,
                        merk,
                        type_fiets,
                        framehoogte,
                        kleur,
                        created_at,
                    ) = entry
                    status_label = self._get_status_label(statusfiets)
                    locatie_label = self._get_locatie_label(locatie)

                    result = [f"🚲 Fietsgegevens voor framenummer: {framenummer}"]
                    result.append(f"Status: {status_label}")
                    result.append(f"Locatie: {locatie_label}")

                    if merk:
                        result.append(f"Merk: {merk}")
                    if type_fiets:
                        result.append(f"Type: {type_fiets}")
                    if framehoogte:
                        result.append(f"Framehoogte: {framehoogte}")
                    if kleur:
                        result.append(f"Kleur: {kleur}")

                    result.append(f"Laatst bijgewerkt: {created_at}")

                    # Fetch history for this bike
                    query_history = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                    """
                    cursor.execute(query_history, (framenummer,))
                    history = cursor.fetchall()

                    if len(history) > 1:
                        result.append("\nRecente historie:")
                        for i, hist_entry in enumerate(history):
                            if i == 0:  # Skip current status which we already displayed
                                continue
                            h_status, h_locatie, h_date = hist_entry
                            h_status_label = self._get_status_label(h_status)
                            h_locatie_label = self._get_locatie_label(h_locatie)
                            result.append(
                                f"{h_date}: Status: {h_status_label}, Locatie: {h_locatie_label}"
                            )

                    return "\n".join(result)

            except Exception as e:
                return f"Error bij ophalen fietsgegevens: {str(e)}"

        # Define SQL tool to fetch rider history for a specific bike
        async def tool_fetch_bike_rider_history(framenummer: str):
            """
            Fetches the rider assignment history for a specific bike by frame number

            Args:
                framenummer: The frame number of the bike to look up rider history for
            """
            try:
                # First check if the bike exists
                with self.easylog_db.cursor() as cursor:
                    bike_query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.type')) as type
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    cursor.execute(bike_query, (framenummer,))
                    bike = cursor.fetchone()

                    if not bike:
                        return f"Geen fiets gevonden met framenummer: {framenummer}"

                    # Fetch the rider history from the renner_historie field in the JSON data
                    history_query = """
                        SELECT 
                            JSON_EXTRACT(data, '$.renner_historie') as renner_historie,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) = %s
                            AND JSON_EXTRACT(data, '$.renner_historie') IS NOT NULL
                            AND JSON_EXTRACT(data, '$.renner_historie') != 'null'
                            AND JSON_EXTRACT(data, '$.renner_historie') != '[]'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    cursor.execute(history_query, (framenummer,))
                    history_result = cursor.fetchone()

                    framenummer, merk, type_fiets = bike
                    fiets_info = f"🚲 Fiets: {framenummer}"
                    if merk:
                        fiets_info += f" - {merk}"
                    if type_fiets:
                        fiets_info += f" {type_fiets}"

                    if not history_result or not history_result[0]:
                        return f"{fiets_info}\n\nGeen renner-toewijzingen gevonden voor deze fiets."

                    # Process the rider history
                    import json

                    renner_historie_json, latest_update = history_result

                    try:
                        renner_historie = json.loads(renner_historie_json)
                        if not renner_historie or len(renner_historie) == 0:
                            return f"{fiets_info}\n\nGeen renner-toewijzingen gevonden voor deze fiets."

                        # Build the result
                        result = [fiets_info]
                        result.append(
                            f"\n📋 Renner-toewijzingen (bijgewerkt: {latest_update}):"
                        )

                        # Sort by datum_toewijzing if available (newest first)
                        if (
                            renner_historie
                            and len(renner_historie) > 0
                            and "datum_toewijzing" in renner_historie[0]
                        ):
                            renner_historie = sorted(
                                renner_historie,
                                key=lambda x: x.get("datum_toewijzing", ""),
                                reverse=True,
                            )

                        for i, toewijzing in enumerate(renner_historie, 1):
                            entry = [f"\n{i}. "]

                            # Datum toewijzing
                            if (
                                "datum_toewijzing" in toewijzing
                                and toewijzing["datum_toewijzing"]
                            ):
                                entry.append(f"Datum: {toewijzing['datum_toewijzing']}")

                            # Renner naam
                            if "renner" in toewijzing and toewijzing["renner"]:
                                entry.append(f"Renner: {toewijzing['renner']}")

                            # Team/Klant
                            if "team_klant" in toewijzing and toewijzing["team_klant"]:
                                entry.append(f"Team/Klant: {toewijzing['team_klant']}")

                            # Toegewezen door
                            if (
                                "toegewezen_door" in toewijzing
                                and toewijzing["toegewezen_door"]
                            ):
                                entry.append(
                                    f"Toegewezen door: {toewijzing['toegewezen_door']}"
                                )

                            # Offerte nummer
                            if (
                                "offerte_nummer" in toewijzing
                                and toewijzing["offerte_nummer"]
                            ):
                                entry.append(f"Offerte: {toewijzing['offerte_nummer']}")

                            # Opmerkingen
                            if (
                                "opmerkingen_toewijzing" in toewijzing
                                and toewijzing["opmerkingen_toewijzing"]
                            ):
                                entry.append(
                                    f"Opmerkingen: {toewijzing['opmerkingen_toewijzing']}"
                                )

                            result.append(" | ".join(entry))

                        return "\n".join(result)

                    except json.JSONDecodeError as e:
                        return f"Error bij verwerken renner historie JSON: {str(e)}"

            except Exception as e:
                return f"Error bij ophalen renner historie: {str(e)}"

        # Define SQL tool to search bikes by rider name
        async def tool_search_bikes_by_rider(rider_name: str, limit: int = 10):
            """
            Search for bikes that have been assigned to a specific rider

            Args:
                rider_name: Name (or partial name) of the rider to search for
                limit: Maximum number of results to return
            """
            try:
                with self.easylog_db.cursor() as cursor:
                    # Use JSON_SEARCH to find bikes with this rider in the renner_historie
                    query = """
                        SELECT 
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.framenummer')) as framenummer,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.statusfiets')) as statusfiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.actuele_locatie_fiets')) as actuele_locatie_fiets,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.merk')) as merk,
                            JSON_UNQUOTE(JSON_EXTRACT(data, '$.type')) as type,
                            JSON_EXTRACT(data, '$.renner_historie') as renner_historie,
                            created_at
                        FROM follow_up_entries
                        WHERE 
                            JSON_SEARCH(JSON_EXTRACT(data, '$.renner_historie'), 'one', %s, NULL, '$.*.renner') IS NOT NULL
                        GROUP BY framenummer
                        ORDER BY created_at DESC
                        LIMIT %s
                    """

                    cursor.execute(query, (rider_name, limit))
                    entries = cursor.fetchall()

                    if not entries:
                        return f"Geen fietsen gevonden die toegewezen zijn aan renner met naam '{rider_name}'"

                    import json

                    results = [f"🔍 Fietsen toegewezen aan renner '{rider_name}':"]

                    for entry in entries:
                        (
                            framenummer,
                            statusfiets,
                            locatie,
                            merk,
                            type_fiets,
                            renner_historie_json,
                            created_at,
                        ) = entry
                        status_label = (
                            self._get_status_label(statusfiets)
                            if statusfiets
                            else "Onbekend"
                        )
                        locatie_label = (
                            self._get_locatie_label(locatie) if locatie else "Onbekend"
                        )

                        fiets_info = []
                        fiets_info.append(f"Framenummer: {framenummer}")

                        if merk:
                            fiets_info.append(f"Merk: {merk}")
                        if type_fiets:
                            fiets_info.append(f"Type: {type_fiets}")

                        fiets_info.append(f"Status: {status_label}")
                        fiets_info.append(f"Locatie: {locatie_label}")

                        # Get the most recent assignment to this rider
                        try:
                            if renner_historie_json:
                                renner_historie = json.loads(renner_historie_json)
                                for toewijzing in renner_historie:
                                    if (
                                        "renner" in toewijzing
                                        and toewijzing["renner"]
                                        and rider_name.lower()
                                        in toewijzing["renner"].lower()
                                    ):
                                        if (
                                            "datum_toewijzing" in toewijzing
                                            and toewijzing["datum_toewijzing"]
                                        ):
                                            fiets_info.append(
                                                f"Toegewezen op: {toewijzing['datum_toewijzing']}"
                                            )
                                        if (
                                            "team_klant" in toewijzing
                                            and toewijzing["team_klant"]
                                        ):
                                            fiets_info.append(
                                                f"Team: {toewijzing['team_klant']}"
                                            )
                                        break
                        except:
                            # Ignore JSON parsing errors in search results
                            pass

                        results.append(" | ".join(fiets_info))

                    return "\n".join(results)

            except Exception as e:
                return f"Error bij zoeken naar fietsen voor renner '{rider_name}': {str(e)}"

        # Define available tools
        tools = [
            tool_fetch_all_bikes,
            tool_fetch_bike_by_frame,
            tool_fetch_bike_rider_history,
            tool_search_bikes_by_rider,
        ]

        # Convert tools to Anthropic format
        anthropic_tools = [function_to_anthropic_tool(tool) for tool in tools]

        # Start time for logging
        start_time = time.time()

        # Create the stream with Claude
        stream = await self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system="""Je bent een vriendelijke en behulpzame fiets-beheerder voor EasyLog.
Je taak is om gebruikers te helpen bij het vinden en analyseren van fietsgegevens.

### BELANGRIJKE INFORMATIE:
Elke fiets heeft de volgende eigenschappen:
- Framenummer: Uniek identificatienummer van de fiets
- Status: Huidige status van de fiets (BESCHIKBAAR, GERESERVEERD, IN_GEBRUIK, ELDERS, IN_ONDERHOUD)
- Locatie: Waar de fiets zich nu bevindt (HPC, TRUCK, RENNER, TRANSPORT, ANDERS)
- Merk: Het merk van de fiets
- Type: Het type/model van de fiets
- Framehoogte: De hoogte van het fietsframe
- Kleur: De kleur van de fiets

Voor fietsen is ook een historie van renner-toewijzingen beschikbaar, met de volgende gegevens:
- Datum toewijzing: Wanneer de fiets werd toegewezen
- Renner: Naam van de renner
- Team/Klant: Team of klant waarvoor de renner rijdt
- Toegewezen door: Persoon die de toewijzing heeft gedaan
- Offerte nummer: Referentie voor financiële administratie
- Opmerkingen: Extra informatie over de toewijzing

### BELANGRIJKE REGELS:
- Geef nauwkeurige en feitelijke informatie over de fietsen
- Help de gebruiker om snel de juiste fiets te vinden
- Maak duidelijke en overzichtelijke weergaves van de data
- Wees behulpzaam en informatief

### Beschikbare tools:
- tool_fetch_all_bikes: Haalt status en locatie op voor alle fietsen
- tool_fetch_bike_by_frame: Haalt gegevens op voor een specifieke fiets op basis van framenummer
- tool_fetch_bike_rider_history: Haalt de renner-toewijzingen op voor een specifieke fiets
- tool_search_bikes_by_rider: Zoekt fietsen die aan een bepaalde renner zijn toegewezen
            """,
            messages=message_history,
            tools=anthropic_tools,
            stream=True,
        )

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Time taken for API call: {execution_time:.2f} seconds")

        # Stream the response
        async for content in self.handle_stream(stream, tools):
            yield content
