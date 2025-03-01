import base64
import json
import time
from collections.abc import AsyncGenerator
from datetime import date

import parser
from anthropic.types.beta.beta_base64_pdf_block_param import BetaBase64PDFBlockParam
from pydantic import BaseModel

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
from src.utils.truncate import truncate


class DebugAnthropicConfig(BaseModel):
    tool_result_max_length: int = Field(default=2000)


class ActivePDF(BaseModel):
    file_data: bytes
    summary: str
    long_summary: str
    markdown_content: str


# Agent class that integrates with Anthropic's Claude API and handles PDF documents
class DebugAnthropic(AnthropicAgent[DebugAnthropicConfig]):
    _active_pdf: ActivePDF | None = None

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

        # Create special blocks for each PDF that Claude can read
        # This is like creating a digital package for each PDF
        pdf_content_blocks: list[BetaBase64PDFBlockParam] = (
            [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(self._active_pdf.file_data).decode("utf-8"),
                    },
                    "cache_control": {"type": "ephemeral"},  # Tells Claude this is temporary.
                }
            ]
            if self._active_pdf
            else []
        )

        pdf_content_blocks = []

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

        async def tool_search_pdf(query: str):
            """
            Search for a PDF in the knowledge base.
            """
            knowledge_result = await self.search_knowledge(query)

            if (
                knowledge_result is None
                or knowledge_result.object is None
                or knowledge_result.object.name is None
                or knowledge_result.object.bucket_id is None
            ):
                return "Geen PDF gevonden"

            return json.dumps(
                {
                    "id": knowledge_result.id,
                    "markdown_content": knowledge_result.markdown_content,
                }
            )

        async def tool_load_image(id: str, file_name: str):
            """
            Load an image from the database. Id is the id of the pdf file, and in the markdown you'll find many references to images. Use the exact file path to load the image.
            """

            image_data = await self.load_image(id, file_name)

            return f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"

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

            return truncate(datasources.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_planning_projects(
            from_date: str | None = None,
            to_date: str | None = None,
        ):
            """
            This will return all the projects that you can allocate to.

            Dates should be in the format YYYY-MM-DD.
            """
            planning_projects = await self.easylog_backend.get_planning_projects(
                from_date=parser.parse(from_date) if from_date else None,
                to_date=parser.parse(to_date) if to_date else None,
            )

            return truncate(planning_projects.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_planning_project(project_id: int) -> str:
            """
            This is the most important tool, it will return all the information about a project.

            This will return allocation types (which are phases usually), and the resource groups that you can allocate to.

            You can get the allocation group to figure out what resources you can assign to this project, and phase.
            """
            project = await self.easylog_backend.get_planning_project(project_id)

            return truncate(project.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

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
            Get all planning phases for a project. This is the same as getting the allocation types from the tool "get_planning_project".
            """
            phases = await self.easylog_backend.get_planning_phases(project_id)

            return truncate(phases.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_planning_phase(phase_id: int) -> str:
            """
            Get a planning phase by id. This is the same as getting a single allocation type from the tool "get_planning_project".
            """
            phase = await self.easylog_backend.get_planning_phase(phase_id)

            return truncate(phase.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

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

            return truncate(phase.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_resources() -> str:
            """
            This will return all the resources. This is rarely used.
            """
            resources = await self.easylog_backend.get_resources()

            return truncate(resources.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_projects_of_resource(resource_group_id: int, slug: str) -> str:
            """
            This will return all the projects of a resource. The slug should be a slug like "td" or "modificaties", so basically the slug of the allocation type.
            """
            projects = await self.easylog_backend.get_projects_of_resource(resource_group_id, slug)

            return truncate(projects.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_get_resource_groups(resource_id: int, resource_group_slug: str) -> str:
            """
            This will return all the resource groups for a resource.
            """
            resource_groups = await self.easylog_backend.get_resource_groups(resource_id, resource_group_slug)

            return truncate(resource_groups.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        async def tool_create_multiple_allocations(
            project_id: int,
            group: str,
            resources: list,
        ) -> str:
            """
            You can use this tool to allocate resources to a project. For each project you can allocate resources to a group.
            The group is the name of the group you want to allocate to. You can get the groups with the tool "get_resource_groups".
            The resources are the resources you want to allocate. You can get the resources with the tool "get_resources".

            Example:

            {
                "project_id": 2315,
                "group": "td",
                "resources": [
                    {
                        "resource_id": 440, // This is a
                        "start": "2025-02-20T00:00:00.000000Z",
                        "end": "2025-02-24T00:00:00.000000Z",
                        "type": "modificatiesi" // Allocation type
                    },
                    {
                        "resource_id": 441,
                        "start": "2025-02-20T00:00:00.000000Z",
                        "end": "2025-02-24T00:00:00.000000Z",
                        "type": "modificatiesi"
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
                            start=parser.parse(r.get("start")),
                            end=parser.parse(r.get("end")),
                            fields=r.get("fields"),
                        )
                        for r in resources
                    ],
                ),
            )

            return truncate(allocations.model_dump_json(exclude_none=True), self.config.tool_result_max_length)

        tools = [
            tool_search_pdf,
            tool_store_memory,
            tool_clear_memories,
            tool_load_image,
            tool_get_datasources,
            tool_get_planning_projects,
            tool_get_planning_project,
            tool_update_planning_project,
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

Gebruik de tool "search_pdf" om een PDF te zoeken in de kennisbasis.

G
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
