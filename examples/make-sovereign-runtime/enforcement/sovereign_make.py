"""
sovereign_make.py — Make.com Enforcement Layer
AI SAFE2 v3.0 Sovereign Runtime
Cyber Strategy Institute

Seven enforcement surfaces unique to Make.com visual automation platform.
Make chains modules on a visual canvas — every surface is a different
entry point for an attack that travels silently down the module chain.

  MK-WHK   Webhook payload injection (any external system POSTs arbitrary JSON)
            Recursive scanner — flat string scan misses payload.nested.deep.injection
  MK-SCEN  Module output chaining gate (AI Agent output → next module input)
            Untrusted email/Slack content reaches the AI Agent further down the chain
  MK-HTTP  HTTP module domain restriction (no built-in allowlist in Make)
            SSRF to private IPs + exfiltration to external endpoints
  MK-INST  AI Agent instruction field (persistent system prompt for every run)
            One poisoned instruction save → all future invocations affected
  MK-KNOW  Knowledge file RAG injection (txt/pdf/docx/csv/md/json → vector DB)
            Hidden Unicode (U+200B/U+200C/FEFF) invisible in UI, readable by LLM
  MK-MCP   MCP server scopes (scenarios:write + no allowlist = full account control)
            "View and modify teams and organizations" = account takeover
  MK-DS    Data Store write (persists between runs → cross-run contamination)
            Agent-triggered key writes poison downstream scenario executions

Source verification:
  help.make.com/manage-ai-agents         → MK-INST, MK-SCEN
  help.make.com/knowledge                → MK-KNOW (RAG, file types, chunking)
  developers.make.com/mcp-server         → MK-MCP (scopes, management tools)
  help.make.com/data-stores              → MK-DS

Usage:
  from enforcement.sovereign_make import MakeSovereignRuntime

  guard = MakeSovereignRuntime(
      allowed_http_domains=["api.crm.example.com", "hooks.slack.com"],
      allowed_mcp_scenario_ids=[1234, 5678],
      max_ops_per_scenario_run=500,
  )

  # Before processing any webhook payload:
  guard.scan_webhook_payload(payload_dict, source_id="whk-orders")

  # Before passing module output to next module:
  guard.scan_module_output(output, module_name="AI Agent 1", module_position=3)

  # Before any HTTP module call:
  guard.scan_http_module("https://api.crm.example.com/contacts", "POST", body)

  # Before saving agent instructions:
  guard.scan_agent_instructions(instructions, agent_name="Sales Agent")

  # Before uploading to knowledge base:
  guard.scan_knowledge_file(content, filename="brand-guidelines.md")

  # Before connecting MCP token:
  guard.scan_mcp_scope(["scenarios:read", "scenarios:run"], [1234, 5678])

  # Before any Data Store write:
  guard.scan_data_store_write("customer_profile", value, store_name="crm-cache")
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ai_safe2_engine import AISAFE2Engine, Band, ScanResult, Severity, Violation


# ─────────────────────────────────────────────────────────────
# MK-WHK: Webhook payload injection patterns
# Controls: P1.T1.2, P1.T1.10, S1.3
# ─────────────────────────────────────────────────────────────
_WEBHOOK_INJECT_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior|above)\s+instructions",   "MK.WHK.INJECT"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                            "MK.WHK.INJECT"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",            "MK.WHK.INJECT"),
    (r"(?i)(?:forget|override|bypass)\s+(?:your\s+)?instructions",       "MK.WHK.INJECT"),
    (r"(?i)new\s+instructions?:\s*\n",                                    "MK.WHK.INJECT"),
    (r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[ADMIN\]|\[INST\]",                  "MK.WHK.INJECT"),
    (r"(?i)print\s+(?:your\s+)?(?:system\s+prompt|instructions)",        "MK.WHK.INJECT"),
    (r"(?i)act\s+as\s+(?:a|an|the)\s+(?:root|admin|superuser)",         "MK.WHK.INJECT"),
]

# Make-specific restricted operations that should not appear in webhook payloads
_WEBHOOK_RESTRICTED_OPS: List[str] = [
    "delete scenario", "disable scenario", "stop scenario",
    "delete webhook", "delete connection", "delete team",
    "delete organization", "remove user", "change owner",
    "modify permissions", "grant admin", "revoke access",
    "export all data", "download all", "list all scenarios",
    "list all connections", "list api keys",
]

# ─────────────────────────────────────────────────────────────
# MK-SCEN: Module output gate patterns
# Controls: P1.T1.10, S1.3, P4.T7.1
# ─────────────────────────────────────────────────────────────
_MODULE_OUTPUT_DANGER: List[tuple] = [
    # IPI surviving from earlier module (email/Slack content reaching AI Agent)
    (r"(?i)ignore\s+(all\s+)?previous\s+instructions",                   "MK.SCEN.IPI"),
    (r"(?i)system\s+override",                                            "MK.SCEN.IPI"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                           "MK.SCEN.IPI"),
    (r"(?i)disregard\s+(?:your\s+)?(?:guidelines|rules|constraints)",    "MK.SCEN.IPI"),
    # Escalation detection (agent trying to expand permissions)
    (r"(?i)send\s+(?:all\s+)?(?:emails?|messages?|data)\s+to\s+(?:https?://|http://)", "MK.SCEN.ESCALATE"),
    (r"(?i)(?:forward|exfiltrate|upload)\s+(?:all\s+)?(?:connections?|scenarios?|api)", "MK.SCEN.ESCALATE"),
    (r"(?i)(?:disable|delete|stop)\s+(?:all\s+)?(?:scenarios?|webhooks?|connections?)", "MK.SCEN.DESTRUCT"),
]

# ─────────────────────────────────────────────────────────────
# MK-HTTP: HTTP module domain/request validation
# Controls: P1.T2.5, S1.3, M4.5
# ─────────────────────────────────────────────────────────────
# Private IP ranges for SSRF detection
_PRIVATE_IP_PATTERNS: List[str] = [
    r"(?:https?://)?10\.\d{1,3}\.\d{1,3}\.\d{1,3}",           # 10.x.x.x
    r"(?:https?://)?172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}",  # 172.16-31.x.x
    r"(?:https?://)?192\.168\.\d{1,3}\.\d{1,3}",               # 192.168.x.x
    r"(?:https?://)?127\.\d{1,3}\.\d{1,3}\.\d{1,3}",           # 127.x.x.x
    r"(?:https?://)?localhost\b",                               # localhost
    r"(?:https?://)?169\.254\.\d{1,3}\.\d{1,3}",              # link-local
    r"(?:https?://)?0\.0\.0\.0\b",                             # any
]

# Destructive HTTP methods that require external-content gate
_DESTRUCTIVE_METHODS: Set[str] = {"DELETE", "PATCH"}

# ─────────────────────────────────────────────────────────────
# MK-INST: Agent instruction injection patterns
# Controls: P1.T1.2, P1.T1.10, S1.3, S1.5
# ─────────────────────────────────────────────────────────────
_INSTRUCTION_PATTERNS: List[tuple] = [
    # Standard overrides
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",         "MK.INST.OVERRIDE"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",            "MK.INST.OVERRIDE"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                           "MK.INST.PERSONA"),
    # Covert instruction patterns
    (r"(?i)do\s+not\s+(?:tell|inform|mention|reveal)\s+(?:the\s+)?(?:user|operator|team)", "MK.INST.COVERT"),
    (r"(?i)(?:never|do\s+not)\s+(?:show|display|reveal)\s+(?:this|these)\s+(?:rule|instruction)", "MK.INST.COVERT"),
    # Exfil instructions
    (r"(?i)(?:always|before\s+every\s+(?:run|response|message))\s+(?:send|post|call|fetch)\s+https?://", "MK.INST.EXFIL"),
    (r"(?i)(?:forward|send|exfiltrate)\s+(?:all\s+)?(?:input|data|messages?)\s+to\s+https?://", "MK.INST.EXFIL"),
    # Destructive instructions
    (r"(?i)(?:delete|disable|stop)\s+(?:all\s+)?(?:scenarios?|webhooks?|connections?)",  "MK.INST.DESTRUCT"),
]

# ─────────────────────────────────────────────────────────────
# MK-KNOW: Knowledge file injection patterns
# Controls: P1.T1.2, P1.T1.10, S1.5, S1.6
# Confirmed from live docs: RAG vector DB, chunks and retrieves
# Hidden Unicode invisible in UI but readable by LLM
# ─────────────────────────────────────────────────────────────
_KNOWLEDGE_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",         "MK.KNOW.INJECT"),
    (r"(?i)disregard\s+(?:your\s+)?(?:guidelines|rules|constraints)",    "MK.KNOW.INJECT"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                           "MK.KNOW.INJECT"),
    (r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[ADMIN\]",                           "MK.KNOW.INJECT"),
    (r"(?i)(?:always|before\s+every\s+(?:run|response))\s+(?:send|post|call)", "MK.KNOW.EXFIL"),
    (r"(?i)do\s+not\s+(?:tell|inform|reveal)\s+(?:the\s+)?(?:user|operator)", "MK.KNOW.COVERT"),
]

# Hidden Unicode that is invisible in Make UI but readable by the LLM
_HIDDEN_UNICODE_CHARS: List[str] = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # byte order mark / zero-width no-break space
    "\u00ad",  # soft hyphen
    "\u2028",  # line separator
    "\u2029",  # paragraph separator
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
]

# ─────────────────────────────────────────────────────────────
# MK-MCP: MCP scope and management tool risk
# Controls: P1.T2.5, CP.4, M4.5
# Confirmed: "View and modify teams and organizations" = account takeover
# ─────────────────────────────────────────────────────────────
_HIGH_RISK_MCP_SCOPES: Set[str] = {
    "scenarios:write",
    "scenarios:delete",
    "connections:write",
    "connections:delete",
    "webhooks:write",
    "webhooks:delete",
    "data-stores:write",
    "data-stores:delete",
    "teams:write",
    "organizations:write",
    "users:write",
}

_CRITICAL_MCP_SCOPES: Set[str] = {
    "teams:write",
    "organizations:write",
    "users:write",
}

# ─────────────────────────────────────────────────────────────
# MK-DS: Data Store write restrictions
# Controls: P1.T2.5, S1.5
# ─────────────────────────────────────────────────────────────
_SENSITIVE_DS_KEY_PATTERNS: List[str] = [
    r"(?i)(?:api[_\-]?key|apikey|secret|token|password|credential|auth)",
    r"(?i)(?:private[_\-]?key|signing[_\-]?key|encryption[_\-]?key)",
    r"(?i)(?:webhook[_\-]?url|callback[_\-]?url|exfil)",
    r"(?i)(?:admin|root|superuser|owner)[_\-]?(?:token|key|pass)",
]


# ─────────────────────────────────────────────────────────────
# Main Runtime Class
# ─────────────────────────────────────────────────────────────

class MakeSovereignRuntime:
    """
    AI SAFE2 v3.0 Sovereign Runtime for Make.com.

    Make is a visual no-code canvas where automation logic is built by
    connecting modules in sequence. AI Agents live inside this canvas
    with access to 3000+ app connectors as tools. The MCP Server
    exposes every active scenario as a callable tool for external LLMs.

    This class enforces at every injection surface — webhook ingestion,
    module chaining, HTTP calls, agent instructions, knowledge files,
    MCP scopes, and Data Store writes.
    """

    DEFAULT_MAX_OPS    = 500     # P3.T5.5: operations per scenario run
    DEFAULT_MAX_TURNS  = 50      # F3.2: AI agent turns per run

    def __init__(
        self,
        allowed_http_domains:       Optional[List[str]] = None,
        allowed_mcp_scenario_ids:   Optional[List[int]] = None,
        max_ops_per_scenario_run:   int  = DEFAULT_MAX_OPS,
        max_agent_turns:            int  = DEFAULT_MAX_TURNS,
        audit_log_path:             Optional[Path] = None,
        session_id:                 Optional[str]  = None,
    ) -> None:
        self._allowed_domains   = set(allowed_http_domains or [])
        self._allowed_scenarios = set(allowed_mcp_scenario_ids or [])
        self._max_ops           = max_ops_per_scenario_run
        self._max_turns         = max_agent_turns
        self._engine            = AISAFE2Engine(
            session_id=session_id,
            audit_log_path=audit_log_path,
        )
        self._ops_count         = 0
        self._turn_count        = 0
        self._external_context  = False  # tracks if run ingested external content

    # ── MK-WHK ───────────────────────────────────────────────

    def scan_webhook_payload(
        self,
        payload:   Union[Dict[str, Any], str],
        source_id: str = "webhook",
    ) -> ScanResult:
        """
        Scan webhook payload BEFORE processing in scenario.

        Why it matters: Any external system can POST arbitrary JSON to
        a Make webhook. Make's HTTP module has no built-in input validation.
        The recursive scanner is critical — a flat string scanner misses
        payload.customer.notes.nested_injection.

        Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3
        """
        source     = f"webhook[{source_id}]"
        violations: List[Violation] = []

        # Recursively extract all string values from nested payload
        all_strings = self._extract_strings(payload)
        full_text   = " ".join(all_strings)

        # Engine-level: injection + secrets
        base_result = self._engine.scan_text(full_text, source)
        violations.extend(base_result.violations)

        # Webhook-specific injection patterns
        for pattern, surface_id in _WEBHOOK_INJECT_PATTERNS:
            if re.search(pattern, full_text):
                v = Violation(
                    control_id="P1.T1.2",
                    severity=Severity.CRITICAL,
                    message=f"[{surface_id}] Injection in '{source}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Restricted operation check
        full_lower = full_text.lower()
        for op in _WEBHOOK_RESTRICTED_OPS:
            if op in full_lower:
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.HIGH,
                    message=f"[MK.WHK.RESTRICT] Restricted operation '{op}' in '{source}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Ops rate (P3.T5.5)
        self._ops_count += 1
        if self._ops_count > self._max_ops:
            v = Violation(
                control_id="P3.T5.5",
                severity=Severity.HIGH,
                message=f"Scenario ops ceiling {self._max_ops} exceeded",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Mark external context (payload came from external system)
        self._external_context = True

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 P1.T1.2] [CRITICAL] "
                f"Webhook payload '{source_id}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-SCEN ──────────────────────────────────────────────

    def scan_module_output(
        self,
        output:          Any,
        module_name:     str = "module",
        module_position: int = 0,
    ) -> ScanResult:
        """
        Gate module output BEFORE it becomes input to the next module.

        Why it matters: Make chains modules — output of module 3 is input
        to module 4. Untrusted email or Slack content retrieved in module 2
        can reach an AI Agent in module 5 carrying injected instructions.
        The SilentBridge pattern: external content → AI Agent → Gmail send.

        Controls: P1.T1.10, S1.3, P4.T7.1
        """
        source    = f"module_output[{module_name}@{module_position}]"
        output_str = self._extract_strings(output)
        full_text  = " ".join(output_str)
        violations: List[Violation] = []

        base_result = self._engine.scan_text(full_text, source)
        violations.extend(base_result.violations)

        for pattern, surface_id in _MODULE_OUTPUT_DANGER:
            if re.search(pattern, full_text):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Injection/escalation in output of "
                        f"'{module_name}' (position {module_position}). "
                        f"Will propagate to downstream modules."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        self._turn_count += 1
        if self._turn_count > self._max_turns:
            v = Violation(
                control_id="F3.2",
                severity=Severity.HIGH,
                message=f"Agent turn ceiling {self._max_turns} exceeded",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.SCEN] [CRITICAL] "
                f"Module output from '{module_name}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-HTTP ──────────────────────────────────────────────

    def scan_http_module(
        self,
        url:     str,
        method:  str = "GET",
        body:    Optional[Union[str, Dict]] = None,
        context: Optional[str] = None,
    ) -> ScanResult:
        """
        Validate HTTP module call BEFORE execution.

        Why it matters: Make's HTTP module has no built-in domain restriction.
        When triggered by external content (webhook or email), it becomes
        a direct SSRF or exfiltration vector. DELETE/PATCH requests triggered
        by external content are especially dangerous.

        Controls: P1.T2.5, S1.3, M4.5
        """
        source     = f"http_module[{method} {url[:60]}]"
        violations: List[Violation] = []
        method_upper = method.upper()

        # Domain allowlist check
        if self._allowed_domains:
            parsed_host = self._extract_host(url)
            if not any(parsed_host.endswith(d) for d in self._allowed_domains):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=(
                        f"HTTP {method_upper} to '{parsed_host}' is outside the "
                        f"allowed domain list. Make HTTP module has no built-in restriction."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # SSRF: private IP / localhost
        for pattern in _PRIVATE_IP_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=f"[MK.HTTP.SSRF] Private IP/localhost in HTTP URL: '{url[:80]}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Destructive method during external-content context
        if method_upper in _DESTRUCTIVE_METHODS and self._external_context:
            v = Violation(
                control_id="P4.T7.1",
                severity=Severity.HIGH,
                message=(
                    f"[MK.HTTP.DESTRUCT] {method_upper} request during external-content "
                    f"context. Possible IPI-triggered destructive operation."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Scan body for secrets
        if body:
            body_str = body if isinstance(body, str) else " ".join(self._extract_strings(body))
            secret_result = self._engine.scan_text(body_str, f"{source}.body")
            violations.extend(secret_result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.HTTP] [CRITICAL] "
                f"HTTP {method_upper} to '{url[:60]}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-INST ──────────────────────────────────────────────

    def scan_agent_instructions(
        self,
        instructions: str,
        agent_name:   str = "agent",
    ) -> ScanResult:
        """
        Scan AI Agent instructions BEFORE saving.

        Why it matters (confirmed from live docs): The agent's system prompt
        (instructions field) defines its purpose and constraints for EVERY
        run. One poisoned instruction save affects ALL future invocations
        of that agent — persistent, shared across all team members.

        Controls: P1.T1.2, P1.T1.10, S1.3, S1.5
        """
        source     = f"agent_instructions[{agent_name}]"
        violations: List[Violation] = []

        base_result = self._engine.scan_text(instructions, source)
        violations.extend(base_result.violations)

        for pattern, surface_id in _INSTRUCTION_PATTERNS:
            if re.search(pattern, instructions):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Malicious instruction pattern in "
                        f"agent '{agent_name}'. "
                        f"Affects ALL future runs of this agent."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.INST] [CRITICAL] "
                f"Agent instructions for '{agent_name}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-KNOW ──────────────────────────────────────────────

    def scan_knowledge_file(
        self,
        content:  str,
        filename: str = "knowledge.md",
    ) -> ScanResult:
        """
        Scan knowledge file content BEFORE uploading to RAG vector DB.

        Why it matters (confirmed from live docs): Knowledge files are
        chunked and converted to vectors. The LLM retrieves relevant
        chunks when responding. Hidden Unicode (U+200B/U+200C/FEFF)
        is invisible in the Make UI and GitHub diffs, but the LLM
        reads it in the retrieved chunk — persistent covert instruction.
        Supported types: txt, pdf, docx, csv, md, json.

        Controls: P1.T1.2, P1.T1.10, S1.5, S1.6
        """
        source     = f"knowledge_file[{filename}]"
        violations: List[Violation] = []

        # Engine scan (injection + secrets)
        base_result = self._engine.scan_text(content, source)
        violations.extend(base_result.violations)

        # Knowledge-specific injection patterns
        for pattern, surface_id in _KNOWLEDGE_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Malicious pattern in knowledge file '{filename}'. "
                        f"File is chunked into RAG vector DB — instruction persists "
                        f"in retrieved chunks for all future agent runs."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Hidden Unicode (invisible in UI, readable by LLM)
        for ch in _HIDDEN_UNICODE_CHARS:
            if ch in content:
                v = Violation(
                    control_id="S1.6",
                    severity=Severity.HIGH,
                    message=(
                        f"Hidden Unicode U+{ord(ch):04X} in knowledge file '{filename}'. "
                        f"Invisible in Make UI; readable by LLM in RAG chunks."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.KNOW] [CRITICAL] "
                f"Knowledge file '{filename}' BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-MCP ───────────────────────────────────────────────

    def scan_mcp_scope(
        self,
        scopes:       List[str],
        scenario_ids: Optional[List[int]] = None,
    ) -> ScanResult:
        """
        Validate MCP token scopes BEFORE connecting to Make MCP Server.

        Why it matters (confirmed from live docs): Make MCP Server allows
        LLMs to "run scenarios and manage the contents of your Make account."
        Management scopes include "View and modify teams and organizations"
        = full account takeover. scenarios:write + no scenario allowlist
        = LLM can delete/modify ALL scenarios in the account.

        Controls: P1.T2.5, CP.4, M4.5
        """
        source     = "mcp_scope"
        violations: List[Violation] = []

        # Critical scopes: account/org management
        critical = [s for s in scopes if s in _CRITICAL_MCP_SCOPES]
        if critical:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.CRITICAL,
                message=(
                    f"[MK.MCP.ACCOUNT] Critical MCP scope(s): {critical}. "
                    f"'organizations:write' / 'teams:write' = full account takeover."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # High-risk scopes without scenario allowlist
        high_risk = [s for s in scopes if s in _HIGH_RISK_MCP_SCOPES and s not in _CRITICAL_MCP_SCOPES]
        if high_risk and not self._allowed_scenarios:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.HIGH,
                message=(
                    f"[MK.MCP.NOLIMIT] High-risk MCP scope(s) {high_risk} "
                    f"with no scenario allowlist — applies to ALL scenarios in account."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Scenario allowlist enforcement (CP.4)
        if scenario_ids and self._allowed_scenarios:
            blocked = [sid for sid in scenario_ids if sid not in self._allowed_scenarios]
            if blocked:
                v = Violation(
                    control_id="CP.4",
                    severity=Severity.HIGH,
                    message=(
                        f"[MK.MCP.ALLOWLIST] Scenario IDs {blocked} not in "
                        f"authorized allowlist."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.MCP] [CRITICAL] "
                f"MCP scope BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── MK-DS ────────────────────────────────────────────────

    def scan_data_store_write(
        self,
        key:        str,
        value:      Any,
        store_name: str = "data-store",
    ) -> ScanResult:
        """
        Validate Data Store write BEFORE execution.

        Why it matters: Make Data Stores persist between scenario runs.
        An AI agent writing a poisoned value to a Data Store contaminates
        all FUTURE scenario executions that read that key — cross-run
        contamination that survives scenario restarts and team access.

        Controls: P1.T2.5, S1.5
        """
        source     = f"data_store_write[{store_name}.{key}]"
        violations: List[Violation] = []

        # Sensitive key name check
        for pattern in _SENSITIVE_DS_KEY_PATTERNS:
            if re.search(pattern, key, re.IGNORECASE):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.HIGH,
                    message=(
                        f"[MK.DS.SENSITIVE] Write to sensitive-looking key '{key}' "
                        f"in Data Store '{store_name}'. "
                        f"Data Stores persist between runs — verify this write is intentional."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # Scan value for injection/secrets
        if value is not None:
            value_str = value if isinstance(value, str) else " ".join(self._extract_strings(value))
            if value_str:
                secret_result = self._engine.scan_text(value_str, f"{source}.value")
                violations.extend(secret_result.violations)

                # Check for injection in value
                for pattern, surface_id in _INSTRUCTION_PATTERNS[:4]:  # top override patterns
                    if re.search(pattern, value_str):
                        v = Violation(
                            control_id="S1.5",
                            severity=Severity.HIGH,
                            message=(
                                f"[MK.DS.INJECT] Injection pattern in Data Store "
                                f"value for key '{key}'. "
                                f"Persists across runs — downstream scenarios affected."
                            ),
                            source=source,
                        )
                        violations.append(v)
                        self._engine._record(v)
                        break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 MK.DS] [HIGH] "
                f"Data Store write '{store_name}.{key}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── Helpers ───────────────────────────────────────────────

    def _extract_strings(self, obj: Any, _depth: int = 0) -> List[str]:
        """Recursively extract all string values from nested dicts/lists."""
        if _depth > 10:
            return []
        results = []
        if isinstance(obj, str):
            results.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                results.extend(self._extract_strings(v, _depth + 1))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                results.extend(self._extract_strings(item, _depth + 1))
        elif obj is not None:
            results.append(str(obj))
        return results

    def _extract_host(self, url: str) -> str:
        """Extract hostname from URL."""
        url = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        return url.split("/")[0].split(":")[0].lower()

    def clear_external_context(self) -> None:
        """Reset external-content context flag at scenario boundary."""
        self._external_context = False

    # ── Status / reporting ────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        status = self._engine.get_status()
        status["ops_count"]         = self._ops_count
        status["turn_count"]        = self._turn_count
        status["external_context"]  = self._external_context
        return status

    def compliance_report(self) -> str:
        return self._engine.compliance_report("make-sovereign-runtime")
