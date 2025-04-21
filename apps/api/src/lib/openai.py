from openai import AsyncOpenAI

from src.settings import settings

openai_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)
