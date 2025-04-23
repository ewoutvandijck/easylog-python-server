from pydantic import BaseModel


class DocumentPageEntity(BaseModel):
    page_number: int
    markdown: str


class DocumentEntity(BaseModel):
    file_name: str
    document_url: str
    pages: list[DocumentPageEntity]
