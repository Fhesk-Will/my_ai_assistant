from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    metrics: dict = Field(default_factory=dict)


class GuardrailResult(BaseModel):
    passed: bool = True
    blocked_reason: str | None = None
    sanitized_content: str | None = None


class GraphState(TypedDict, total=False):
    message: str
    session_id: str
    history: list
    context: str
    response: str
    metrics: dict
    guardrail_input: dict
    guardrail_output: dict
