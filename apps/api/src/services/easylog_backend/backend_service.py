from datetime import date

from httpx import AsyncClient

from .schemas import (
    Datasource,
    DatasourceDataEntry,
    DatasourceDataType,
    PaginatedResponse,
    PlanningProject,
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

    async def get_datasource_planning_projects(
        self, from_date: date, to_date: date
    ) -> PaginatedResponse[PlanningProject]:
        """
        Get all planning projects
        """
        response = await self.client.get(
            "/planning/projects",
            params={"from_date": from_date.isoformat(), "to_date": to_date.isoformat()},
        )
        response.raise_for_status()
        return PaginatedResponse[PlanningProject].model_validate_json(response.text)

    async def update_planning_project(self, project_id: int, update_planning_project: UpdatePlanningProject) -> None:
        """
        Update a planning project

        Args:
            project_id: The id of the project
            update_planning_project: The update planning project
        """
        response = await self.client.put(f"/planning/projects/{project_id}", json=update_planning_project.model_dump())
        response.raise_for_status()

    async def delete_planning_project(self, project_id: int) -> None:
        """
        Delete a planning project
        """
        response = await self.client.delete(f"/planning/projects/{project_id}")
        response.raise_for_status()
