"""
Rate limiting and per-tenant quota management.

Uses slowapi (a port of Flask-Limiter for FastAPI) with in-memory storage by default,
or Redis when configured via REDIS_URL env var.

Rate limit hierarchy:
  • Global: 1000 req/min per IP (burst protection)
  • Authenticated: 100 req/min per user/tenant
  • Cost-intensive endpoints (LLM proxy): 20 req/min per tenant

Tenant quotas:
  • Monthly request quota per tenant (e.g., 100k requests/month)
  • Enforced via middleware checking X-Tenant-ID or JWT tenant claim
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Slowapi Limiter ──────────────────────────────────────────────────────────
def _get_identifier(request: Request) -> str:
    """
    Identify the requester for rate limiting.
    
    Priority: authenticated tenant > authenticated user > IP address.
    """
    # Check for tenant ID from OIDC claims (set by oidc.py middleware)
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return f"tenant:{request.state.tenant_id}"
    
    # Check for user from OIDC claims
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user}"
    
    # Fall back to IP
    return f"ip:{get_remote_address(request)}"


# Global limiter instance
limiter = Limiter(
    key_func=_get_identifier,
    default_limits=["1000/minute"],  # Global burst protection
    storage_uri=settings.redis_url if hasattr(settings, "redis_url") and settings.redis_url else "memory://",
)

# ─── Per-Tenant Monthly Quotas ────────────────────────────────────────────────
# In-memory quota tracking (replace with Redis/DB for multi-instance deployments)
_tenant_quotas: dict[str, int] = defaultdict(int)  # tenant_id -> request_count
_quota_reset_month: Optional[str] = None


def _current_month() -> str:
    """Return YYYY-MM string for the current month."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _reset_quotas_if_new_month() -> None:
    """Reset all tenant quotas if we've entered a new calendar month."""
    global _quota_reset_month, _tenant_quotas
    current = _current_month()
    if _quota_reset_month != current:
        logger.info(f"Resetting tenant quotas for new month: {current}")
        _tenant_quotas.clear()
        _quota_reset_month = current


def check_tenant_quota(request: Request, max_requests_per_month: int = 100_000) -> None:
    """
    Enforce monthly request quota for the authenticated tenant.
    
    Raises HTTPException(429) if quota exceeded.
    
    Args:
        request: FastAPI request object (expects request.state.tenant_id)
        max_requests_per_month: Monthly quota limit
    """
    _reset_quotas_if_new_month()
    
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # No tenant identified — skip quota check
        return
    
    _tenant_quotas[tenant_id] += 1
    used = _tenant_quotas[tenant_id]
    
    if used > max_requests_per_month:
        logger.warning(
            f"Tenant {tenant_id} exceeded monthly quota: {used}/{max_requests_per_month}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly quota exceeded ({used}/{max_requests_per_month}). Resets on the 1st of next month.",
            headers={"X-Quota-Limit": str(max_requests_per_month), "X-Quota-Used": str(used)},
        )
    
    # Log warning at 80% threshold
    if used == int(max_requests_per_month * 0.8):
        logger.warning(f"Tenant {tenant_id} at 80% of monthly quota: {used}/{max_requests_per_month}")


def get_tenant_quota_stats(tenant_id: str) -> dict[str, int]:
    """
    Retrieve quota usage stats for a given tenant.
    
    Returns:
        dict with keys: used, limit, remaining, resets_at (ISO8601 timestamp of next reset)
    """
    _reset_quotas_if_new_month()
    used = _tenant_quotas.get(tenant_id, 0)
    limit = 100_000  # TODO: make this configurable per tenant
    
    # Calculate next reset (first day of next month at 00:00 UTC)
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_reset = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_reset = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    
    return {
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "resets_at": next_reset.isoformat(),
    }
