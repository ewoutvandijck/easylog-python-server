from typing import Literal

from pydantic import BaseModel, Field


class Choice(BaseModel):
    """A choice in a multiple-choice question."""

    label: str = Field(..., description="The (text) label of the choice")
    value: str = Field(..., description="The value of the choice")


class MultipleChoiceWidget(BaseModel):
    """Widget for asking the user a multiple-choice question. When using this widget,DONT WRITE ANY REPLY UNDER THIS WIDGET AFTER A TOOL RESULT."""

    type: Literal["multiple_choice"] = Field(default="multiple_choice", description="The type of widget")
    question: str = Field(..., description="The question text presented to the user")
    choices: list[Choice] = Field(..., description="A list of possible text choices for the user to select from")
    selected_choice: str | None = Field(None, description="The value of the choice that the user has selected")
