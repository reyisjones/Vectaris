import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_prometheus_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content


def test_request_id_header_roundtrip():
    response = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers.get("X-Request-ID") == "abc-123"


def test_usage_metrics():
    response = client.get("/api/v1/metrics/usage")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "models" in data
    assert len(data["models"]) > 0


def test_latency_metrics():
    response = client.get("/api/v1/metrics/latency")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    for m in data["models"]:
        assert m["p95_ms"] >= m["p50_ms"]
        assert m["p99_ms"] >= m["p95_ms"]


def test_agents_list():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) > 0
    assert all("id" in a for a in agents)


def test_agent_health():
    response = client.get("/api/v1/agents/agent-001/health")
    assert response.status_code == 200
    assert response.json()["agent_id"] == "agent-001"


def test_agent_not_found():
    response = client.get("/api/v1/agents/nonexistent/health")
    assert response.status_code == 404


def test_cost_summary():
    response = client.get("/api/v1/costs")
    assert response.status_code == 200
    data = response.json()
    assert data["total_usd"] > 0
    assert len(data["by_model"]) > 0
    assert len(data["by_team"]) > 0


def test_cost_forecast():
    response = client.get("/api/v1/costs/forecast", params={"horizon_days": 7})
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_days"] == 7
    assert data["projected_usd"] >= 0
    assert data["daily_run_rate_usd"] >= 0


def test_alerts():
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if body:
        assert {"id", "name", "severity", "message"}.issubset(body[0].keys())


@pytest.mark.asyncio
async def test_llm_runtime_disabled_by_default():
    response = client.get("/api/v1/llm/runtime")
    assert response.status_code == 200
    body = response.json()
    assert body["status"]["provider"] == "ollama"
    assert body["status"]["reachable"] is False


def test_api_key_disabled_by_default_allows_protected_path():
    # No API_KEY configured → /api/v1/** is public.
    response = client.get("/api/v1/agents")
    assert response.status_code == 200


def test_api_key_enforced_when_configured(monkeypatch):
    from app import auth as auth_module

    monkeypatch.setattr(auth_module.settings, "api_key", "secret-token")

    # Public paths still work without a key.
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200

    # Protected path without a key is rejected.
    bad = client.get("/api/v1/agents")
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid or missing API key"

    # Protected path with the correct key succeeds.
    ok = client.get("/api/v1/agents", headers={"X-API-Key": "secret-token"})
    assert ok.status_code == 200


# ---------------------------------------------------------------------------
# Agent registry (POST /agents, DELETE, heartbeat)
# ---------------------------------------------------------------------------


def test_register_agent_returns_201():
    payload = {"name": "test-agent", "model": "gpt-4o", "tags": {"env": "ci"}}
    response = client.post("/api/v1/agents", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "test-agent"
    assert body["model"] == "gpt-4o"
    assert body["tags"] == {"env": "ci"}
    assert "id" in body
    assert "registered_at" in body
    # Clean up
    client.delete(f"/api/v1/agents/{body['id']}")


def test_register_agent_with_explicit_id_is_idempotent():
    payload = {"name": "stable-agent", "model": "gpt-4o-mini", "agent_id": "my-pod-1"}
    r1 = client.post("/api/v1/agents", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/agents", json=payload)
    assert r2.status_code == 201
    assert r1.json()["registered_at"] == r2.json()["registered_at"]
    # Clean up
    client.delete("/api/v1/agents/my-pod-1")


def test_delete_agent():
    payload = {"name": "ephemeral-agent", "model": "gpt-4o"}
    agent_id = client.post("/api/v1/agents", json=payload).json()["id"]
    assert client.delete(f"/api/v1/agents/{agent_id}").status_code == 204
    assert client.delete(f"/api/v1/agents/{agent_id}").status_code == 404


def test_agent_heartbeat():
    payload = {"name": "heartbeat-agent", "model": "gpt-4o"}
    agent_id = client.post("/api/v1/agents", json=payload).json()["id"]
    beat = {"status": "degraded", "task_success_rate": 0.75, "uptime_seconds": 120}
    resp = client.patch(f"/api/v1/agents/{agent_id}/heartbeat", json=beat)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["task_success_rate"] == 0.75
    # Clean up
    client.delete(f"/api/v1/agents/{agent_id}")

