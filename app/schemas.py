from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1600)


class Profile(BaseModel):
    education: str = Field(default="", max_length=140)
    interests: str = Field(default="", max_length=180)
    goals: str = Field(default="", max_length=180)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1600)
    history: list[Turn] = Field(default_factory=list, max_length=12)
    profile: Profile = Field(default_factory=Profile)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Please enter a question before submitting.")
        return value.strip()
