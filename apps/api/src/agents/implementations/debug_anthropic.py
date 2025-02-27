import base64
import glob
import json
import os
import time
from collections.abc import AsyncGenerator
from datetime import date

from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from dateutil import parser
from pydantic import BaseModel, Field

from src.agents.anthropic_agent import AnthropicAgent
from src.logger import logger
from src.models.messages import Message, MessageContent
from src.services.easylog_backend.schemas import (
    CreateMultipleAllocations,
    CreatePlanningPhase,
    CreateResourceAllocation,
    UpdatePlanningPhase,
    UpdatePlanningProject,
)
from src.utils.function_to_anthropic_tool import function_to_anthropic_tool


class Subject(BaseModel):
    name: str
    instructions: str
    glob_pattern: str


class DebugAnthropicConfig(BaseModel):
    subjects: list[Subject] = Field(
        default=[
            Subject(
                name="GezonderLeven",
                instructions="Help met bewegen en het creeren van een gezonder leven!",
                glob_pattern="pdfs/gezonderleven/*.pdf",
            ),
            Subject(
                name="Dieet",
                instructions="Help met het eten van gezonde voeding en help met afvallen",
                glob_pattern="pdfs/dieet/*.pdf",
            ),
        ]
    )
    default_subject: str | None = Field(default="WerkenSnelweg")


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class DebugAnthropic(AnthropicAgent[DebugAnthropicConfig]):
    def _load_pdfs(self, glob_pattern: str = "pdfs/*.pdf") -> list[str]:
        pdfs: list[str] = []

        # Get absolute path by joining with current file's directory
        glob_with_path = os.path.join(os.path.dirname(__file__), glob_pattern)

        # Find all PDF files in directory and encode them
        for file in glob.glob(glob_with_path):
            with open(file, "rb") as f:
                pdfs.append(base64.standard_b64encode(f.read()).decode("utf-8"))

        return pdfs

    async def on_message(self, messages: list[Message]) -> AsyncGenerator[MessageContent, None]:
        """
        This is the main function that handles each message from the user.!
        It processes the message, looks up relevant information, and generates a response.

        Step by step, this function:
        1. Loads all PDFs from the specified folder
        2. Converts previous messages into a format Claude understands
        3. Prepares the PDF contents to be sent to Claude
        4. Sets up helpful tools that Claude can use
        5. Sends everything to Claude and gets back a response

        Example usage:
            agent = AnthropicFirst()
            config = AnthropicFirstConfig(pdfs_path="./pdfs")
            messages = [Message(content="How do I fix the brake system?")]

            async for response in agent.on_message(messages, config):
                print(response)  # Prints each part of the AI's response as it's generated

        Args:
            messages: List of previous messages in the conversation
            config: Settings for the agent, including where to find PDFs

        Returns:
            An async generator that yields parts of the AI's response as they're generated
        """

        # Convert messages to a format Claude understands
        # This is like translating from one language to another
        message_history = self._convert_messages_to_anthropic_format(messages)

        # The get and set metadata functions are used to store and retrieve information between messages
        current_subject = self.get_metadata("subject")
        if current_subject is None:
            current_subject = self.config.default_subject

        subject = next((s for s in self.config.subjects if s.name == current_subject), None)

        if subject is not None:
            current_subject_name = subject.name
            current_subject_instructions = subject.instructions
            current_subject_pdfs = self._load_pdfs(subject.glob_pattern)
        else:
            current_subject_name = current_subject
            current_subject_instructions = ""
            current_subject_pdfs = []

        # Create special blocks for each PDF that Claude can read
        # This is like creating a digital package for each PDF
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf,
                },
                "cache_control": {"type": "ephemeral"},  # Tells Claude this is temporary.
            }
            for pdf in current_subject_pdfs
        ]

        # Claude won't respond to tool results if there is a PDF in the message.
        # So we add the PDF to the last user message that doesn't contain a tool result.
        for message in reversed(message_history):
            if (
                message["role"] == "user"  # Only attach PDFs to user messages
                and isinstance(message["content"], list)  # Content must be a list to extend
                and not any(
                    isinstance(content, dict) and content.get("type") == "tool_result" for content in message["content"]
                )  # Skip messages that contain tool results
            ):
                # Add PDF content blocks to eligible messages
                # This ensures Claude can reference PDFs when responding to user queries
                message["content"].extend(pdf_content_blocks)
                break

        # Memories are a way to store important information about a user.
        memories = self.get_metadata("memories", default=[])
        logger.info(f"Memories: {memories}")

        # Define helper tools that Claude can use
        # These are like special commands Claude can run to get extra information

        def tool_switch_subject(subject: str | None = None):
            """
            Switch to a different subject.
            """
            if subject is None:
                self.set_metadata("subject", None)
                return "Je bent nu terug in het algemene onderwerp"

            if subject not in [s.name for s in self.config.subjects]:
                raise ValueError(
                    f"Subject {subject} not found, choose from {', '.join([s.name for s in self.config.subjects])}"
                )

            self.set_metadata("subject", subject)

            return f"Je bent nu overgestapt naar het onderwerp: {subject}"

        # This tool is used to store a memory in the database.
        async def tool_store_memory(memory: str):
            """
            Store a memory in the database.
            """
            # Verwijder eventuele '-' aan het begin van de memory
            memory = memory.lstrip("- ")

            current_memory = self.get_metadata("memories", default=[])
            current_memory.append(memory)

            logger.info(f"Storing memory: {memory}")

            self.set_metadata("memories", current_memory)

            return "Memory stored"

        # Aangepaste tool om memories en thread te wissen
        def tool_clear_memories():
            """
            Wis alle opgeslagen herinneringen en de gespreksgeschiedenis.
            """
            self.set_metadata("memories", [])
            message_history.clear()  # Wist de gespreksgeschiedenis
            return "Alle herinneringen en de gespreksgeschiedenis zijn gewist."

        async def tool_get_datasources():
            """
            Get all datasources.
            """

            datasources = await self.easylog_backend.get_datasources()

            result = []
            for ds in datasources.data:
                datasource_text = f"- Datasource {ds.id}\n"
                datasource_text += f"  - naam: {ds.name}\n"
                datasource_text += f"  - beschrijving: {ds.description}\n"
                datasource_text += f"  - slug: {ds.slug}\n"
                datasource_text += f"  - types: {', '.join(ds.types) if ds.types else 'Geen'}\n"
                datasource_text += f"  - category_id: {ds.category_id if ds.category_id else 'Geen'}\n"

                # Handle resource_groups
                if ds.resource_groups:
                    if isinstance(ds.resource_groups, list):
                        resource_groups = [
                            rg.get("name", rg) if isinstance(rg, dict) else rg for rg in ds.resource_groups
                        ]
                        datasource_text += f"  - resource_groups: \n    - {'\n    - '.join(resource_groups)}\n"
                    else:
                        datasource_text += f"  - resource_groups: {ds.resource_groups}\n"
                else:
                    datasource_text += "  - resource_groups: Geen\n"

                # Handle extra_data_fields
                if ds.extra_data_fields:
                    datasource_text += "  - extra_data_fields: \n"
                    if isinstance(ds.extra_data_fields, list):
                        for field in ds.extra_data_fields:
                            if isinstance(field, dict):
                                field_name = field.get("name", "")
                                field_type = field.get("type", "")
                                field_options = field.get("options", [])

                                if field_options:
                                    options_str = ", ".join(field_options)
                                    datasource_text += f"    - {field_name} ({field_type}): {options_str}\n"
                                else:
                                    datasource_text += f"    - {field_name} ({field_type})\n"
                            else:
                                datasource_text += f"    - {field}\n"
                    else:
                        datasource_text += f"    {ds.extra_data_fields}\n"
                else:
                    datasource_text += "  - extra_data_fields: Geen\n"

                # Handle allocation_types
                if ds.allocation_types:
                    datasource_text += "  - allocation_types: \n"
                    if isinstance(ds.allocation_types, list):
                        for alloc_type in ds.allocation_types:
                            if isinstance(alloc_type, dict):
                                datasource_text += f"    - {alloc_type.get('name', alloc_type)}\n"
                            else:
                                datasource_text += f"    - {alloc_type}\n"
                    else:
                        datasource_text += f"    {ds.allocation_types}\n"
                else:
                    datasource_text += "  - allocation_types: Geen\n"

                datasource_text += f"  - aangemaakt op: {ds.created_at.isoformat()}\n"
                datasource_text += f"  - bijgewerkt op: {ds.updated_at.isoformat()}\n"

                result.append(datasource_text)

            return "\n".join(result) if result else "Geen datasources gevonden."

        async def tool_get_planning_projects(
            from_date: str | None = None,
            to_date: str | None = None,
        ):
            """
            Get all planning projects.

            Dates should be in the format YYYY-MM-DD.
            """
            planning_projects = await self.easylog_backend.get_planning_projects(
                from_date=parser.parse(from_date) if from_date else None,
                to_date=parser.parse(to_date) if to_date else None,
            )

            result = []
            for p in planning_projects.data:
                project_text = f"- Project {p.id}\n"
                project_text += f"  - naam: {p.name}\n"
                project_text += f"  - kleur: {p.color}\n"
                project_text += f"  - zichtbaar in rapport: {p.report_visible}\n"
                project_text += f"  - uitsluiten in werkdagen: {p.exclude_in_workdays}\n"
                project_text += f"  - start: {p.start.isoformat() if p.start else 'Niet ingesteld'}\n"
                project_text += f"  - eind: {p.end.isoformat() if p.end else 'Niet ingesteld'}\n"

                if p.extra_data:
                    project_text += f"  - extra data: {p.extra_data}\n"

                result.append(project_text)

            return "\n".join(result) if result else "Geen projecten gevonden."

        async def tool_get_planning_project(project_id: int) -> str:
            """
            Get a planning project by id.
            """
            project = await self.easylog_backend.get_planning_project(project_id)

            p = project.data
            result = f"Project {p.id}\n"
            result += f"- naam: {p.name}\n"
            result += f"- kleur: {p.color}\n"
            result += f"- zichtbaar in rapport: {p.report_visible}\n"
            result += f"- uitsluiten in werkdagen: {p.exclude_in_workdays}\n"
            result += f"- start: {p.start.isoformat() if p.start else 'Niet ingesteld'}\n"
            result += f"- eind: {p.end.isoformat() if p.end else 'Niet ingesteld'}\n"

            if p.extra_data:
                result += f"- extra data: {p.extra_data}\n"

            return result

        async def tool_update_planning_project(
            project_id: int,
            name: str | None = None,
            color: str | None = None,
            report_visible: bool | None = None,
            exclude_in_workdays: bool | None = None,
            start: str | None = None,
            end: str | None = None,
            extra_data: dict | None = None,
        ) -> str:
            """
            Update a planning project, you can update the name, color, report_visible, exclude_in_workdays, start and end date.

            Dates should be in the format YYYY-MM-DD.
            Extra data should be a JSON object.
            """
            await self.easylog_backend.update_planning_project(
                project_id,
                UpdatePlanningProject(
                    name=name,
                    color=color,
                    report_visible=report_visible,
                    exclude_in_workdays=exclude_in_workdays,
                    start=date.fromisoformat(start) if start else None,
                    end=date.fromisoformat(end) if end else None,
                    extra_data=json.loads(extra_data) if isinstance(extra_data, str) else extra_data,
                ),
            )

            return await tool_get_planning_project(project_id)

        async def tool_get_planning_phases(project_id: int) -> str:
            """
            Get all planning phases for a project.
            """
            phases = await self.easylog_backend.get_planning_phases(project_id)

            result = []
            for p in phases.data:
                phase_text = f"- Fase {p.id}\n"
                phase_text += f"  - project_id: {p.project_id}\n"
                phase_text += f"  - slug: {p.slug}\n"
                phase_text += f"  - start: {p.start.isoformat() if p.start else 'Niet ingesteld'}\n"
                phase_text += f"  - eind: {p.end.isoformat() if p.end else 'Niet ingesteld'}\n"

                result.append(phase_text)

            return "\n".join(result) if result else "Geen fases gevonden."

        async def tool_get_planning_phase(phase_id: int) -> str:
            """
            Get a planning phase by id.
            """
            phase = await self.easylog_backend.get_planning_phase(phase_id)

            p = phase.data
            result = f"Fase {p.id}\n"
            result += f"- project_id: {p.project_id}\n"
            result += f"- slug: {p.slug}\n"
            result += f"- start: {p.start.isoformat() if p.start else 'Niet ingesteld'}\n"
            result += f"- eind: {p.end.isoformat() if p.end else 'Niet ingesteld'}\n"

            return result

        async def tool_update_planning_phase(
            phase_id: int,
            start: str,
            end: str,
        ) -> str:
            """
            Update a planning phase.
            """
            await self.easylog_backend.update_planning_phase(
                phase_id,
                UpdatePlanningPhase(start=parser.parse(start), end=parser.parse(end)),
            )

            return await tool_get_planning_phase(phase_id)

        async def tool_create_planning_phase(
            project_id: int,
            slug: str,
            start: str,
            end: str,
        ) -> str:
            """
            Create a planning phase.
            """
            phase = await self.easylog_backend.create_planning_phase(
                project_id,
                CreatePlanningPhase(slug=slug, start=parser.parse(start), end=parser.parse(end)),
            )

            p = phase.data
            result = f"Nieuwe fase {p.id} aangemaakt:\n"
            result += f"- project_id: {p.project_id}\n"
            result += f"- slug: {p.slug}\n"
            result += f"- start: {p.start.isoformat() if p.start else 'Niet ingesteld'}\n"
            result += f"- eind: {p.end.isoformat() if p.end else 'Niet ingesteld'}\n"

            return result

        async def tool_get_resources() -> str:
            """
            Get all resources.
            """
            resources = await self.easylog_backend.get_resources()

            result = []
            for r in resources.data:
                resource_text = f"- Resource {r.id}\n"
                resource_text += f"  - naam: {r.name}\n"
                resource_text += f"  - label: {r.label}\n"
                resource_text += f"  - aangemaakt op: {r.created_at.isoformat() if r.created_at else 'Onbekend'}\n"
                resource_text += f"  - bijgewerkt op: {r.updated_at.isoformat() if r.updated_at else 'Onbekend'}\n"

                result.append(resource_text)

            return "\n".join(result) if result else "Geen resources gevonden."

        async def tool_get_projects_of_resource(resource_id: int, slug: str) -> str:
            """
            Get all projects of a resource. The slug should be a datasource slug.
            """
            projects = await self.easylog_backend.get_projects_of_resource(resource_id, slug)

            # Convert the Pydantic model to a dictionary
            projects_dict = projects.model_dump()

            result = []
            result.append(f"Projecten voor resource {resource_id} (slug: {slug}):")

            if "data" in projects_dict and projects_dict["data"]:
                for p in projects_dict["data"]:
                    project_text = f"- Project {p.get('id')}\n"
                    for key, value in p.items():
                        if key != "id":
                            project_text += f"  - {key}: {value}\n"
                    result.append(project_text)

            return "\n".join(result) if len(result) > 1 else "Geen projecten gevonden voor deze resource."

        async def tool_get_resource_groups(resource_id: int, slug: str) -> str:
            """
            Get all resource groups for a resource.
            """
            resource_groups = await self.easylog_backend.get_resource_groups(resource_id, slug)

            result = []
            result.append(f"Resource groepen voor resource {resource_id} (slug: {slug}):")

            for rg in resource_groups.items:
                group_text = f"- Groep {rg.id}\n"
                group_text += f"  - naam: {rg.name}\n"
                group_text += f"  - label: {rg.label}\n"
                group_text += f"  - slug: {rg.slug}\n"
                group_text += f"  - aangemaakt op: {rg.created_at.isoformat() if rg.created_at else 'Onbekend'}\n"
                group_text += f"  - bijgewerkt op: {rg.updated_at.isoformat() if rg.updated_at else 'Onbekend'}\n"

                result.append(group_text)

            return "\n".join(result) if len(result) > 1 else "Geen resource groepen gevonden."

        async def tool_create_multiple_allocations(
            project_id: int,
            group: str,
            resources: dict,
        ) -> str:
            """
            Create multiple allocations.

            Example:

            {
              "project_id": 510,
              "group": "dokter",
              "resources": [
                {
                  "resource_id": 508,
                  "type": "hpcvoor",
                  "comment": "string",
                  "start": "10-2-2023",
                  "end": "10-2-2024",
                  "fields": {
                    "roadcaptain": 1
                  }
                }
              ]
            }
            """

            resources = json.loads(resources) if isinstance(resources, str) else resources

            allocations = await self.easylog_backend.create_multiple_allocations(
                CreateMultipleAllocations(
                    project_id=project_id,
                    group=group,
                    resources=[
                        CreateResourceAllocation(
                            resource_id=r.get("resource_id"),
                            type=r.get("type"),
                            comment=r.get("comment"),
                            start=date.fromisoformat(r.get("start")),
                            end=date.fromisoformat(r.get("end")),
                            fields=r.get("fields"),
                        )
                        for r in resources
                    ],
                ),
            )

            result = []
            result.append(f"Allocaties aangemaakt voor project {project_id}, groep {group}:")

            for a in allocations.data:
                allocation_text = f"- Allocatie {a.id}\n"
                for key, value in a.model_dump().items():
                    if key != "id":
                        allocation_text += f"  - {key}: {value}\n"
                result.append(allocation_text)

            return "\n".join(result) if len(result) > 1 else "Geen allocaties aangemaakt."

        tools = [
            tool_switch_subject,
            tool_store_memory,
            tool_clear_memories,
            tool_get_datasources,
            tool_update_planning_project,
            tool_get_planning_projects,
            tool_get_planning_project,
            tool_get_planning_phases,
            tool_get_planning_phase,
            tool_update_planning_phase,
            tool_create_planning_phase,
            tool_get_resources,
            tool_get_projects_of_resource,
            tool_get_resource_groups,
            tool_create_multiple_allocations,
        ]

        # Start measuring how long the operation takes
        # This is like starting a stopwatch
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
            system=f"""Je bent een behulpzame planning assistent die gebruikers helpt bij het beheren van projecten, fases en resources in EasyLog.

### Wat je kunt doen
- Projecten bekijken, aanmaken en bijwerken
- Projectfases plannen en aanpassen
- Resources toewijzen aan projecten
- Planning visualiseren en optimaliseren
- Conflicten in planning identificeren en oplossen

### Hoe je helpt
- Leg planningsconcepten duidelijk uit
- Geef praktische suggesties voor efficiënte resourceallocatie
- Help bij het maken van realistische tijdlijnen
- Assisteer bij het organiseren van projectfases
- Bied inzicht in beschikbare resources en hun capaciteiten

### Core memories
Core memories zijn belangrijke informatie die je moet onthouden over een gebruiker. Die verzamel je zelf met de tool "store_memory". Als de gebruiker bijvoorbeeld zijn naam vertelt, of een belangrijke gebeurtenis heeft meegemaakt, of een belangrijke informatie heeft geleverd, dan moet je die opslaan in de core memories.

Je huidige core memories zijn:
{"\n- " + "\n- ".join(memories) if memories else " Geen memories opgeslagen"}

### Subject
Je bent nu in het onderwerp: {current_subject_name}

### Instructions
{current_subject_instructions}
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
