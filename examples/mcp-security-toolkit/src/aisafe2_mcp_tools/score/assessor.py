"""
AI SAFE2 MCP Security Toolkit — mcp-score Remote Assessment Engine

Scores any MCP HTTP server against AI SAFE2 v3.0 CP.5.MCP controls.
All findings include the CP.5.MCP control reference, severity, remediation,
and where applicable the originating CVE.

Bug fixes applied:
  BUG-5: TLS check now tries MCP endpoint if /health returns 404/error
  BUG-6: Rate limit check sends separate unauthenticated probe to verify
          application-layer enforcement independent of auth middleware
  BUG-7: Report serialization uses dataclass fields directly (no double-parse)

Scoring rubric (100 points total):
  Authentication        0–25  (OAuth 2.1=25, bearer token=15, any auth=5, none=0)
  TLS                   0–15  (HTTPS confirmed=12, plain HTTP=0)
  Tool injection scan   0–20  (clean=20; -5 per high pattern; -20 per critical)
  FSP patterns absent   0–10  (clean=10, any FSP=0)
  Security headers      0–10  (2 pts each: HSTS, X-Frame, X-Content-Type,
                                Referrer-Policy, Server header removed)
  Rate limiting         0–10  (429+Retry-After=10, 429 only=5, none=0)
  No session in URL     0–5   (clean=5, session ID found=0)
  SSRF surface          0–5   (no URL params=5, URL params present=2, raw=0)
  Builder attestation   0–25  (bonus points for controls not visible remotely;
                                total score capped at 100)
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog

from aisafe2_mcp_tools.score.models import AttestationData, CheckResult, ScoreReport
from aisafe2_mcp_tools.shared.patterns import (
    INJECTION_PATTERNS,
    SSRF_URL_PATTERNS,
    scan_text,
)
# Sub-module imports (assessor delegates to these)
from aisafe2_mcp_tools.score.auth_checker import check_auth
from aisafe2_mcp_tools.score.header_checker import check_security_headers
from aisafe2_mcp_tools.score.schema_scanner import scan_tool_schemas
from aisafe2_mcp_tools.score.ssrf_detector import check_ssrf_surface
from aisafe2_mcp_tools.score.scorer import (
    compute_attestation_bonus,
    get_rating,
    is_badge_eligible,
)

log = structlog.get_logger()


# ── Data models ───────────────────────────────────────────────────────────────

def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "cp5_control": self.cp5_control,
            "passed": self.passed,
            "score": self.score,
            "max_score": self.max_score,
            "severity": self.severity,
            "detail": self.detail,
            "remediation": self.remediation,
            "findings": self.findings,
        }





# ── Scoring helpers ───────────────────────────────────────────────────────────

# _rating is now in scorer.py — kept as alias for backward compat
_rating = get_rating


_REMEDIATIONS: dict[str, str] = {
    "AUTH": (
        "Implement OAuth 2.1 with PKCE (RFC 9700). "
        "See AI SAFE2 v3.0 CP.5.MCP-7. "
        "OX Advisory April 2026 shows unauthenticated servers allow any network "
        "actor to invoke all tools with full permissions."
    ),
    "TLS": (
        "Enforce HTTPS. Use Caddy (automatic TLS) or nginx with Let's Encrypt. "
        "See AI SAFE2 v3.0 CP.5.MCP-6. "
        "Plain HTTP exposes all credentials and tool payloads in transit."
    ),
    "INJECTION": (
        "Apply output sanitization: from aisafe2_mcp_tools.shared.patterns import sanitize_value. "
        "Wrap every tool return: return sanitize_value(result, 'tool_name')[0]. "
        "See AI SAFE2 v3.0 CP.5.MCP-2."
    ),
    "FSP": (
        "Audit all tool schemas for FSP markers — not just description fields. "
        "Check parameter names, enum values, and response schemas. "
        "CyberArk FSP research (April 2026). See AI SAFE2 v3.0 CP.5.MCP-2."
    ),
    "HEADERS": (
        "Add to your reverse proxy: Strict-Transport-Security, X-Frame-Options: DENY, "
        "X-Content-Type-Options: nosniff, Referrer-Policy: strict-origin. "
        "Remove Server header. See AI SAFE2 v3.0 CP.5.MCP-6."
    ),
    "RATE": (
        "Wire application-layer rate limiting independent of Caddy/nginx. "
        "Use aisafe2-mcp-tools ratelimit.py or slowapi. "
        "Caddy-only rate limits are bypassed by direct port access. "
        "See AI SAFE2 v3.0 CP.5.MCP-6."
    ),
    "SESSION": (
        "Never include session identifiers in URL query parameters. "
        "Use Authorization headers or short-lived cookies. "
        "See AI SAFE2 v3.0 CP.5.MCP-4 and CVE-2025-6515."
    ),
    "SSRF": (
        "Validate all URL parameters against a blocklist before making requests: "
        "block 169.254.x.x (IMDS), RFC 1918, loopback, file:// URIs. "
        "See AI SAFE2 v3.0 CP.5.MCP-6 and CVE-2026-26118."
    ),
}


def _remediation(check_id: str) -> str:
    for key, text in _REMEDIATIONS.items():
        if key in check_id:
            return text
    return "See AI SAFE2 v3.0 CP.5.MCP documentation."


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ── Core assessor ─────────────────────────────────────────────────────────────

class MCPAssessor:
    """
    Black-box remote CP.5.MCP assessment for any MCP HTTP server.

    Authorization: By using mcp-score, the caller attests they are authorized
    to assess the target server. This tool reads only publicly accessible
    endpoints and does not modify server state.

    Usage:
        assessor = MCPAssessor("https://example.com/mcp", token="optional")
        report = await assessor.assess()
    """

    _SECURITY_HEADERS = [
        ("strict-transport-security", "HSTS"),
        ("x-frame-options", "X-Frame-Options"),
        ("x-content-type-options", "X-Content-Type-Options"),
        ("referrer-policy", "Referrer-Policy"),
    ]

    def __init__(
        self,
        server_url: str,
        token: str | None = None,
        timeout: float = 15.0,
        user_agent: str = "aisafe2-mcp-score/1.0 (AI SAFE2 Security Assessment; "
                          "github.com/CyberStrategyInstitute/ai-safe2-framework)",
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._auth_headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Content-Type": "application/json",
        }
        self._unauth_headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Content-Type": "application/json",
        }
        if token:
            self._auth_headers["Authorization"] = f"Bearer {token}"

    async def assess(self) -> ScoreReport:
        """Run the full CP.5.MCP remote assessment. Returns a ScoreReport."""
        start = time.monotonic()
        checks: list[CheckResult] = []
        errors: list[str] = []
        tool_count = 0
        tools_scanned: list[str] = []

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            verify=True,
        ) as client:
            # Check 1: TLS (BUG-5 fix: try MCP endpoint if /health fails)
            tls_check = await self._check_tls(client)
            checks.append(tls_check)

            # Check 2: Authentication + collect response headers for header check
            auth_check, resp_headers = await self._check_auth(client)
            checks.append(auth_check)

            # Check 3: Security response headers
            checks.append(self._check_security_headers(resp_headers))

            # Check 4: Rate limiting (BUG-6 fix: test unauthenticated surface too)
            checks.append(await self._check_rate_limiting(client))

            # Checks 5-8: Tool schema analysis
            tools_result = await self._fetch_tools(client)
            if tools_result is not None:
                tools_data, tool_count, tools_scanned = tools_result
                for check in self._analyze_tools(tools_data):
                    checks.append(check)
            else:
                errors.append(
                    "Could not retrieve tools/list — server may require auth "
                    "or the endpoint is unavailable. Provide --token to enable auth."
                )
                for check_id, name, control, max_s in [
                    ("INJECTION", "Tool Injection Scan", "MCP-2", 20),
                    ("FSP", "Full Schema Poisoning Scan", "MCP-2", 10),
                    ("SSRF", "SSRF Surface", "MCP-6", 5),
                    ("SESSION", "Session ID in URL", "MCP-4", 5),
                ]:
                    checks.append(CheckResult(
                        check_id=check_id, name=name, cp5_control=control,
                        passed=False, score=0, max_score=max_s, severity="medium",
                        detail="Could not assess — tool list unavailable.",
                        remediation=_remediation(check_id),
                    ))

            # Builder attestation
            attestation = await self._fetch_attestation(client)

        base_score = min(100, sum(c.score for c in checks))
        att_bonus = self._compute_attestation_bonus(attestation) if attestation.present else 0
        total_score = min(100, base_score + att_bonus)
        duration = round(time.monotonic() - start, 2)

        return ScoreReport(
            server_url=self.server_url,
            assessment_timestamp=_iso_now(),
            total_score=total_score,
            max_possible=100,
            base_score=base_score,
            attestation_bonus=att_bonus,
            rating=_rating(total_score),
            badge_eligible=(total_score >= 70),
            checks=checks,
            attestation=attestation,
            tool_count=tool_count,
            tools_scanned=tools_scanned,
            errors=errors,
            duration_seconds=duration,
        )

    # ── Individual checks ─────────────────────────────────────────────────────

    async def _check_tls(self, client: httpx.AsyncClient) -> CheckResult:
        """
        TLS check. BUG-5 fix: tries the MCP endpoint if /health returns 404.
        Many MCP servers do not expose a health endpoint.
        """
        if self.server_url.startswith("http://"):
            return CheckResult(
                check_id="TLS", name="TLS Encryption", cp5_control="MCP-6",
                passed=False, score=0, max_score=15, severity="critical",
                detail="Server uses plain HTTP. All credentials and tool payloads are exposed in transit.",
                remediation=_remediation("TLS"),
            )

        # Try /health first, then fall back to the MCP endpoint itself
        for probe_url in (f"{self.server_url}/health", self.server_url):
            try:
                resp = await client.get(probe_url, headers=self._unauth_headers)
                if resp.status_code not in (404, 405):
                    break
            except httpx.ConnectError as exc:
                return CheckResult(
                    check_id="TLS", name="TLS Encryption", cp5_control="MCP-6",
                    passed=False, score=0, max_score=15, severity="critical",
                    detail=f"Could not connect: {exc}. Verify the URL and that the server is running.",
                    remediation=_remediation("TLS"),
                )
            except Exception:
                continue

        return CheckResult(
            check_id="TLS", name="TLS Encryption", cp5_control="MCP-6",
            passed=True, score=12, max_score=15, severity="info",
            detail=(
                "HTTPS confirmed (TLS active). "
                "Note: TLS version (1.2 vs 1.3) requires server configuration audit. "
                "Caddy enforces TLS 1.3 by default."
            ),
            remediation="",
        )

    async def _check_auth(
        self, client: httpx.AsyncClient
    ) -> tuple[CheckResult, dict[str, str]]:
        """
        Authentication check. BUG-6: sends unauthenticated request to verify
        auth is enforced at the server layer (not just at a proxy).
        Returns (CheckResult, response_headers_for_header_check).
        """
        mcp_request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        resp_headers: dict[str, str] = {}

        try:
            # Send unauthenticated
            resp = await client.post(
                self.server_url,
                headers=self._unauth_headers,
                json=mcp_request,
            )
            resp_headers = dict(resp.headers)

            if resp.status_code == 401:
                www = resp.headers.get("WWW-Authenticate", "").lower()
                base_score = 15 if "bearer" in www else 5
                detail = f"Auth required (WWW-Authenticate: {www or 'present'})."

                # Check for OAuth 2.1 discovery endpoint
                base_url = self.server_url.rsplit("/mcp", 1)[0]
                try:
                    oauth_resp = await client.get(
                        f"{base_url}/.well-known/oauth-authorization-server",
                        headers=self._unauth_headers,
                    )
                    if oauth_resp.status_code == 200:
                        base_score = 25
                        detail = "OAuth 2.1 authorization server metadata found. Maximum auth score."
                except Exception:
                    pass

                return CheckResult(
                    check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                    passed=True, score=base_score, max_score=25, severity="info",
                    detail=detail, remediation="",
                ), resp_headers

            if resp.status_code in (200, 201):
                return CheckResult(
                    check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                    passed=False, score=0, max_score=25, severity="critical",
                    detail=(
                        "Unauthenticated access granted to MCP tools. "
                        "Any network-accessible actor can invoke all tools. "
                        "Matches the 492 unauthenticated server pattern (Trend Micro 2025). "
                        "CVE-2026-30623 class."
                    ),
                    remediation=_remediation("AUTH"),
                ), resp_headers

            return CheckResult(
                check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                passed=False, score=0, max_score=25, severity="high",
                detail=f"Unexpected unauthenticated response: HTTP {resp.status_code}",
                remediation=_remediation("AUTH"),
            ), resp_headers

        except Exception as exc:
            return CheckResult(
                check_id="AUTH", name="Authentication Required", cp5_control="MCP-7",
                passed=False, score=0, max_score=25, severity="high",
                detail=f"Auth check failed: {type(exc).__name__}",
                remediation=_remediation("AUTH"),
            ), resp_headers

    def _check_security_headers(self, headers: dict[str, str]) -> CheckResult:
        headers_lower = {k.lower(): v for k, v in headers.items()}
        score = 0
        present: list[str] = []
        missing: list[str] = []

        for header_name, label in self._SECURITY_HEADERS:
            if header_name in headers_lower:
                score += 2
                present.append(label)
            else:
                missing.append(label)

        if "server" not in headers_lower:
            score += 2
            present.append("Server header removed")
        else:
            missing.append(f"Server header exposed: '{headers_lower.get('server', '')}'")

        detail = ""
        if present:
            detail += f"Present: {', '.join(present)}. "
        if missing:
            detail += f"Missing: {', '.join(missing)}."

        return CheckResult(
            check_id="HEADERS", name="Security Response Headers", cp5_control="MCP-6",
            passed=(score >= 8), score=min(10, score), max_score=10,
            severity="medium" if score < 8 else "info",
            detail=detail.strip() or "No headers available.",
            remediation=_remediation("HEADERS") if score < 8 else "",
        )

    async def _check_rate_limiting(self, client: httpx.AsyncClient) -> CheckResult:
        """
        Rate limiting check. BUG-6 fix: sends rapid requests using BOTH
        unauthenticated and authenticated probes to detect application-layer
        rate limiting independent of auth middleware ordering.
        """
        # Use authenticated headers to get past auth middleware if present
        for headers in (self._auth_headers, self._unauth_headers):
            try:
                last_status = 0
                has_retry_after = False
                for i in range(5):
                    resp = await client.post(
                        self.server_url,
                        headers=headers,
                        json={"jsonrpc": "2.0", "id": 100 + i, "method": "tools/list"},
                    )
                    last_status = resp.status_code
                    if resp.status_code == 429:
                        has_retry_after = "retry-after" in {k.lower() for k in resp.headers}
                        if has_retry_after:
                            return CheckResult(
                                check_id="RATE", name="Application-Layer Rate Limiting",
                                cp5_control="MCP-6", passed=True, score=10, max_score=10,
                                severity="info",
                                detail="Rate limiting enforced with Retry-After header. Full points.",
                                remediation="",
                            )
                        return CheckResult(
                            check_id="RATE", name="Application-Layer Rate Limiting",
                            cp5_control="MCP-6", passed=True, score=5, max_score=10,
                            severity="low",
                            detail="Rate limiting enforced but Retry-After header absent. Add for RFC 7231 compliance.",
                            remediation="Add Retry-After header to 429 responses.",
                        )
            except Exception:
                continue

        return CheckResult(
            check_id="RATE", name="Application-Layer Rate Limiting", cp5_control="MCP-6",
            passed=False, score=0, max_score=10, severity="medium",
            detail=(
                "No application-layer rate limiting detected after rapid probing. "
                "Caddy/proxy rate limits are bypassed by direct port access (e.g., Railway, "
                "local dev). AI SAFE2 v3.0 CP.5.MCP-6."
            ),
            remediation=_remediation("RATE"),
        )

    async def _fetch_tools(
        self, client: httpx.AsyncClient
    ) -> tuple[dict, int, list[str]] | None:
        """Fetch tools/list. Returns (data, count, names) or None on failure."""
        try:
            resp = await client.post(
                self.server_url,
                headers=self._auth_headers,
                json={"jsonrpc": "2.0", "id": 99, "method": "tools/list"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            tools = data.get("result", {}).get("tools", [])
            if not isinstance(tools, list):
                return None
            names = [str(t.get("name", "")) for t in tools]
            return data, len(tools), names
        except Exception:
            return None

    def _analyze_tools(self, tools_data: dict) -> list[CheckResult]:
        """Analyze tool schemas. Returns exactly 4 CheckResults."""
        tools = tools_data.get("result", {}).get("tools", [])
        raw_json = json.dumps(tools_data)
        results: list[CheckResult] = []

        # ── Injection scan (MCP-2) ──
        inj_findings: list[dict] = []
        inj_score = 20
        for tool in tools:
            for field_path, text in _extract_strings(tool, tool.get("name", "?")):
                for pattern in INJECTION_PATTERNS:
                    if pattern.regex.search(text):
                        inj_findings.append({
                            "tool": tool.get("name"),
                            "field": field_path,
                            "family": pattern.family,
                            "severity": pattern.severity,
                            "cp5": pattern.cp5_control,
                        })
                        deduction = 20 if pattern.severity == "critical" else 5
                        inj_score = max(0, inj_score - deduction)

        results.append(CheckResult(
            check_id="INJECTION", name="Tool Injection Scan (MCP-2)", cp5_control="MCP-2",
            passed=(len(inj_findings) == 0), score=inj_score, max_score=20,
            severity=(
                "critical" if any(f["severity"] == "critical" for f in inj_findings)
                else "high" if inj_findings else "info"
            ),
            detail=(
                f"{len(inj_findings)} injection pattern(s) in {len(tools)} tools."
                if inj_findings else f"No injection patterns in {len(tools)} tools."
            ),
            remediation=_remediation("INJECTION") if inj_findings else "",
            findings=inj_findings,
        ))

        # ── FSP scan (MCP-2, CyberArk research) ──
        from aisafe2_mcp_tools.shared.patterns import INJECTION_PATTERNS as _IP
        fsp_hits = [
            pat.description[:80]
            for pat in _IP if pat.family == "fsp_schema_poisoning" and pat.regex.search(raw_json)
        ]
        results.append(CheckResult(
            check_id="FSP", name="Full Schema Poisoning (FSP) Scan", cp5_control="MCP-2",
            passed=(not fsp_hits), score=0 if fsp_hits else 10, max_score=10,
            severity="critical" if fsp_hits else "info",
            detail=f"FSP markers: {'; '.join(fsp_hits)}" if fsp_hits else "No FSP markers detected.",
            remediation=_remediation("FSP") if fsp_hits else "",
        ))

        # ── SSRF surface (MCP-6) ──
        ssrf_tools = [
            t.get("name", "?") for t in tools
            if any(p.search(json.dumps(t.get("inputSchema", {}))) for p in SSRF_URL_PATTERNS)
        ]
        ssrf_score = 5 if not ssrf_tools else (2 if len(ssrf_tools) <= 2 else 0)
        results.append(CheckResult(
            check_id="SSRF", name="SSRF Surface Detection", cp5_control="MCP-6",
            passed=(ssrf_score >= 3), score=ssrf_score, max_score=5,
            severity="high" if ssrf_tools else "info",
            detail=(
                f"{len(ssrf_tools)} tool(s) accept URL params: {', '.join(ssrf_tools[:5])}. "
                "Each is a potential SSRF vector (CVE-2026-26118 pattern)."
                if ssrf_tools else "No URL-accepting parameters detected."
            ),
            remediation=_remediation("SSRF") if ssrf_tools else "",
        ))

        # ── Session ID in URL ──
        session_markers = ["sessionid", "session_id", "sid=", "jsessionid"]
        session_found = any(m in raw_json.lower() for m in session_markers)
        results.append(CheckResult(
            check_id="SESSION", name="Session ID in URL Check", cp5_control="MCP-4",
            passed=(not session_found), score=0 if session_found else 5, max_score=5,
            severity="medium" if session_found else "info",
            detail=(
                "Session identifier detected in server responses (CVE-2025-6515 pattern)."
                if session_found else "No session identifiers in URL patterns."
            ),
            remediation=_remediation("SESSION") if session_found else "",
        ))

        return results

    async def _fetch_attestation(self, client: httpx.AsyncClient) -> AttestationData:
        """Fetch /.well-known/mcp-security.json from server root."""
        base = self.server_url.rsplit("/mcp", 1)[0]
        try:
            resp = await client.get(
                f"{base}/.well-known/mcp-security.json",
                headers=self._unauth_headers,
                timeout=5.0,
            )
            if resp.status_code != 200:
                return AttestationData(present=False)
            raw = resp.json()
            controls = raw.get("controls", {})
            return AttestationData(
                present=True,
                server_name=str(raw.get("server_name", "")),
                framework=str(raw.get("framework", "")),
                no_dynamic_commands=bool(controls.get("MCP-1_no_dynamic_commands")),
                output_sanitization=str(controls.get("MCP-2_output_sanitization", "")),
                source_hash=str(controls.get("MCP-4_source_hash", "")),
                rate_limiting=bool(controls.get("MCP-6_rate_limiting")),
                audit_logging=bool(controls.get("MCP-5_audit_logging")),
                network_isolation=str(controls.get("MCP-6_network_isolation", "")),
                session_economics=bool(controls.get("MCP-8_session_economics")),
                context_tool_isolation=str(controls.get("MCP-9_context_tool_isolation", "")),
                multi_agent_provenance=bool(controls.get("MCP-10_multi_agent_provenance")),
                schema_temporal_profiling=bool(controls.get("MCP-11_schema_temporal_profiling")),
                swarm_c2_controls=bool(controls.get("MCP-12_swarm_c2_controls")),
                failure_taxonomy=bool(controls.get("MCP-13_failure_taxonomy")),
                last_assessed=str(raw.get("last_assessed", "")),
                raw=raw,
            )
        except Exception:
            return AttestationData(present=False)

    def _compute_attestation_bonus(self, att: AttestationData) -> int:
        """
        Attestation bonus — risk-weighted across all 13 CP.5.MCP controls (max 25).

        Points are weighted by threat likelihood and confirmed incident impact.
        Higher-risk controls earn more points per ATTESTATION_POINTS in scorer.py.

          +5 MCP-1: no_dynamic_commands  — RCE tier, OX Security confirmed
          +4 MCP-9: context_tool_isolation — 92.9% attack surface (MCP-UPD)
          +3 MCP-2: output_sanitization  — core injection defense
          +3 MCP-8: session_economics    — $47K confirmed, 658x amplification
          +2 MCP-11: schema_temporal_profiling — rug pull, delayed_weeks
          +2 MCP-4: source_hash          — tamper detection
          +2 MCP-5: audit_logging        — forensic foundation
          +1 MCP-10: multi_agent_provenance — lateral movement detection
          +1 MCP-6: network_isolation    — egress control
          +1 MCP-12: swarm_c2_controls   — Swarm C2 detection
          +1 MCP-13: failure_taxonomy    — CP.1 taxonomy correctness
          ─────────────────────────────────────────
          25 total (sum of all 11 fields)

        Total score is capped at 100 regardless of bonus.
        """
        from aisafe2_mcp_tools.score.scorer import ATTESTATION_POINTS
        bonus = 0
        if att.no_dynamic_commands:
            bonus += ATTESTATION_POINTS["no_dynamic_commands"]
        if att.context_tool_isolation:
            bonus += ATTESTATION_POINTS["context_tool_isolation"]
        if att.output_sanitization:
            bonus += ATTESTATION_POINTS["output_sanitization"]
        if att.session_economics:
            bonus += ATTESTATION_POINTS["session_economics"]
        if att.schema_temporal_profiling:
            bonus += ATTESTATION_POINTS["schema_temporal_profiling"]
        if att.source_hash:
            bonus += ATTESTATION_POINTS["source_hash"]
        if att.audit_logging:
            bonus += ATTESTATION_POINTS["audit_logging"]
        if att.multi_agent_provenance:
            bonus += ATTESTATION_POINTS["multi_agent_provenance"]
        if att.network_isolation and (
            "localhost" in att.network_isolation.lower()
            or "127.0.0.1" in att.network_isolation
        ):
            bonus += ATTESTATION_POINTS["network_isolation"]
        if att.swarm_c2_controls:
            bonus += ATTESTATION_POINTS["swarm_c2_controls"]
        if att.failure_taxonomy:
            bonus += ATTESTATION_POINTS["failure_taxonomy"]
        return min(25, bonus)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_strings(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively extract all (path, string) pairs from a JSON-compatible object."""
    results: list[tuple[str, str]] = []
    if isinstance(obj, str):
        results.append((prefix, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(_extract_strings(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(_extract_strings(item, f"{prefix}[{i}]"))
    return results
