from datetime import date, datetime
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
    resource_groups: dict | list[dict] | None
    extra_data_fields: dict | list[dict] | None
    allocation_types: dict | list[dict] | None
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
    from_: int | None = Field(alias="from")
    last_page: int
    links: list[PaginationLink]
    path: str
    per_page: int
    to: int | None
    total: int


class PaginatedResponse(BaseModel, Generic[PaginatedResponseType]):
    data: list[PaginatedResponseType]
    links: PaginationLinks | None = None
    meta: PaginationMeta | None = None


class PaginatedItemsResponse(BaseModel, Generic[PaginatedResponseType]):
    items: list[PaginatedResponseType]
    links: PaginationLinks | None = None
    meta: PaginationMeta | None = None


class DatasourceDataEntry(BaseModel, Generic[DatasourceDataType]):
    id: int
    datasource_id: int
    data: DatasourceDataType
    created_at: datetime
    updated_at: datetime


class DataEntry(BaseModel, Generic[DatasourceDataType]):
    data: DatasourceDataType


class AllocationType(BaseModel):
    id: int | None = None
    name: str
    label: str
    slug: str
    start: datetime | None = None
    end: datetime | None = None


class Conflict(BaseModel):
    id: int
    label: str
    project_id: int
    project_label: str
    type: str
    group: str
    start: datetime
    end: datetime
    conflict_start: datetime
    conflict_end: datetime
    created_at: datetime
    updated_at: datetime


class Allocation(BaseModel):
    id: int
    resource_id: int
    label: str
    type: str | None
    group: str
    comment: str | None = ""
    start: datetime
    end: datetime
    fields: dict | list[dict] = Field(default_factory=dict)
    conflicts: list[Conflict] = Field(default_factory=list)
    worked_days: dict | None = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AllocationGroup(BaseModel):
    id: int
    name: str
    label: str
    slug: str
    allocations: list[Allocation]


class PlanningProject(BaseModel):
    id: int
    datasource_id: int
    label: str
    name: str
    start: datetime | None = None
    end: datetime | None = None
    color: str
    extra_data: dict | None = None
    report_visible: bool | None = None
    exclude_in_workdays: bool | None = None
    allocation_types: list[AllocationType]
    allocations_grouped: list[AllocationGroup] | None = None
    created_at: datetime
    updated_at: datetime


class UpdatePlanningProject(BaseModel):
    name: str | None = None
    color: str | None = None
    report_visible: bool | None = None
    exclude_in_workdays: bool | None = None
    start: date | None = None
    end: date | None = None
    extra_data: dict | None = None


class PlanningPhase(BaseModel):
    id: int | None = None
    slug: str | None = None
    project_id: int | None = None
    start: datetime | None = None
    end: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UpdatePlanningPhase(BaseModel):
    start: datetime
    end: datetime


class CreatePlanningPhase(BaseModel):
    slug: str
    start: datetime
    end: datetime


class Resource(BaseModel):
    id: int
    label: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class ResourceGroup(BaseModel):
    id: int
    label: str
    name: str
    slug: str
    data: list[Resource] | None = None
    created_at: datetime
    updated_at: datetime


class CreateResourceAllocation(BaseModel):
    resource_id: int
    type: str
    comment: str | None = None
    start: date
    end: date
    fields: dict | None = None


class CreateMultipleAllocations(BaseModel):
    project_id: int
    group: str
    resources: list[CreateResourceAllocation]


class UpdateResourceAllocation(BaseModel):
    comment: str | None = None
    start: date | None = None
    end: date | None = None
    fields: dict | None = None
