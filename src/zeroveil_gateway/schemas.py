from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ChatRole = Literal["system", "user", "assistant", "tool", "function"]
ALLOWED_ROLES: tuple[ChatRole, ...] = ("system", "user", "assistant", "tool", "function")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class ChatMessage(BaseModel):
    role: str
    content: str | None


class RequestMetadata(BaseModel):
    scrubbed: bool = False
    scrubber: str | None = None
    scrubber_version: str | None = None


class ChatCompletionsRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    zdr_only: bool = True
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)


class ChoiceMessage(BaseModel):
    role: ChatRole
    content: str


class Choice(BaseModel):
    index: int
    message: ChoiceMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionsResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Usage
