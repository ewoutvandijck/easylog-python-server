from fastapi import APIRouter, HTTPException

from src.db.prisma import prisma
from src.models.health import HealthResponse
from src.services.easylog_backend.easylog_sql_service import EasylogSqlService

router = APIRouter()


@router.get(
    "/health",
    name="health",
    tags=["health"],
    response_model=HealthResponse,
    description="Returns a 200 status code if the API is healthy.",
)
async def health():
    prisma.query_raw("select 1")

    db = EasylogSqlService().db
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")

    with db.cursor() as cursor:
        cursor.execute("select 1")

    return HealthResponse(status="healthy")
