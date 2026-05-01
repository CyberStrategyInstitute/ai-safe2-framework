"""
AI SAFE2 MCP Security Toolkit — mcp-scan: Pattern Scanner
Regex-based vulnerability detection for MCP server source code.

Covers all CVE classes from the CSI MCP Threat Intelligence Report
(April 2026) that are detectable via source pattern matching.

Organization:
  CRITICAL_PATTERNS — RCE-002 through RCE-006
  HIGH_PATTERNS     — INJ-001 through INJ-005, SEC-001 through SEC-006
  MEDIUM_PATTERNS   — RL-001, RL-002, LOG-001, LOG-002, MEM-001, STP-001, SWM-001
  MEDIUM_CUSTOM     — CTI-001 (proximity-based, not regex; handled in _scan_medium)
  LOW_PATTERNS      — AUTH-001, DEP-001, CONF-001

Each pattern tuple: (finding_id, compiled_regex, title, description, cve_refs, remediation)
HIGH/MEDIUM add: auto_fixable bool

Detection limits (documented per P2 requirement):
  Absence-class findings (RL-002, MEM-001, STP-001, SWM-001) detect PRESENCE of
  related code and flag it for manual verification. They do NOT confirm that a
  control is missing — that requires human review. Finding descriptions use
  "verify" language to communicate this distinction.
"""
from __future__ import annotations

import re
from typing import Iterator

from aisafe2_mcp_tools.scan.findings import Finding

# ── Retrieval / disclosure verb sets used by CTI-001 proximity check ──────────
_RETRIEVAL_VERBS = re.compile(
    r'\b(get_file|read_document|search_db|fetch_url|read_email|query_db)\s*\(',
    re.IGNORECASE,
)
_DISCLOSURE_VERBS = re.compile(
    r'\b(send_email|post_webhook|write_file|upload|post_slack)\s*\(',
    re.IGNORECASE,
)
_SANITIZE_CALL = re.compile(r'\bsanitize_value\s*\(', re.IGNORECASE)

# Maximum line gap between retrieval and disclosure to be considered a chain
_CTI_MAX_LINE_GAP = 15


# ── Critical patterns — RCE class ─────────────────────────────────────────────
# These require manual review. auto_fixable is always False.
# Correct fix depends on server's intended behavior.

CRITICAL_PATTERNS: list[tuple[str, re.Pattern, str, str, list[str], str]] = [

    ("RCE-002",
     re.compile(r'\bsubprocess\b.*\bshell\s*=\s*True\b|\bshell\s*=\s*True\b.*\bsubprocess\b',
                re.DOTALL),
     "shell=True in subprocess call",
     "shell=True enables shell injection. Any user-controlled content in the command string "
     "becomes arbitrary OS command execution. Root cause pattern of OX Security April 2026 "
     "disclosure. Every affected platform (LiteLLM, LangFlow, Flowise) used this pattern.",
     ["CVE-2026-30623"],
     "Replace shell=True with a list of arguments: subprocess.run(['cmd', arg1, arg2], shell=False). "
     "NEVER join user input into a shell string. See fixes/RCE-002.template"),

    ("RCE-003",
     re.compile(r'\beval\s*\(|\bexec\s*\('),
     "eval() or exec() usage",
     "eval() and exec() execute arbitrary Python code from strings. Any path that allows "
     "external input to reach these calls enables RCE. OWASP A03:2021.",
     [],
     "Replace with safe alternatives: json.loads() for data, explicit dispatch tables for "
     "routing. Never execute dynamic code strings. See fixes/RCE-003.template"),

    ("RCE-004",
     re.compile(r'\byaml\.load\s*\([^,\)]*\)(?!\s*,\s*Loader)', re.DOTALL),
     "Unsafe yaml.load() without Loader argument",
     "yaml.load() without an explicit Loader executes arbitrary Python constructors. "
     "Equivalent to eval() on attacker-controlled YAML. CVE-2025-68145 class.",
     ["CVE-2025-68145"],
     "Replace yaml.load(data) with yaml.safe_load(data). Always. "
     "See fixes/RCE-004.template"),

    ("RCE-005",
     re.compile(r'os\.path\.join\([^\)]*(?:request|user_input|user_file|filename)[^\)]*\)|'
                r'open\([^\)]*(?:request\.|user_input|user_file)[^\)]*\)',
                re.IGNORECASE),
     "Path traversal via unvalidated path construction",
     "Constructing file paths from request data without normalization and containment "
     "allows directory traversal beyond intended boundaries. "
     "CVE-2025-68143 — Path Traversal in MCP Resource URI handling.",
     ["CVE-2025-68143"],
     "Always call os.path.realpath() and verify result starts with allowed base dir: "
     "if not real.startswith(base): raise PermissionError. See fixes/RCE-005.template"),

    ("RCE-006",
     re.compile(r'\bsubprocess\b.*?\bkubectl\b|\bkubectl\b.*?\bsubprocess\b|'
                r'\bPopen\b.*?\bkubectl\b', re.DOTALL | re.IGNORECASE),
     "kubectl invoked via subprocess — argument injection risk",
     "Building kubectl commands from tool parameters via subprocess enables argument injection. "
     "CVE-2026-39884 — mcp-server-kubernetes argument injection via port_forward parameters.",
     ["CVE-2026-39884"],
     "Use the kubernetes Python client library instead of subprocess+kubectl. "
     "from kubernetes import client, config. Never pass tool params into kubectl strings. "
     "See fixes/RCE-006.template"),
]


