from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LLMRuntimeStatus(BaseModel):
    """Health snapshot for a local LLM runtime (e.g. Ollama)."""

    provider: str
    base_url: str
    reachable: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    checked_at: datetime


class LLMModelInfo(BaseModel):
    name: str
    size_bytes: int = Field(ge=0, default=0)
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None
    modified_at: Optional[datetime] = None


class LLMRuntimeReport(BaseModel):
    status: LLMRuntimeStatus
    models: list[LLMModelInfo]


# ---------------------------------------------------------------------------
# Chat proxy models (OpenAI-compatible)
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant|tool)$")
    content: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = False
    # Pass-through extras forwarded unchanged to the upstream provider.
    extra: dict[str, Any] = Field(default_factory=dict)


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage
    # Vectaris instrumentation fields
    latency_ms: float
    upstream_url: str
