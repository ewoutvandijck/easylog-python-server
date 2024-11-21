from fastapi import APIRouter

from src.db.prisma import prisma
from src.models.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    name="health",
    tags=["health"],
    response_model=HealthResponse,
    description="Returns a 200 status code if the API is healthy.",
)
async def health():
    await prisma.query_raw("select 1")
    return HealthResponse(status="healthy")