# ── High patterns ─────────────────────────────────────────────────────────────

HIGH_PATTERNS: list[tuple[str, re.Pattern, str, str, list[str], str, bool]] = [

    ("INJ-001",
     re.compile(r'@mcp\.tool[^#\n]*\n(?:(?!@mcp\.tool)[^\n]*\n)*?[^\n]*\breturn\b(?!\s*sanitize)',
                re.MULTILINE),
     "No output sanitization on tool return",
     "MCP tool returns raw data to LLM clients without injection scanning. "
     "Supply chain compromise of the data source (JSON file, DB, API) could deliver "
     "prompt injection payloads as trusted tool-response content. "
     "AI SAFE2 v3.0 CP.5.MCP-2.",
     [],
     "Wrap every tool return: sanitized, _ = sanitize_value(result, 'tool_name'); return sanitized. "
     "from aisafe2_mcp_tools.shared.patterns import sanitize_value. "
     "See fixes/INJ-001.template",
     True),  # auto_fixable

    ("INJ-003",
     re.compile(r'(?:requests|httpx|aiohttp)\s*\.\s*(?:get|post|put|delete|request)\s*\([^\'\"]*'
                r'(?:url|endpoint|href|uri|target|webhook|callback)',
                re.IGNORECASE | re.DOTALL),
     "HTTP request to URL from tool parameter — SSRF risk",
     "Making HTTP requests with URLs sourced from tool parameters enables SSRF. "
     "CVE-2026-26118 (Azure MCP to AWS credential theft via IMDS). "
     "RAXE-2026-034 (Atlassian SSRF to prompt injection chain via Jira/Confluence).",
     ["CVE-2026-26118", "RAXE-2026-034", "CVE-2025-6607"],
     "Validate URL against SSRF blocklist before making request. "
     "from aisafe2_mcp_tools.shared.patterns import SSRF_BLOCKED_PATTERNS. "
     "Block: 169.254.x.x (IMDS), RFC 1918, loopback, file://. "
     "See fixes/INJ-003.template",
     False),

    ("INJ-005",
     re.compile(r'tools_?list|tool_list|register_tool|add_tool|@mcp\.tool', re.IGNORECASE),
     "Dynamic tool registration — verify rug pull protection",
     "Dynamically registered tools are not locked at install time. Rug pull attack: "
     "legitimate server mutates tool descriptions after trust is established. "
     "Detection requires schema-change monitoring at runtime. "
     "AI SAFE2 v3.0 CP.5.MCP-3.",
     [],
     "Implement schema-change detection: hash tools/list response at startup, "
     "alert on unexpected changes between sessions. "
     "See mcp-safe-wrap schema monitoring and AI SAFE2 CP.5.MCP-3.",
     False),

    ("SEC-001",
     re.compile(r'host\s*=\s*["\']0\.0\.0\.0["\']|MCP_HOST.*0\.0\.0\.0'),
     "Server bound to 0.0.0.0 — all network interfaces",
     "Binding to 0.0.0.0 exposes the MCP server on ALL network interfaces. "
     "Enables NeighborJack (DNS rebinding) attacks. "
     "MCP servers MUST bind to 127.0.0.1 only and use a reverse proxy for external access.",
     [],
     "Change host='0.0.0.0' to host='127.0.0.1'. "
     "Use Caddy or nginx as reverse proxy for external access with TLS. "
     "See fixes/SEC-001.template",
     True),

    ("SEC-003",
     re.compile(r'(?:token|bearer).*?(?:downstream|forward|pass|relay)|'
                r'(?:forward|relay|passthrough).*?token', re.IGNORECASE),
     "OAuth token forwarding — verify audience validation",
     "Forwarding client OAuth tokens to downstream APIs without validating the 'aud' claim "
     "enables token cross-server reuse. "
     "CVE-2025-69196 — FastMCP token cross-server reuse. "
     "CVE-2026-27124 — OAuth confused deputy attack.",
     ["CVE-2025-69196", "CVE-2026-27124"],
     "Validate 'aud' claim matches downstream resource server before forwarding. "
     "Issue new scoped tokens per downstream service rather than forwarding client tokens. "
     "See fixes/SEC-003.template",
     False),

    ("SEC-004",
     re.compile(r'redirect_uri|redirect_url', re.IGNORECASE),
     "OAuth redirect_uri detected — verify allowlisting",
     "OAuth redirect_uri must be strictly allowlisted. "
     "Dynamic Client Registration without redirect_uri restrictions enables "
     "CSRF-style one-click account takeover. "
     "CVE-2026-27124 (FastMCP OAuth confused deputy).",
     ["CVE-2026-27124"],
     "Enforce strict redirect_uri allowlisting. Disable DCR without allowlist. "
     "Validate authorization codes are bound to the user's active session. "
     "See fixes/SEC-004.template",
     False),

    ("SEC-005",
     re.compile(r'session\s*=\s*\{|sessions\s*\[|user_sessions|tenant_data|'
                r'shared_state\s*=', re.IGNORECASE),
     "Shared session/tenant state — verify per-client isolation",
     "Session or tenant state in shared objects can leak across connections. "
     "CVE-2026-25536 — cross-client data leak in multi-tenant MCP. "
     "June 2025 Asana incident — Organization A data visible to Organization B agents.",
     ["CVE-2026-25536"],
     "Ensure session state is isolated per asyncio context or per-request scope. "
     "Never share mutable state between client connections. "
     "See fixes/SEC-005.template",
     False),

    ("SEC-006",
     re.compile(r'os\.path\.join[^\n]*(?!realpath)|'
                r'open\s*\([^\n]*(?:filename|filepath|path)[^\n]*\)(?![^\n]*realpath)',
                re.IGNORECASE),
     "File path construction without containment check",
     "Path operations without realpath() + boundary validation allow symlink attacks "
     "and directory traversal. "
     "August 2025 Anthropic filesystem MCP sandbox escape — CVE-2025-68143.",
     ["CVE-2025-68143"],
     "Always: path = os.path.realpath(os.path.join(base, user_input)); "
     "assert path.startswith(os.path.realpath(base)). "
     "See fixes/SEC-006.template",
     False),
]


