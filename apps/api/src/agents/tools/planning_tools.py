import json
from collections.abc import Callable
from datetime import date

from dateutil import parser

from src.services.easylog_backend.backend_service import BackendService
from src.services.easylog_backend.schemas import (
    CreateMultipleAllocations,
    CreatePlanningPhase,
    CreateResourceAllocation,
    UpdatePlanningPhase,
    UpdatePlanningProject,
)
from src.utils.truncate import truncate


class PlanningTools:
    """
    A collection of tools for interacting with planning projects, phases, and resource allocations.

    This class provides methods to retrieve, create, and update planning data through the backend service.
    """

    def __init__(self, backend: BackendService, max_tool_result_length: int = 3250) -> None:
        """
        Initialize the PlanningTools with a backend service.

        Args:
            backend: The backend service for data operations
            max_tool_result_length: Maximum length for tool results before truncation (default: 2000)
        """
        self.backend = backend
        self.max_tool_result_length = max_tool_result_length

    @property
    def all_tools(self) -> list[Callable]:
        return [
            self.tool_get_planning_projects,
            self.tool_get_planning_project,
            self.tool_update_planning_project,
            self.tool_get_planning_phases,
            self.tool_get_planning_phase,
            self.tool_update_planning_phase,
            self.tool_create_planning_phase,
            self.tool_get_resources,
            self.tool_get_projects_of_resource,
            self.tool_create_multiple_allocations,
            self.tool_get_resource_groups,
        ]

    async def tool_get_planning_projects(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> str:
        """
        Retrieve all planning projects available for allocation within a date range.

        Args:
            from_date: Optional start date in YYYY-MM-DD format
            to_date: Optional end date in YYYY-MM-DD format

        Returns:
            JSON string containing planning projects data, truncated if necessary
        """
        planning_projects = await self.backend.get_planning_projects(
            from_date=parser.parse(from_date) if from_date else None,
            to_date=parser.parse(to_date) if to_date else None,
        )

        return truncate(planning_projects.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_get_planning_project(self, project_id: int) -> str:
        """
        Retrieve detailed information about a specific planning project.

        This returns comprehensive project data including allocation types (phases),
        resource groups, and current allocations. Use this to understand what resources
        can be assigned to which phases of the project.

        Args:
            project_id: The ID of the planning project to retrieve

        Returns:
            JSON string containing detailed project data, truncated if necessary
        """
        project = await self.backend.get_planning_project(project_id)

        return truncate(project.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_update_planning_project(
        self,
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
        Update properties of an existing planning project.

        Args:
            project_id: The ID of the project to update
            name: Optional new name for the project
            color: Optional new color code for the project
            report_visible: Optional flag to control report visibility
            exclude_in_workdays: Optional flag to exclude project in workday calculations
            start: Optional new start date in YYYY-MM-DD format
            end: Optional new end date in YYYY-MM-DD format
            extra_data: Optional additional data as a dictionary or JSON string

        Returns:
            JSON string containing the updated project data, truncated if necessary
        """
        await self.backend.update_planning_project(
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

        return await self.tool_get_planning_project(project_id)

    async def tool_get_planning_phases(self, project_id: int) -> str:
        """
        Retrieve all planning phases for a specific project.

        This provides the same allocation types information as the get_planning_project tool,
        but focused only on the phases.

        Args:
            project_id: The ID of the project to get phases for

        Returns:
            JSON string containing planning phases data, truncated if necessary
        """
        phases = await self.backend.get_planning_phases(project_id)

        return truncate(phases.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_get_planning_phase(self, phase_id: int) -> str:
        """
        Retrieve detailed information about a specific planning phase.

        Args:
            phase_id: The ID of the planning phase to retrieve

        Returns:
            JSON string containing phase data, truncated if necessary
        """
        phase = await self.backend.get_planning_phase(phase_id)

        return truncate(phase.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_update_planning_phase(
        self,
        phase_id: int,
        start: str,
        end: str,
    ) -> str:
        """
        Update the date range of an existing planning phase.

        Args:
            phase_id: The ID of the phase to update
            start: New start date (accepts various date formats)
            end: New end date (accepts various date formats)

        Returns:
            JSON string containing the updated phase data, truncated if necessary
        """
        await self.backend.update_planning_phase(
            phase_id,
            UpdatePlanningPhase(start=parser.parse(start), end=parser.parse(end)),
        )

        return await self.tool_get_planning_phase(phase_id)

    async def tool_create_planning_phase(
        self,
        project_id: int,
        slug: str,
        start: str,
        end: str,
    ) -> str:
        """
        Create a new planning phase for a project.

        Args:
            project_id: The ID of the project to create a phase for
            slug: Identifier slug for the phase (e.g., "design", "development")
            start: Start date for the phase (accepts various date formats)
            end: End date for the phase (accepts various date formats)

        Returns:
            JSON string containing the created phase data, truncated if necessary
        """
        phase = await self.backend.create_planning_phase(
            project_id,
            CreatePlanningPhase(slug=slug, start=parser.parse(start), end=parser.parse(end)),
        )

        return truncate(phase.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_get_resources(self) -> str:
        """
        Retrieve all available resources in the system.

        This provides a comprehensive list of all resources that can be allocated to projects.

        Returns:
            JSON string containing resources data, truncated if necessary
        """
        resources = await self.backend.get_resources()

        return truncate(resources.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_get_projects_of_resource(self, resource_group_id: int, slug: str) -> str:
        """
        Retrieve all projects associated with a specific resource and allocation type.

        Args:
            resource_group_id: The ID of the resource group
            slug: The slug of the allocation type (e.g., "td", "modificaties")

        Returns:
            JSON string containing projects data, truncated if necessary
        """
        projects = await self.backend.get_projects_of_resource(resource_group_id, slug)

        return truncate(projects.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_get_resource_groups(self, resource_id: int, resource_group_slug: str) -> str:
        """
        Retrieve all resource groups for a specific resource and group slug.

        Resource groups represent categories of resources that can be allocated together.

        Args:
            resource_id: The ID of the resource
            resource_group_slug: The slug identifier for the resource group

        Returns:
            JSON string containing resource groups data, truncated if necessary
        """
        resource_groups = await self.backend.get_resource_groups(resource_id, resource_group_slug)

        return truncate(resource_groups.model_dump_json(exclude_none=True), self.max_tool_result_length)

    async def tool_create_multiple_allocations(
        self,
        project_id: int,
        group: str,
        resources: list,
    ) -> str:
        """
        Allocate multiple resources to a project in a single operation.

        This tool allows batch allocation of resources to a project within a specific group.
        Each resource allocation includes timing and type information.

        Args:
            project_id: The ID of the project to allocate resources to
            group: The name of the resource group to allocate to (e.g., "td")
            resources: List of resource allocation specifications, each containing:
                - resource_id: ID of the resource to allocate
                - start: Start date/time of the allocation
                - end: End date/time of the allocation
                - type: Allocation type (e.g., "modificatiesi")
                - comment: Optional comment for the allocation
                - fields: Optional additional fields

        Returns:
            JSON string containing the created allocations data, truncated if necessary

        Example resources format:
            [
                {
                    "resource_id": 440,
                    "start": "2025-02-20T00:00:00.000000Z",
                    "end": "2025-02-24T00:00:00.000000Z",
                    "type": "modificatiesi",
                    "comment": "Optional comment"
                },
                {
                    "resource_id": 441,
                    "start": "2025-02-20T00:00:00.000000Z",
                    "end": "2025-02-24T00:00:00.000000Z",
                    "type": "modificatiesi"
                }
            ]
        """

        resources = json.loads(resources) if isinstance(resources, str) else resources

        allocations = await self.backend.create_multiple_allocations(
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

        return truncate(allocations.model_dump_json(exclude_none=True), self.max_tool_result_length)
