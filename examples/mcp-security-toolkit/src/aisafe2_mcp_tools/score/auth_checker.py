"""
AI SAFE2 MCP Security Toolkit — mcp-score: Auth Checker
Checks MCP-7 (Zero-Trust Client Configuration) and authentication posture.
Separated so auth checking logic can be tested and modified independently.

Scoring:
  No auth (unauthenticated 200):  0/25 — CRITICAL
  Unknown auth (non-401):          0/25 — HIGH
  Auth present (401):              5/25
  Bearer token (401 + WWW-Auth):  15/25
  OAuth 2.1 discovery found:      25/25
"""
from __future__ import annotations

import httpx
import structlog

from aisafe2_mcp_tools.score.models import CheckResult

log = structlog.get_logger()

_REMEDIATION = (
    "Implement OAuth 2.1 with PKCE (RFC 9700). "
    "See AI SAFE2 v3.0 CP.5.MCP-7. "
    "OX Advisory April 2026: unauthenticated servers allow any network "
    "actor to invoke all tools with full permissions."
)


async def check_auth(
    client: httpx.AsyncClient,
    server_url: str,
    unauth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> tuple[CheckResult, dict[str, str]]:
    """
    Check authentication. Returns (CheckResult, response_headers).
    response_headers used by header_checker downstream.
    """
    mcp_request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    resp_headers: dict[str, str] = {}

    try:
        resp = await client.post(server_url, headers=unauth_headers, json=mcp_request)
        resp_headers = dict(resp.headers)

        if resp.status_code == 401:
            www = resp.headers.get("WWW-Authenticate", "").lower()
            score = 15 if "bearer" in www else 5
            detail = f"Auth required (WWW-Authenticate: {www or 'present'})."

            # Check for OAuth 2.1 discovery
            base = server_url.rsplit("/mcp", 1)[0]
            try:
                oauth_resp = await client.get(
                    f"{base}/.well-known/oauth-authorization-server",
                    headers=unauth_headers,
                )
                if oauth_resp.status_code == 200:
                    score = 25
                    detail = "OAuth 2.1 authorization server metadata found. Maximum auth score."
            except Exception:
                pass

            return CheckResult(
                check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                passed=True, score=score, max_score=25, severity="info",
                detail=detail, remediation="",
            ), resp_headers

        if resp.status_code in (200, 201):
            return CheckResult(
                check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                passed=False, score=0, max_score=25, severity="critical",
                detail=(
                    "Unauthenticated access granted. Any actor can invoke all tools. "
                    "492 public unauthenticated servers documented (Trend Micro 2025). "
                    "CVE-2026-30623 class."
                ),
                remediation=_REMEDIATION,
            ), resp_headers

        return CheckResult(
            check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
            passed=False, score=0, max_score=25, severity="high",
            detail=f"Unexpected response: HTTP {resp.status_code}",
            remediation=_REMEDIATION,
        ), resp_headers

    except Exception as exc:
        return CheckResult(
            check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
            passed=False, score=0, max_score=25, severity="high",
            detail=f"Auth check failed: {type(exc).__name__}",
            remediation=_REMEDIATION,
        ), resp_headers
