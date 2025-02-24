from httpx import AsyncClient

from .schemas import (
    Datasource,
    DatasourceDataEntry,
    DatasourceDataType,
    PaginatedResponse,
)


class BackendService:
    def __init__(self, bearer_token: str, base_url: str = "https://staging2.easylog.nu/api/v2") -> None:
        self.bearer_token = bearer_token
        self.client = AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            follow_redirects=True
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
