from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_SECRET_KEY: str
    API_ROOT_PATH: str = Field(default="/")
    SUPABASE_URL: str
    SUPABASE_KEY: str
    ADOBE_CLIENT_ID: str
    ADOBE_CLIENT_SECRET: str
    GEMINI_API_KEY: str

    # SSH Settings
    EASYLOG_SSH_KEY_PATH: str | None = Field(default=None)  # ~/.ssh/id_ed25519
    EASYLOG_SSH_HOST: str | None = Field(default=None)  # staging.easylog.nu
    EASYLOG_SSH_USERNAME: str | None = Field(default=None)  # forge

    # Database Settings
    EASYLOG_DB_HOST: str = Field(default="127.0.0.1")
    EASYLOG_DB_PORT: int = Field(default=3306)
    EASYLOG_DB_USER: str = Field(default="easylog")
    EASYLOG_DB_NAME: str = Field(default="easylog")
    EASYLOG_DB_PASSWORD: str = Field(default="")

    EASYLOG_API_URL: str = Field(default="https://staging.easylog.nu/api/v2")


settings = Settings()  # type: ignore
