from google import genai

from src.settings import settings

gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
