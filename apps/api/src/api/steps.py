import datetime

from fastapi import APIRouter, HTTPException, Response
from prisma.enums import health_data_point_type, health_data_unit, health_platform
from prisma.types import (
    health_data_pointsCreateWithoutRelationsInput,
    health_data_pointsWhereInput,
    usersCreateInput,
    usersWhereInput,
)

from src.lib.prisma import prisma
from src.logger import logger
from src.models.steps import LastSyncedResponse, SyncStepsInput

router = APIRouter()


@router.get(
    "/steps/last-synced", name="get_last_synced", description="Get the last synced date for steps", tags=["health"]
)
async def last_synced(
    user_id: str,
) -> LastSyncedResponse:
    user = await prisma.users.find_first(where=usersWhereInput(external_id=user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    last_synced = await prisma.health_data_points.find_first(
        where=health_data_pointsWhereInput(user_id=user.id, type=health_data_point_type.steps),
        order={"created_at": "desc"},
    )

    if last_synced is None:
        return LastSyncedResponse(last_synced=datetime.datetime(1970, 1, 1))

    return LastSyncedResponse(last_synced=last_synced.created_at)


@router.post("/steps/sync", name="sync_steps", description="Sync steps data", tags=["health"])
async def sync_steps(
    data: SyncStepsInput,
) -> Response:
    try:
        logger.info(f"Syncing steps data for user {data.user_id} with {len(data.data_points)} data points")
        if data.data_points is None:
            return Response(status_code=200)

        for step_data in data.data_points:
            if step_data.unit != health_data_unit.COUNT:
                raise HTTPException(status_code=400, detail="Invalid unit")

        user = await prisma.users.find_first(where=usersWhereInput(external_id=data.user_id))
        user_id = user.id if user else None
        if user is None:
            user_create = await prisma.users.create(data=usersCreateInput(external_id=data.user_id))
            user_id = user_create.id

        if user_id is None:
            # Cannot be None given the above...
            raise HTTPException(status_code=500, detail="User not found")

        # Map data to prisma insert data
        step_insert_data = [
            health_data_pointsCreateWithoutRelationsInput(
                user_id=user_id,
                type=health_data_point_type.steps,
                value=step_data.value,
                unit=health_data_unit(step_data.unit),
                date_from=step_data.date_from,
                date_to=step_data.date_to,
                source_uuid=step_data.source_uuid,
                health_platform=health_platform(step_data.health_platform),
                source_device_id=step_data.source_device_id,
                source_id=step_data.source_id,
                source_name=step_data.source_name,
            )
            for step_data in data.data_points
        ]

        # TODO: Upsert data!!!
        await prisma.health_data_points.create_many(
            data=step_insert_data,
            skip_duplicates=True,  # This will skip records that violate unique constraints
        )
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error inserting steps data: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
