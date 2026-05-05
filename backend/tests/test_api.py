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

