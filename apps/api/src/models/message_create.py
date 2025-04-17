from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    agent_class: str

    model_config = ConfigDict(extra="allow")


class MessageCreateInputFileContent(BaseModel):
    type: Literal["file"] = Field(default="file")
    file_data: str
    file_name: str


class MessageCreateInputImageContent(BaseModel):
    type: Literal["image"] = Field(default="image")
    image_url: str


class MessageCreateInputTextContent(BaseModel):
    type: Literal["text"] = Field(default="text")
    text: str


MessageCreateInputContent = (
    MessageCreateInputFileContent | MessageCreateInputImageContent | MessageCreateInputTextContent
)


class MessageCreateInput(BaseModel):
    content: list[MessageCreateInputContent]

    agent_config: AgentConfig = Field(
        ...,
        description="The configuration for the agent that generated the message. Requires at least a `agent_class` key.",
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello, what color is this image?",
                        },
                        {
                            "type": "image",
                            "image_url": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAE0lEQVR42mP8/5+hngENMNJAEAD4tAx3yVEBjwAAAABJRU5ErkJggg==",
                        },
                    ],
                    "agent_config": {"agent_class": "DebugAgent"},
                }
            ]
        }
    }
