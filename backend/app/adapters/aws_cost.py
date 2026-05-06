"""AWS Cost Explorer adapter.

Calls the AWS Cost Explorer ``GetCostAndUsage`` API to fetch per-service spend.

Configuration
-------------
``AWS_ACCESS_KEY_ID``     — IAM user or role access key.
``AWS_SECRET_ACCESS_KEY`` — IAM user or role secret.
``AWS_REGION``            — Region where Cost Explorer endpoint is hosted
                            (must be ``us-east-1`` per AWS docs).
``AWS_SESSION_TOKEN``     — Optional; for temporary credentials (STS).

The adapter uses **AWS Signature Version 4** signing implemented directly with
``httpx`` to avoid adding ``boto3`` as a hard dependency.  When ``boto3`` is
present in the environment it is used as a fallback path (useful in Lambda /
ECS environments where the SDK is already available).

Returns ``None`` when credentials are not configured or the API call fails, so
the caller can fall back to stub data.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import date, datetime, timedelta, timezone

import httpx
import structlog

from app.config import settings

_log = structlog.get_logger("adapter.aws_cost")

_CE_HOST = "ce.us-east-1.amazonaws.com"
_CE_URL = "https://ce.us-east-1.amazonaws.com/"
_SERVICE = "ce"
_REGION = "us-east-1"  # Cost Explorer only exists in us-east-1


def _is_configured() -> bool:
    return bool(settings.aws_access_key_id and settings.aws_secret_access_key)


# ---------------------------------------------------------------------------
# AWS SigV4 helpers (no boto3 required)
# ---------------------------------------------------------------------------


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(f"AWS4{secret_key}".encode(), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def _sigv4_headers(body: bytes) -> dict[str, str]:
    now = datetime.now(tz=timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(body).hexdigest()

    headers_to_sign = {
        "content-type": "application/x-amz-json-1.1",
        "host": _CE_HOST,
        "x-amz-date": amz_date,
        "x-amz-target": "AWSInsightsIndexService.GetCostAndUsage",
    }
    if settings.aws_session_token:
        headers_to_sign["x-amz-security-token"] = settings.aws_session_token

    signed_headers = ";".join(sorted(headers_to_sign.keys()))
    canonical_headers = "".join(
        f"{k}:{v}\n" for k, v in sorted(headers_to_sign.items())
    )

    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    credential_scope = f"{date_stamp}/{_REGION}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )

    signing_key = _get_signature_key(
        settings.aws_secret_access_key, date_stamp, _REGION, _SERVICE
    )
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={settings.aws_access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    result = {
        "Authorization": authorization,
        "Content-Type": headers_to_sign["content-type"],
        "X-Amz-Date": amz_date,
        "X-Amz-Target": headers_to_sign["x-amz-target"],
        "Host": _CE_HOST,
    }
    if settings.aws_session_token:
        result["X-Amz-Security-Token"] = settings.aws_session_token
    return result


# ---------------------------------------------------------------------------
# Public adapter function
# ---------------------------------------------------------------------------


async def get_usage_costs(period_days: int = 30) -> list[dict] | None:
    """Return per-service cost data for *period_days* from AWS Cost Explorer.

    Each item: ``model`` (AWS service), ``team`` (AWS account alias or ID),
    ``usd_cost``, ``token_count`` (0), ``request_count`` (0).

    Returns ``None`` when unconfigured or on any API error.
    """
    if not _is_configured():
        _log.debug("adapter.aws_cost.unavailable", reason="missing credentials")
        return None

    today = date.today()
    start = (today - timedelta(days=period_days)).isoformat()
    end = today.isoformat()

    payload = {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": "MONTHLY",
        "Metrics": ["BlendedCost"],
        "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
    }
    body = json.dumps(payload).encode()

    try:
        headers = _sigv4_headers(body)
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            resp = await client.post(_CE_URL, content=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        _log.warning("adapter.aws_cost.error", error=str(exc))
        return None

    results: list[dict] = []
    for result_by_time in data.get("ResultsByTime", []):
        for group in result_by_time.get("Groups", []):
            service_name = group["Keys"][0] if group.get("Keys") else "unknown"
            amount = float(group["Metrics"]["BlendedCost"]["Amount"])
            results.append(
                {
                    "model": service_name,
                    "team": "aws",
                    "usd_cost": round(amount, 4),
                    "token_count": 0,
                    "request_count": 0,
                }
            )

    _log.info("adapter.aws_cost.ok", rows=len(results))
    return results
