"""LLM router — runtime probe + chat proxy."""

from __future__ import annotations

import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from opentelemetry import trace
from opentelemetry.propagate import inject

from app.config import settings
from app.models.llm import (
    ChatRequest,
    ChatResponse,
    LLMRuntimeReport,
)
from app.ratelimit import check_tenant_quota, limiter
from app.services.llm_runtime_service import get_runtime_report

router = APIRouter()
_tracer = trace.get_tracer("vectaris.llm")


@router.get("/runtime", response_model=LLMRuntimeReport)
async def llm_runtime() -> LLMRuntimeReport:
    """Live status + installed models for the configured LLM runtime (Ollama)."""
    return await get_runtime_report()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # Stricter limit for cost-intensive LLM calls
async def llm_chat(request_obj: Request, request: ChatRequest) -> ChatResponse:
    """Proxy a chat completion request to any OpenAI-compatible upstream.

    The upstream URL is resolved in priority order:
    1. ``LLM_CHAT_URL`` env var (explicit override)
    2. ``OLLAMA_BASE_URL`` when ``OLLAMA_ENABLED=true``
    3. ``https://api.openai.com``

    Token counts and end-to-end latency are captured and returned alongside
    the upstream response.
    
    Rate limits:
    - 20 requests/minute per tenant/user/IP
    - Monthly quota of 100k requests per tenant (when authenticated)
    """
    # Enforce monthly tenant quota
    check_tenant_quota(request_obj)
    base_url = _resolve_upstream_url()
    upstream = f"{base_url}/v1/chat/completions"

    body: dict[str, Any] = {
        "model": request.model,
        "messages": [m.model_dump(exclude_none=True) for m in request.messages],
        "stream": False,
        **request.extra,
    }
    if request.temperature is not None:
        body["temperature"] = request.temperature
    if request.max_tokens is not None:
        body["max_tokens"] = request.max_tokens

    headers: dict[str, str] = {"Content-Type": "application/json"}
    api_key = settings.llm_chat_api_key or settings.openai_api_key
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    with _tracer.start_as_current_span("llm.chat.proxy") as span:
        inject(headers)
        span.set_attribute("llm.model", request.model)
        span.set_attribute("llm.upstream", upstream)

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds
            ) as client:
                resp = await client.post(upstream, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Upstream LLM timed out") from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502, detail=f"Upstream LLM unreachable: {exc}"
            ) from exc

        latency_ms = (time.perf_counter() - t0) * 1000
        span.set_attribute("llm.latency_ms", round(latency_ms, 2))

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.text[:512],
        )

    data = resp.json()
    usage_raw = data.get("usage") or {}
    choices_raw = data.get("choices") or []
    choices = [
        {
            "index": c.get("index", 0),
            "message": c.get("message", {"role": "assistant", "content": ""}),
            "finish_reason": c.get("finish_reason"),
        }
        for c in choices_raw
    ]

    return ChatResponse(
        id=data.get("id") or f"chatcmpl-{uuid.uuid4().hex[:12]}",
        object=data.get("object", "chat.completion"),
        model=data.get("model", request.model),
        choices=choices,
        usage={
            "prompt_tokens": usage_raw.get("prompt_tokens", 0),
            "completion_tokens": usage_raw.get("completion_tokens", 0),
            "total_tokens": usage_raw.get("total_tokens", 0),
        },
        latency_ms=round(latency_ms, 2),
        upstream_url=upstream,
    )


def _resolve_upstream_url() -> str:
    if settings.llm_chat_url:
        return settings.llm_chat_url.rstrip("/")
    if settings.ollama_enabled:
        return settings.ollama_base_url.rstrip("/")
    return "https://api.openai.com"


@router.get("/quota")
async def get_quota_stats(request: Request) -> dict[str, Any]:
    """
    Return the current tenant's monthly quota usage.
    
    Returns 404 if no tenant is authenticated.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=404,
            detail="No tenant identified. Quota tracking requires authentication with tenant_id claim.",
        )
    
    from app.ratelimit import get_tenant_quota_stats
    
    return get_tenant_quota_stats(tenant_id)
