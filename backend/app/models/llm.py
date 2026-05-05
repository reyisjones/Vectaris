from datetime import datetime
from typing import Optional

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