# ── Medium patterns ───────────────────────────────────────────────────────────
# Note: CTI-001 is NOT in this list — it uses proximity-based detection
# in PatternScanner._check_cti001() and is called from _scan_medium().

MEDIUM_PATTERNS: list[tuple[str, re.Pattern, str, str, list[str], str, bool]] = [

    ("RL-001",
     re.compile(r'FastMCP|fastmcp|streamable_http_app|Starlette\('),
     "MCP HTTP server — verify application-layer rate limiting",
     "HTTP MCP servers require application-layer rate limiting independent of any reverse "
     "proxy. Caddy/nginx rate limits are bypassed when uvicorn is accessed directly "
     "(Railway direct port, local dev, any deployment without Caddy in the stack). "
     "AI SAFE2 v3.0 CP.5.MCP-6.",
     [],
     "Wire rate limiting into the ASGI app. "
     "Use aisafe2-mcp-tools ratelimit.py or slowapi. "
     "Do NOT rely solely on Caddy/nginx.",
     False),

    ("RL-002",
     re.compile(r'openai\.|anthropic\.|claude\.|AsyncAnthropic\b', re.IGNORECASE),
     "LLM API calls detected — verify per-session cost budget",
     "Agents calling LLM APIs without session-level cost budgets are vulnerable to "
     "billing amplification (Phantom framework — 658x amplification, 97% miss rate). "
     "November 2025 incident: $47,000 API bill from 4-agent infinite retry loop. "
     "Verify per-session token budget and cost ceiling are implemented. "
     "AI SAFE2 v3.0 CP.5.MCP-8.",
     [],
     "Implement per-session token budget and cost ceiling. "
     "Halt and alert when session exceeds 2x expected daily spend. "
     "See AI SAFE2 v3.0 CP.5.MCP-8 (Session Economics).",
     False),

    ("LOG-001",
     re.compile(r'@mcp\.tool'),
     "MCP tool handler — verify audit logging",
     "Every MCP tool invocation must generate an immutable audit record: "
     "tool name, parameters, response hash, timestamp, calling agent identity. "
     "AI SAFE2 v3.0 CP.5.MCP-5.",
     [],
     "Add structlog/logging to every @mcp.tool handler: "
     "log.info('tool.NAME', query=query, tier=tier). "
     "See fixes/LOG-001.template",
     True),

    ("LOG-002",
     re.compile(r'\blogging\.basicConfig\s*\(', re.IGNORECASE),
     "Standard Python logging configured — verify MCP-5 audit compliance",
     "logging.basicConfig() produces human-readable logs that lack the response hash, "
     "calling agent identity, and immutable append-only guarantees required by MCP-5. "
     "Standard Python logging does not satisfy MCP-5 Tool Invocation Audit Log compliance. "
     "Verify that a structured, immutable JSONL audit trail is also implemented. "
     "AI SAFE2 v3.0 CP.5.MCP-5.",
     [],
     "Implement immutable JSONL audit logging alongside standard logging. "
     "Use aisafe2_mcp_tools.wrap.audit.AuditLog or equivalent. "
     "Every tool invocation record must include: tool name, parameters, "
     "response hash, timestamp, and calling agent identity. "
     "See fixes/LOG-001.template for implementation pattern.",
     False),

    ("MEM-001",
     re.compile(r'\bpersist\b|\blong.?term.?memory\b|\bcross.?session\b|'
                r'\bmemory_store\b|\bremember\b', re.IGNORECASE),
     "Persistent memory detected — verify isolation and expiry",
     "Persistent agent memory creates durable attack surfaces. "
     "Claude Code March 2026 source exposure confirmed: tool results treated as "
     "trusted persistent context without guardrails. "
     "Poisoned tool results in persistent memory influence all future sessions. "
     "Verify memory contents are sanitized on read and that expiry is enforced. "
     "AI SAFE2 v3.0 CP.5.MCP-10.",
     [],
     "Implement memory decay/expiry. Validate memory contents on read "
     "using sanitize_value(). Provide a clear-memory endpoint. "
     "Document cross-session persistence in your security attestation.",
     False),

    # ── Schema Temporal Profiling (MCP-11) ────────────────────────────────────
    ("STP-001",
     re.compile(r'tools[/_]list|tools\.list|"tools/list"|list_tools', re.IGNORECASE),
     "tools/list call — verify schema hash pinning at session startup",
     "MCP clients that call tools/list without recording and comparing the response "
     "hash are vulnerable to rug pull attacks (temporal profile: delayed_weeks). "
     "A server with established trust can mutate its tool descriptions between sessions "
     "with no native client detection mechanism. "
     "Verify that tools/list responses are hashed and compared on each session startup. "
     "AI SAFE2 v3.0 CP.5.MCP-11.",
     [],
     "Record the tools/list response hash at deployment (baseline). "
     "Compare the hash at every session startup. "
     "Alert on any hash change not accompanied by a documented release event. "
     "Use mcp-safe-wrap --pin-schema for consumer-side enforcement. "
     "See AI SAFE2 v3.0 CP.5.MCP-11 (Schema Temporal Profiling).",
     False),

    # ── Swarm C2 Detection (MCP-12) — comment lines excluded in _scan_medium ──
    ("SWM-001",
     re.compile(
         r'\b(spawn_agent|create_agent|invoke_agent|agent_pool|orchestrat\w*|swarm\w*|'
         r'multi.?agent\w*|agent_network|delegate_to)\b',
         re.IGNORECASE,
     ),
     "Multi-agent orchestration detected — verify Swarm C2 controls",
     "Code orchestrates multiple agents or spawns sub-agents. "
     "Vectra AI February 2026: MCP can be weaponized as a C2 fabric for offensive "
     "agent swarms. MCP-based C2 traffic is semantically indistinguishable from "
     "legitimate agent coordination at the per-request level. "
     "Verify that behavioral topology monitoring and CP.7 honeypot endpoints are deployed. "
     "AI SAFE2 v3.0 CP.5.MCP-12.",
     [],
     "Establish behavioral baselines for inter-agent communication topology. "
     "Deploy CP.7 honeypot tool endpoints as canaries. "
     "Implement semantic traffic analysis at the orchestration layer. "
     "See AI SAFE2 v3.0 CP.5.MCP-12 (Swarm C2 Detection Controls).",
     False),
]


