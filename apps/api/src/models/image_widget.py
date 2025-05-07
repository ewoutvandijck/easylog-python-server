from typing import Literal

from pydantic import BaseModel, Field


class ImageWidget(BaseModel):
    # TODO: Implement widget_type
    widget_type: Literal["image"] = Field("image", description="Discriminator for embedded image widget.")
    data: bytes
    content_type: str
    mode: Literal["image", "image_url"] = Field(default="image_url")
