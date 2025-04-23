from supabase import AsyncClient, create_async_client

from src.settings import settings


async def create_supabase() -> AsyncClient:
    return await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
    )