# ── Low patterns ──────────────────────────────────────────────────────────────

LOW_PATTERNS: list[tuple[str, re.Pattern, str, str, list[str], str]] = [

    ("AUTH-001",
     re.compile(r'TRANSPORT.*?=.*?["\']stdio["\']|transport.*?stdio', re.IGNORECASE),
     "STDIO transport — verify startup security checks",
     "STDIO transport that grants elevated access without identity verification is "
     "vulnerable to malicious project-level settings.json attacks. "
     "OX Security CVE-2026-30615 (Windsurf zero-click injection).",
     ["CVE-2026-30615"],
     "Implement verify_stdio_security() at startup: command allowlist, "
     "install path verification, optional source integrity hash. "
     "Reference: skills/mcp/src/mcp_server/auth.py"),

    ("DEP-001",
     re.compile(r'["\']mcp["\']|["\']fastmcp["\']|["\']langchain["\']|'
                r'["\']litellm["\']|["\']langflow["\']', re.IGNORECASE),
     "MCP dependency — verify version pinning and update policy",
     "Unpinned MCP dependencies can silently upgrade to vulnerable versions. "
     "Supply chain attacks succeed when dependencies are not pinned and verified. "
     "AI SAFE2 v3.0 CP.5.MCP-3.",
     [],
     "Pin all dependencies to exact versions. Use a lockfile (pip-compile or poetry.lock). "
     "Subscribe to security advisories for all MCP-related dependencies."),

    ("CONF-001",
     re.compile(r'(?:api_?key|token|secret|password|credential)\s*=\s*'
                r'["\'][a-zA-Z0-9_\-\.]{10,}["\']', re.IGNORECASE),
     "Potential hardcoded credential",
     "Hardcoded credentials in source code are a primary harvest target in supply "
     "chain attacks. MCP configuration files are specifically targeted. "
     "OX Security September 2025 Postmark incident.",
     [],
     "Move all credentials to environment variables. "
     "Use python-dotenv for local development. "
     "Rotate any credentials that may have been committed to version control."),
]


