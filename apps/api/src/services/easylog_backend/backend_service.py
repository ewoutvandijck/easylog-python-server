from datetime import date

from httpx import AsyncClient

from src.logger import logger

from .schemas import (
    Allocation,
    CreateMultipleAllocations,
    CreatePlanningPhase,
    DataEntry,
    Datasource,
    DatasourceDataEntry,
    DatasourceDataType,
    PaginatedItemsResponse,
    PaginatedResponse,
    PlanningPhase,
    PlanningProject,
    Resource,
    ResourceGroup,
    UpdatePlanningPhase,
    UpdatePlanningProject,
)


class BackendService:
    def __init__(self, bearer_token: str, base_url: str = "https://staging.easylog.nu/api/v2") -> None:
        self.bearer_token = bearer_token
        self.client = AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.bearer_token}"},
        )

    async def get_datasources(self) -> PaginatedResponse[Datasource]:
        """
        Get all datasources

        Returns:
            PaginatedResponse[Datasource]: The datasources
        """
        response = await self.client.get("/datasources")
        logger.debug(response.text)
        response.raise_for_status()
        return PaginatedResponse[Datasource].model_validate_json(response.text)

    async def get_datasource_entry(
        self,
        datasource_slug: str,
        entry_id: str,
        data_type: type[DatasourceDataType] = dict,
    ) -> DatasourceDataEntry[DatasourceDataType]:
        """
        Get a datasource entry

        Args:
            datasource_slug: The slug of the datasource
            entry_id: The id of the entry
            data_type: The type of the data

        Returns:
            DatasourceDataEntry[DatasourceDataType]: The datasource entry
        """
        response = await self.client.get(
            f"/datasources/{datasource_slug}/entries/{entry_id}",
        )
        response.raise_for_status()
        return DatasourceDataEntry[data_type].model_validate_json(response.text)

    async def get_planning_projects(
        self, from_date: date | None = None, to_date: date | None = None
    ) -> PaginatedResponse[PlanningProject]:
        """
        Get all planning projects
        """
        response = await self.client.get(
            "/datasources/projects",
            params={
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
            },
        )
        logger.debug(response.text)
        response.raise_for_status()
        return PaginatedResponse[PlanningProject].model_validate_json(response.text)

    async def get_planning_project(self, project_id: int) -> DataEntry[PlanningProject]:
        """
        Get a planning project by id
        """
        response = await self.client.get(f"/datasources/projects/{project_id}")
        logger.debug(response.text)
        response.raise_for_status()
        return DataEntry[PlanningProject].model_validate_json(response.text)

    async def update_planning_project(self, project_id: int, update_planning_project: UpdatePlanningProject) -> None:
        """
        Update a planning project

        Args:
            project_id: The id of the project
            update_planning_project: The update planning project
        """
        response = await self.client.put(
            f"/datasources/projects/{project_id}", json=update_planning_project.model_dump(mode="json")
        )
        logger.debug(response.text)
        response.raise_for_status()

    async def delete_planning_project(self, project_id: int) -> None:
        """
        Delete a planning project
        """
        response = await self.client.delete(f"/datasources/projects/{project_id}")
        logger.debug(response.text)
        response.raise_for_status()

    async def get_planning_phases(self, project_id: int) -> DataEntry[list[PlanningPhase]]:
        """
        Get all planning phases
        """
        response = await self.client.get(f"/datasources/project/{project_id}/phases")
        logger.debug(response.text)
        response.raise_for_status()
        return DataEntry[list[PlanningPhase]].model_validate_json(response.text)

    async def get_planning_phase(self, project_id: int, phase_id: int) -> DataEntry[PlanningPhase]:
        """
        Get a planning phase by id
        """
        response = await self.client.get(f"/datasources/project/{project_id}/phases/{phase_id}")
        logger.debug(response.text)
        response.raise_for_status()
        return DataEntry[PlanningPhase].model_validate_json(response.text)

    async def update_planning_phase(self, phase_id: int, update_planning_phase: UpdatePlanningPhase) -> None:
        """
        Update a planning phase
        """

        response = await self.client.put(
            f"/datasources/phases/{phase_id}", json=update_planning_phase.model_dump(mode="json")
        )
        logger.debug(response.text)
        response.raise_for_status()

    async def create_planning_phase(
        self, project_id: int, create_planning_phase: CreatePlanningPhase
    ) -> DataEntry[PlanningPhase]:
        """
        Create a planning phase
        """
        response = await self.client.post(
            f"/datasources/project/{project_id}/phases", json=create_planning_phase.model_dump(mode="json")
        )
        logger.debug(response.text)
        response.raise_for_status()
        return DataEntry[PlanningPhase].model_validate_json(response.text)

    async def get_resources(self) -> PaginatedResponse[Resource]:
        """
        Get all resources
        """
        response = await self.client.get("/datasources/resources")
        logger.debug(response.text)
        response.raise_for_status()
        return PaginatedResponse[Resource].model_validate_json(response.text)

    async def get_projects_of_resource(
        self, resource_id: int, slug: str | None = None, start_date: date | None = None, end_date: date | None = None
    ) -> PaginatedResponse[PlanningProject]:
        """
        Get a list if all projects of every resource
        """
        response = await self.client.get(
            f"/datasources/resources/{resource_id}/projects/{slug or ''}",
            params={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        )
        logger.debug(response.text)
        response.raise_for_status()
        return PaginatedResponse[PlanningProject].model_validate_json(response.text)

    async def get_resource_groups(
        self, resource_id: int, slug: str | None = None
    ) -> PaginatedItemsResponse[ResourceGroup]:
        """
        Get a list of resource groups for a resource

        Args:
            resource_id: The id of the resource
            slug: The slug of the resource group

        Returns:
            PaginatedItemsResponse[ResourceGroup]: The resource groups
        """
        response = await self.client.get(f"/datasources/resources/{resource_id}/{slug or ''}")
        logger.debug(response.text)
        response.raise_for_status()
        return PaginatedItemsResponse[ResourceGroup].model_validate_json(response.text)

    async def create_multiple_allocations(
        self, create_multiple_allocations: CreateMultipleAllocations
    ) -> DataEntry[list[Allocation]]:
        """
        Store an allocation
        """
        response = await self.client.post(
            "/datasources/allocations/multiple", json=create_multiple_allocations.model_dump(mode="json")
        )
        logger.debug(response.text)
        response.raise_for_status()
        return DataEntry[list[Allocation]].model_validate_json(response.text)
