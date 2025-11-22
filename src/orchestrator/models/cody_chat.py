"""Data models for Cody chat."""

from typing import Literal, List

from pydantic import BaseModel

Role = Literal["system", "user", "assistant"]


class CodyMessage(BaseModel):
    """A single message in a Cody chat conversation."""

    role: Role
    content: str


class CodyChatRequest(BaseModel):
    """Request to chat with Cody."""

    messages: List[CodyMessage]


class CodyChatResponse(BaseModel):
    """Response from Cody chat."""

    reply: str

