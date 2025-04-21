from pydantic import BaseModel


class StreamToolCall(BaseModel):
    tool_call_id: str
    name: str
    arguments: str
