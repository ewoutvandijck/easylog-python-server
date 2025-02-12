from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# Define the generic type variable
PaginatedResponseType = TypeVar("PaginatedResponseType")

DatasourceDataType = TypeVar("DatasourceDataType")


class Datasource(BaseModel):
    id: int
    types: list[str]
    category_id: int | None
    name: str
    description: str
    slug: str
    resource_groups: dict | None
    extra_data_fields: dict | None
    allocation_types: dict | None
    created_at: datetime
    updated_at: datetime


class PaginationLink(BaseModel):
    url: str | None
    label: str
    active: bool


class PaginationLinks(BaseModel):
    first: str
    last: str
    prev: str | None
    next: str | None


class PaginationMeta(BaseModel):
    current_page: int
    from_: int = Field(alias="from")
    last_page: int
    links: list[PaginationLink]
    path: str
    per_page: int
    to: int
    total: int


class PaginatedResponse(BaseModel, Generic[PaginatedResponseType]):
    data: list[PaginatedResponseType]
    links: PaginationLinks
    meta: PaginationMeta


class DatasourceDataEntry(BaseModel, Generic[DatasourceDataType]):
    id: int
    datasource_id: int
    data: DatasourceDataType
    created_at: datetime
    updated_at: datetime
