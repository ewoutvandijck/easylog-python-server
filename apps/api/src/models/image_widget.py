from typing import Literal

from pydantic import BaseModel, Field


class ImageWidget(BaseModel):
    data: bytes
    content_type: str
    mode: Literal["image", "image_url"] = Field(default="image_url")
