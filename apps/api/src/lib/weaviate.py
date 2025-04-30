import weaviate

from src.settings import settings

weaviate_client = weaviate.use_async_with_local(
    host=settings.WEAVIATE_HOST,
    port=int(settings.WEAVIATE_PORT),
    headers={
        "X-Openai-Api-Key": settings.OPENAI_API_KEY,
    },
)
