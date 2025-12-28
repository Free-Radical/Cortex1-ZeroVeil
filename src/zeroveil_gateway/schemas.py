from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class ChatMessage(BaseModel):
    role: str
    content: str


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
    role: str
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

