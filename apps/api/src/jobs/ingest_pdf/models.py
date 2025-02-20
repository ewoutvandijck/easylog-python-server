from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProcessedPDFImage(BaseModel):
    file_name: str
    file_type: Literal["image/png", "image/jpeg"]
    file_data: bytes
    summary: str
    page: int


class ProcessedPDF(BaseModel):
    short_summary: str
    long_summary: str
    markdown_content: str
    file_name: str = Field(default_factory=lambda: f"document_{datetime.now().strftime('%Y%m%d_%H%M%S').lower()}.pdf")
    file_type: Literal["application/pdf"]
    images: list[ProcessedPDFImage]