class PatternScanner:
    """
    Regex-based vulnerability scanner for MCP server source code.
    Works on per-file source strings.

    CTI-001 uses proximity-based detection (_check_cti001) rather than a
    DOTALL regex to avoid false positives from file-wide matching.

    SWM-001 excludes comment-only lines to avoid false positives from
    documentation strings that mention orchestration.
    """

    def scan_file(
        self,
        source: str,
        filepath: str,
        lines: list[str],
    ) -> Iterator[Finding]:
        """Scan one file with all pattern classes. Yields Finding objects."""
        yield from self._scan_critical(source, filepath, lines)
        yield from self._scan_high(source, filepath, lines)
        yield from self._scan_medium(source, filepath, lines)
        yield from self._scan_low(source, filepath, lines)

    def _match_to_finding(
        self,
        m: re.Match,
        source: str,
        filepath: str,
        lines: list[str],
        finding_id: str,
        severity: str,
        title: str,
        description: str,
        cve_refs: list[str],
        remediation: str,
        auto_fixable: bool = False,
    ) -> Finding:
        line_no = source[:m.start()].count("\n") + 1
        snippet = lines[line_no - 1].strip()[:120] if line_no <= len(lines) else ""
        return Finding(
            finding_id=finding_id,
            severity=severity,
            cp5_control=Finding.control_for(finding_id),
            title=title,
            description=description,
            file=filepath,
            line=line_no,
            code_snippet=snippet,
            remediation=remediation,
            cve_refs=cve_refs,
            auto_fixable=auto_fixable,
            manual_required=(severity == "critical"),
        )

    def _make_finding(
        self,
        finding_id: str,
        severity: str,
        title: str,
        description: str,
        remediation: str,
        filepath: str,
        line_no: int,
        lines: list[str],
        cve_refs: list[str] | None = None,
        auto_fixable: bool = False,
    ) -> Finding:
        """Build a Finding directly from components (used by custom checks)."""
        snippet = lines[line_no - 1].strip()[:120] if line_no <= len(lines) else ""
        return Finding(
            finding_id=finding_id,
            severity=severity,
            cp5_control=Finding.control_for(finding_id),
            title=title,
            description=description,
            file=filepath,
            line=line_no,
            code_snippet=snippet,
            remediation=remediation,
            cve_refs=cve_refs or [],
            auto_fixable=auto_fixable,
            manual_required=(severity == "critical"),
        )

    def _scan_critical(
        self, source: str, filepath: str, lines: list[str]
    ) -> Iterator[Finding]:
        seen: set[tuple] = set()
        for finding_id, pattern, title, desc, cves, remediation in CRITICAL_PATTERNS:
            for m in pattern.finditer(source):
                key = (finding_id, source[:m.start()].count("\n") + 1)
                if key in seen:
                    continue
                seen.add(key)
                yield self._match_to_finding(
                    m, source, filepath, lines,
                    finding_id, "critical", title, desc, cves, remediation, False,
                )

    def _scan_high(
        self, source: str, filepath: str, lines: list[str]
    ) -> Iterator[Finding]:
        seen: set[tuple] = set()
        for finding_id, pattern, title, desc, cves, remediation, auto_fix in HIGH_PATTERNS:
            for m in pattern.finditer(source):
                key = (finding_id, source[:m.start()].count("\n") + 1)
                if key in seen:
                    continue
                seen.add(key)
                yield self._match_to_finding(
                    m, source, filepath, lines,
                    finding_id, "high", title, desc, cves, remediation, auto_fix,
                )
                break  # One high finding per pattern per file

    def _scan_medium(
        self, source: str, filepath: str, lines: list[str]
    ) -> Iterator[Finding]:
        """
        Scan medium-severity patterns. Includes two special-case controls:
          SWM-001: Skips comment-only lines to reduce false positives.
          CTI-001: Uses proximity-based detection instead of DOTALL regex.
        """
        seen: set[tuple] = set()
        for finding_id, pattern, title, desc, cves, remediation, auto_fix in MEDIUM_PATTERNS:
            for m in pattern.finditer(source):
                line_no = source[:m.start()].count("\n") + 1

                # SWM-001: skip matches on comment-only lines
                if finding_id == "SWM-001":
                    line_text = lines[line_no - 1].lstrip() if line_no <= len(lines) else ""
                    if line_text.startswith("#"):
                        continue

                key = (finding_id, line_no)
                if key in seen:
                    continue
                seen.add(key)
                yield self._match_to_finding(
                    m, source, filepath, lines,
                    finding_id, "medium", title, desc, cves, remediation, auto_fix,
                )

        # CTI-001: proximity-based retrieval-to-disclosure chain detection
        yield from self._check_cti001(source, filepath, lines)

    def _check_cti001(
        self, source: str, filepath: str, lines: list[str]
    ) -> Iterator[Finding]:
        """
        Detect MCP-UPD retrieval-to-disclosure chains (MCP-9).

        Fires only when:
          - A retrieval call (get_file, search_db, etc.) and a disclosure call
            (send_email, post_webhook, etc.) appear within _CTI_MAX_LINE_GAP lines.
          - sanitize_value() does NOT appear between the retrieval and disclosure.

        This avoids the false positives of a file-wide DOTALL regex, which would
        match retrieval and disclosure calls in completely unrelated functions.
        """
        _TITLE = "Unguarded retrieval-to-disclosure chain — verify MCP-UPD protection"
        _DESC = (
            "A retrieval tool call is followed by a disclosure tool call within "
            f"{_CTI_MAX_LINE_GAP} lines without an intervening sanitize_value() call. "
            "MCP-UPD (Zhao et al. September 2025): 92.9% of MCP server categories can "
            "participate as attack capabilities in a parasitic toolchain attack. "
            "The attack requires zero direct victim interaction. "
            "Verify that externally retrieved data is classified as untrusted data-plane "
            "content and processed through a semantic firewall before any disclosure tool. "
            "AI SAFE2 v3.0 CP.5.MCP-9."
        )
        _REMEDIATION = (
            "Apply sanitize_value() from aisafe2_mcp_tools.shared.patterns to all "
            "externally retrieved content before passing it to any disclosure tool. "
            "Ensure the Agentic Control Plane (CP.4) enforces context-tool isolation "
            "at the orchestration layer, not per-tool. "
            "See AI SAFE2 v3.0 CP.5.MCP-9 (Context-Tool Isolation) and fixes/CTI-001.template."
        )

        retrieval_hits = [
            (m, source[:m.start()].count("\n") + 1)
            for m in _RETRIEVAL_VERBS.finditer(source)
        ]
        disclosure_hits = [
            (m, source[:m.start()].count("\n") + 1)
            for m in _DISCLOSURE_VERBS.finditer(source)
        ]

        seen_lines: set[int] = set()
        for r_match, r_line in retrieval_hits:
            for d_match, d_line in disclosure_hits:
                if d_line <= r_line:
                    continue  # disclosure before retrieval — not the attack pattern
                gap = d_line - r_line
                if gap > _CTI_MAX_LINE_GAP:
                    continue  # too far apart to be the same logical chain

                # Check for sanitize_value between retrieval and disclosure
                between = source[r_match.end():d_match.start()]
                if _SANITIZE_CALL.search(between):
                    continue  # sanitized — no finding

                if r_line in seen_lines:
                    continue
                seen_lines.add(r_line)

                yield self._make_finding(
                    finding_id="CTI-001",
                    severity="medium",
                    title=_TITLE,
                    description=_DESC,
                    remediation=_REMEDIATION,
                    filepath=filepath,
                    line_no=r_line,
                    lines=lines,
                )

    def _scan_low(
        self, source: str, filepath: str, lines: list[str]
    ) -> Iterator[Finding]:
        seen: set[tuple] = set()
        for finding_id, pattern, title, desc, cves, remediation in LOW_PATTERNS:
            for m in pattern.finditer(source):
                key = (finding_id, filepath)  # One LOW finding per finding_id per file
                if key in seen:
                    continue
                seen.add(key)
                yield self._match_to_finding(
                    m, source, filepath, lines,
                    finding_id, "low", title, desc, cves, remediation, False,
                )
