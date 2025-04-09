from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    agent_class: str

    model_config = ConfigDict(extra="allow")


class MessageCreateInputPDFContent(BaseModel):
    file_data: bytes
    file_name: str


class MessageCreateInputImageContent(BaseModel):
    image_url: str


class MessageCreateInputTextContent(BaseModel):
    text: str


class MessageCreateInput(BaseModel):
    content: list[MessageCreateInputPDFContent | MessageCreateInputImageContent | MessageCreateInputTextContent]

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
                            "content": "Hello, what color is this image?",
                        },
                        {
                            "type": "image",
                            "content": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAE0lEQVR42mP8/5+hngENMNJAEAD4tAx3yVEBjwAAAABJRU5ErkJggg==",
                            "content_type": "image/png",
                        },
                    ],
                    "agent_config": {
                        "agent_class": "OpenAIAssistant",
                        "assistant_id": "asst_5vWL7aefIopE4aU5DcFRmpA5",
                    },
                }
            ]
        }
    }
