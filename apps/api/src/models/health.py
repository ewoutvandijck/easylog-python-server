from typing import Literal

from openai import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"]
