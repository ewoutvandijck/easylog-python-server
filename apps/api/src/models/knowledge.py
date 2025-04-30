from pydantic import BaseModel


class KnowledgeCreateInput(BaseModel):
    subject: str
