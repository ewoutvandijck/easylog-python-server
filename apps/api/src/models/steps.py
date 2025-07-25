from datetime import datetime

from openai import BaseModel
from prisma.enums import health_data_unit, health_platform


class LastSyncedResponse(BaseModel):
    last_synced: datetime


class SyncStepData(BaseModel):
    value: int
    unit: health_data_unit
    date_from: datetime
    date_to: datetime
    source_uuid: str | None = None
    health_platform: health_platform
    source_device_id: str
    source_id: str
    source_name: str


class SyncStepsInput(BaseModel):
    user_id: str
    data_points: list[SyncStepData]
