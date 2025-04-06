from typing import Literal

from openai import BaseModel


class HealthResponse(BaseModel):
    api: Literal["healthy"]
    main_db: Literal["healthy", "unhealthy"]
    easylog_db: Literal["healthy", "unhealthy"]
    neo4j: Literal["healthy", "unhealthy"]
