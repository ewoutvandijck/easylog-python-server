from pydantic import BaseModel, Field


class PDFSearchResult(BaseModel):
    id: str | None = Field(
        default=None, description="The ID of the document that was found or none if no document was found"
    )
