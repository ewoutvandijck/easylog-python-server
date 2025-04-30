import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException

from src.lib.graphiti import get_graphiti_connection
from src.lib.prisma import prisma
from src.lib.weaviate import weaviate_client
from src.models.health import HealthResponse
from src.services.easylog.easylog_sql_service import EasylogSqlService
from src.settings import settings

router = APIRouter()


@router.get(
    "/health",
    name="health",
    tags=["health"],
    response_model=HealthResponse,
    description="Returns a 200 status code if the API is healthy.",
)
async def health() -> HealthResponse:
    async def _test_main_db() -> Literal["healthy", "unhealthy"]:
        try:
            await prisma.query_raw("select 1")
            return "healthy"
        except Exception:
            return "unhealthy"

    async def _test_graphiti() -> Literal["healthy", "unhealthy"]:
        try:
            graphiti = get_graphiti_connection()
            await graphiti.driver.verify_connectivity(connection_acquisition_timeout=1)
            await graphiti.search("select 1")
            return "healthy"
        except Exception:
            return "unhealthy"

    async def _test_weaviate() -> Literal["healthy", "unhealthy"]:
        try:
            if not weaviate_client.is_connected():
                raise Exception("Not connected")

            await weaviate_client.collections.list_all()

            return "healthy"

        except Exception:
            return "unhealthy"

    async def _test_easylog_service() -> Literal["healthy", "unhealthy"]:
        try:
            db = EasylogSqlService(
                ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
                ssh_host=settings.EASYLOG_SSH_HOST,
                ssh_username=settings.EASYLOG_SSH_USERNAME,
                db_password=settings.EASYLOG_DB_PASSWORD,
                db_user=settings.EASYLOG_DB_USER,
                db_host=settings.EASYLOG_DB_HOST,
                db_port=settings.EASYLOG_DB_PORT,
                db_name=settings.EASYLOG_DB_NAME,
                connect_timeout=1,
            ).db

            if not db:
                raise HTTPException(status_code=500, detail="Database connection failed")

            with db.cursor() as cursor:
                cursor.execute("select 1")

            return "healthy"
        except Exception:
            return "unhealthy"

    # Run all health checks in parallel
    main_db, easylog_db, neo4j, weaviate = await asyncio.gather(
        _test_main_db(), _test_easylog_service(), _test_graphiti(), _test_weaviate()
    )

    return HealthResponse(api="healthy", main_db=main_db, easylog_db=easylog_db, neo4j=neo4j, weaviate=weaviate)
