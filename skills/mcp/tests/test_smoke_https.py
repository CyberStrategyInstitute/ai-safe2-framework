"""
AI SAFE2 MCP Server — HTTPS Smoke Tests
Run against a deployed instance to verify it is functioning correctly.

Usage:
  MCP_SERVER_URL=https://your-domain.com \
  MCP_PRO_TOKEN=pro_your_token \
  MCP_FREE_TOKEN=free_your_token \
  pytest tests/test_smoke_https.py -v

These tests are skipped if MCP_SERVER_URL is not set.
"""
import os
import pytest
import httpx

BASE_URL = os.getenv("MCP_SERVER_URL", "")
PRO_TOKEN = os.getenv("MCP_PRO_TOKEN", "")
FREE_TOKEN = os.getenv("MCP_FREE_TOKEN", "")

skip_if_no_server = pytest.mark.skipif(
    not BASE_URL,
    reason="MCP_SERVER_URL not set — skipping HTTPS smoke tests",
)


def _headers(token: str = "") -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ── Health ────────────────────────────────────────────────────────────────────

@skip_if_no_server
def test_health_endpoint_returns_200():
    """Health endpoint must be reachable without auth."""
    resp = httpx.get(f"{BASE_URL}/health", timeout=15)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["controls_loaded"] == 161

@skip_if_no_server
def test_health_uses_https():
    """Verify TLS is in use (URL starts with https)."""
    assert BASE_URL.startswith("https://"), "Server URL must use HTTPS"

@skip_if_no_server
def test_mcp_endpoint_without_auth_returns_401():
    """MCP endpoint must reject unauthenticated requests."""
    resp = httpx.post(f"{BASE_URL}/mcp", json={}, timeout=15)
    assert resp.status_code == 401

@skip_if_no_server
def test_mcp_endpoint_with_invalid_token_returns_401():
    resp = httpx.post(
        f"{BASE_URL}/mcp",
        json={},
        headers=_headers("invalid_token_12345"),
        timeout=15,
    )
    assert resp.status_code == 401

# ── MCP Protocol ──────────────────────────────────────────────────────────────

@skip_if_no_server
@pytest.mark.skipif(not FREE_TOKEN, reason="MCP_FREE_TOKEN not set")
def test_free_token_authenticates():
    """Free token must be accepted."""
    resp = httpx.post(
        f"{BASE_URL}/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        headers=_headers(FREE_TOKEN),
        timeout=15,
    )
    assert resp.status_code == 200

@skip_if_no_server
@pytest.mark.skipif(not PRO_TOKEN, reason="MCP_PRO_TOKEN not set")
def test_pro_token_authenticates():
    """Pro token must be accepted."""
    resp = httpx.post(
        f"{BASE_URL}/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        headers=_headers(PRO_TOKEN),
        timeout=15,
    )
    assert resp.status_code == 200

@skip_if_no_server
@pytest.mark.skipif(not PRO_TOKEN, reason="MCP_PRO_TOKEN not set")
def test_tool_lookup_control_returns_data():
    """lookup_control tool must return CP.10 when queried by ID."""
    resp = httpx.post(
        f"{BASE_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "lookup_control",
                "arguments": {"control_id": "CP.10"},
            },
            "id": 2,
        },
        headers=_headers(PRO_TOKEN),
        timeout=15,
    )
    assert resp.status_code == 200
    data = resp.json()
    result = data.get("result", {})
    assert "HEAR" in str(result)

@skip_if_no_server
@pytest.mark.skipif(not PRO_TOKEN, reason="MCP_PRO_TOKEN not set")
def test_risk_score_tool_returns_formula_result():
    resp = httpx.post(
        f"{BASE_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "risk_score",
                "arguments": {"cvss_base": 7.5, "pillar_score": 60},
            },
            "id": 3,
        },
        headers=_headers(PRO_TOKEN),
        timeout=15,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "combined_risk_score" in str(data)

# ── Security Headers ──────────────────────────────────────────────────────────

@skip_if_no_server
def test_hsts_header_present():
    """HSTS must be set by Caddy."""
    resp = httpx.get(f"{BASE_URL}/health", timeout=15)
    hsts = resp.headers.get("strict-transport-security", "")
    assert "max-age" in hsts, "Missing HSTS header — check Caddy config"

@skip_if_no_server
def test_x_content_type_options_header():
    resp = httpx.get(f"{BASE_URL}/health", timeout=15)
    assert resp.headers.get("x-content-type-options") == "nosniff"

@skip_if_no_server
def test_no_server_fingerprint():
    resp = httpx.get(f"{BASE_URL}/health", timeout=15)
    server_header = resp.headers.get("server", "")
    assert "caddy" not in server_header.lower(), "Server header should be removed by Caddy config"
