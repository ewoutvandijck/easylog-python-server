from fastapi import APIRouter, HTTPException

from src.db.prisma import prisma
from src.models.health import HealthResponse
from src.services.easylog_backend.easylog_sql_service import EasylogSqlService
from src.settings import settings

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

    db = EasylogSqlService(
        ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
        ssh_host=settings.EASYLOG_SSH_HOST,
        ssh_username=settings.EASYLOG_SSH_USERNAME,
        db_password=settings.EASYLOG_DB_PASSWORD,
        db_user=settings.EASYLOG_DB_USER,
        db_host=settings.EASYLOG_DB_HOST,
        db_port=settings.EASYLOG_DB_PORT,
        db_name=settings.EASYLOG_DB_NAME,
    ).db
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")

    with db.cursor() as cursor:
        cursor.execute("select 1")

    return HealthResponse(status="healthy")
