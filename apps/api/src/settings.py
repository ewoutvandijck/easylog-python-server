from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_SECRET_KEY: str
    API_ROOT_PATH: str = Field(default="/")
    SUPABASE_URL: str
    SUPABASE_KEY: str


settings = Settings()  # type: ignore
