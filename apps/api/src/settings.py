from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_SECRET_KEY: str
    API_SUFFIX: str = Field(default="/api/v1")


settings = Settings()  # type: ignore
