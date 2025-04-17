from mistralai import Mistral

from src.settings import settings

mistralai_client = Mistral(settings.MISTRAL_API_KEY)
