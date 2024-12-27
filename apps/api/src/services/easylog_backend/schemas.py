from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Define the generic type variable
PaginatedResponseType = TypeVar("PaginatedResponseType")

DatasourceDataType = TypeVar("DatasourceDataType")


class Datasource(BaseModel):
    id: int
    types: List[str]
    category_id: Optional[int]
    name: str
    description: str
    slug: str
    resource_groups: Optional[dict]
    extra_data_fields: Optional[dict]
    allocation_types: Optional[dict]
    created_at: datetime
    updated_at: datetime


class PaginationLink(BaseModel):
    url: Optional[str]
    label: str
    active: bool


class PaginationLinks(BaseModel):
    first: str
    last: str
    prev: Optional[str]
    next: Optional[str]


class PaginationMeta(BaseModel):
    current_page: int
    from_: int = Field(alias="from")
    last_page: int
    links: List[PaginationLink]
    path: str
    per_page: int
    to: int
    total: int


class PaginatedResponse(BaseModel, Generic[PaginatedResponseType]):
    data: List[PaginatedResponseType]
    links: PaginationLinks
    meta: PaginationMeta


class DatasourceDataEntry(BaseModel, Generic[DatasourceDataType]):
    id: int
    datasource_id: int
    data: DatasourceDataType | dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
