from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_SECRET_KEY: str
    API_ROOT_PATH: str = Field(default="/")
    SUPABASE_URL: str
    SUPABASE_KEY: str

    OPENROUTER_API_KEY: str
    MISTRAL_API_KEY: str

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

    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")

    WEAVIATE_HOST: str = Field(default="localhost")
    WEAVIATE_PORT: str = Field(default="8080")

    SUPABASE_ORIGIN_OVERRIDE: str | None = Field(default=None)
    OPENAI_API_KEY: str
    
    ONESIGNAL_APPERTO_API_KEY: str = Field(default="")
    ONESIGNAL_HEALTH_API_KEY: str = Field(default="")
    ONESIGNAL_HEUVEL_API_KEY: str = Field(default="")

    ONESIGNAL_APPERTO_APP_ID: str = Field(default="0a64ad5c-7330-4c9a-be23-dd905b3753fc'")
    ONESIGNAL_HEALTH_APP_ID: str = Field(default="137356f1-6558-4910-b51e-a9a4bb31a623")
    ONESIGNAL_HEUVEL_APP_ID: str = Field(default="6aafb443-2d4b-4629-9372-2a6d7afae4ee")


settings = Settings()  # type: ignore
