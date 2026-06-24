"""
sovereign_langflow.py — Langflow Enforcement Layer
AI SAFE2 v3.0 Sovereign Runtime
Cyber Strategy Institute

Eight enforcement surfaces unique to Langflow's visual DAG architecture.
Langflow is NOT a Python runtime framework you can wrap with a callback.
This sovereign runtime sits as an EXTERNAL API PROXY between your clients
and Langflow's HTTP endpoints — the only practical enforcement architecture
for a visual drag-and-drop DAG builder.

  LF-WHK   Webhook payload injection (async background runs — no natural gate)
            LANGFLOW_WEBHOOK_AUTH_ENABLE=False = requests run as flow owner
  LF-RUN   Run request tweaks + session_id (tweaks override ANY component field)
            Default session_id = flow ID = ALL users share one chat history
  LF-GVAR  Global variable header injection (X-LANGFLOW-GLOBAL-VAR-* at request time)
            LANGFLOW_DATABASE_URL can be redirected to attacker-controlled host
  LF-KNOW  RAG knowledge ingestion (Chroma/OpenSearch — poisoned doc persists forever)
            Hidden Unicode invisible in Langflow UI; readable by LLM in retrieved chunks
  LF-MCP   MCP auto-exposure (LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=True is DEFAULT)
            Every new project = all flows instantly exposed as MCP tools
  LF-FLOW  Flow JSON import (CustomComponent nodes embed raw Python executed by engine)
            Drag-and-drop import from ANY Langflow page; API key export in JSON
  LF-INST  Agent system_prompt (saved in flow JSON, applied to every user's session)
            One poisoned save = all future runs permanently affected
  LF-COMP  DAG component output chain (URL fetcher → injection → Agent node downstream)
            Injection travels multiple DAG hops with no native gate

Source verification (June 2026):
  docs.langflow.org/webhook           → LF-WHK (async, LANGFLOW_WEBHOOK_AUTH_ENABLE)
  docs.langflow.org/mcp-server        → LF-MCP (auto-add DEFAULT, LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS)
  docs.langflow.org/configuration-global-variables → LF-GVAR
  docs.langflow.org/concepts-flows-import          → LF-FLOW (CustomComponent, API key export)

Architectural note:
  Unlike LangChain, CrewAI, or Make.com, Langflow has no Python callback
  you can hook into. The DAG executes internally. Enforcement must happen:
  (a) BEFORE the request reaches Langflow's API (proxy pattern), or
  (b) AS an inline component node inside the DAG (langflow-component/).
  Both are provided in this package.

Usage:
  from enforcement.sovereign_langflow import LangflowSovereignRuntime

  guard = LangflowSovereignRuntime(
      allowed_global_var_keys=["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
      allowed_mcp_project_ids=["proj-safe-001"],
      webhook_auth_required=True,
  )

  # Before forwarding any webhook POST:
  guard.scan_webhook_payload(payload_dict, flow_id="abc123")

  # Before forwarding any /run or /predict request:
  guard.scan_run_request(flow_id="abc123", input_data="user msg",
                         tweaks=request_tweaks, session_id=sid)

  # Before forwarding any request with X-LANGFLOW-GLOBAL-VAR-* headers:
  guard.scan_global_var_headers(request_headers)

  # Before uploading any knowledge document:
  guard.scan_knowledge_document(content, filename="guide.pdf")

  # Before importing any flow JSON:
  guard.scan_flow_json(flow_json_string)

  # Before saving agent system_prompt:
  guard.scan_agent_instructions(system_prompt, flow_id="abc123")

  # After DAG component produces output (before it reaches next component):
  guard.scan_component_output(output, component_name="URL Fetcher", position=2)

  # Validate MCP configuration on server start:
  guard.scan_mcp_config(auto_expose_enabled=True, exposed_project_ids=["proj-001"])
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ai_safe2_engine import AISAFE2Engine, Band, ScanResult, Severity, Violation


# ─────────────────────────────────────────────────────────────
# LF-WHK: Webhook payload injection patterns
# Controls: P1.T1.2, P1.T1.10, S1.3
# Confirmed: async background run, no natural response gate
# ─────────────────────────────────────────────────────────────
_WEBHOOK_INJECT_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior|above)\s+instructions",   "LF.WHK.INJECT"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                            "LF.WHK.INJECT"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",            "LF.WHK.INJECT"),
    (r"(?i)(?:forget|override|bypass)\s+(?:your\s+)?instructions",       "LF.WHK.INJECT"),
    (r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[ADMIN\]|\[INST\]",                  "LF.WHK.INJECT"),
    (r"(?i)print\s+(?:your\s+)?(?:system\s+prompt|instructions)",        "LF.WHK.INJECT"),
    (r"(?i)(?:exfiltrate|send|forward)\s+(?:all\s+)?(?:data|flows?|api)", "LF.WHK.EXFIL"),
]

# ─────────────────────────────────────────────────────────────
# LF-RUN: Run request tweaks + session_id
# Controls: P1.T1.2, P1.T2.5, S1.5
# tweaks override ANY component field at request time
# Default session_id = flow ID = shared history across all users
# ─────────────────────────────────────────────────────────────
_TWEAKS_DANGEROUS_FIELDS: List[str] = [
    "system_prompt", "template", "prefix_messages",
    "code", "python_code", "script", "command",
    "url", "file_path", "database_url", "connection_string",
]

_TWEAKS_INJECT_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(?:previous|prior)\s+instructions",       "LF.RUN.TWEAKS_INJECT"),
    (r"(?i)exec\s*\(",                                         "LF.RUN.TWEAKS_EXEC"),
    (r"(?i)eval\s*\(",                                         "LF.RUN.TWEAKS_EXEC"),
    (r"(?i)__import__\s*\(",                                   "LF.RUN.TWEAKS_EXEC"),
    (r"(?i)subprocess\s*\.",                                   "LF.RUN.TWEAKS_EXEC"),
    (r"(?i)os\.system\s*\(",                                   "LF.RUN.TWEAKS_EXEC"),
    (r"(?i)open\s*\(\s*['\"](?:/etc|/proc|/sys)",             "LF.RUN.TWEAKS_PATH"),
]

# ─────────────────────────────────────────────────────────────
# LF-GVAR: Global variable header injection
# Controls: P1.T1.10, P1.T2.5, M4.5
# X-LANGFLOW-GLOBAL-VAR-LANGFLOW_DATABASE_URL can redirect DB
# ─────────────────────────────────────────────────────────────
_DANGEROUS_GVAR_KEYS: List[str] = [
    "LANGFLOW_DATABASE_URL",
    "LANGFLOW_SECRET_KEY",
    "LANGFLOW_SUPERUSER_PASSWORD",
    "LANGFLOW_WEBHOOK_AUTH_ENABLE",
    "LANGFLOW_AUTO_LOGIN",
    "LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
]

_GVAR_HEADER_PREFIX = "x-langflow-global-var-"

# ─────────────────────────────────────────────────────────────
# LF-KNOW: RAG knowledge document injection
# Controls: P1.T1.10, S1.5, S1.6
# Chroma (default) or OpenSearch — poisoned doc persists in vector DB
# ─────────────────────────────────────────────────────────────
_KNOWLEDGE_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",      "LF.KNOW.INJECT"),
    (r"(?i)disregard\s+(?:your\s+)?(?:guidelines|rules|constraints)", "LF.KNOW.INJECT"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                        "LF.KNOW.INJECT"),
    (r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[ADMIN\]",                        "LF.KNOW.INJECT"),
    (r"(?i)(?:always|before\s+every)\s+(?:run|response)\s+(?:send|call|post)\s+https?://", "LF.KNOW.EXFIL"),
]

_HIDDEN_UNICODE = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad", "\u2028", "\u2029"]

# ─────────────────────────────────────────────────────────────
# LF-MCP: MCP auto-exposure
# Controls: P1.T2.5, CP.4, M4.5
# LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=True IS THE DEFAULT
# Every new project immediately exposes all flows as MCP tools
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# LF-FLOW: Flow JSON import scan
# Controls: P1.T1.9, P1.T1.10, P1.T1.4_ADV
# CustomComponent embeds raw Python executed by Langflow's build engine
# ─────────────────────────────────────────────────────────────
_FLOW_DANGEROUS_NODE_TYPES: Set[str] = {
    "CustomComponent",
    "PythonFunction",
    "PythonREPL",
    "ShellTool",
    "BashTool",
    "Terminal",
}

_FLOW_CODE_DANGER_PATTERNS: List[tuple] = [
    (r"(?i)(?:subprocess|os\.system|os\.popen)\s*\(",     "LF.FLOW.EXEC"),
    (r"(?i)__import__\s*\(",                              "LF.FLOW.EXEC"),
    (r"(?i)eval\s*\(",                                    "LF.FLOW.EXEC"),
    (r"(?i)exec\s*\(",                                    "LF.FLOW.EXEC"),
    (r"(?i)open\s*\(\s*['\"](?:/etc|/proc|/tmp|/dev)",   "LF.FLOW.PATH"),
    (r"(?i)socket\s*\.\s*(?:connect|bind)\s*\(",          "LF.FLOW.NETWORK"),
    (r"(?i)(?:requests?|httpx|urllib)\s*\.\s*(?:get|post|put)\s*\(", "LF.FLOW.NETWORK"),
]

# ─────────────────────────────────────────────────────────────
# LF-INST: Agent system_prompt injection
# Controls: P1.T1.2, P1.T1.10, S1.3, S1.5
# Saved in flow JSON, applied to EVERY user's session permanently
# ─────────────────────────────────────────────────────────────
_INST_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",       "LF.INST.OVERRIDE"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",          "LF.INST.OVERRIDE"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                         "LF.INST.PERSONA"),
    (r"(?i)do\s+not\s+(?:tell|inform|reveal)\s+(?:the\s+)?(?:user|operator)", "LF.INST.COVERT"),
    (r"(?i)(?:always|before\s+every)\s+(?:response|run)\s+(?:send|post|call)\s+https?://", "LF.INST.EXFIL"),
    (r"(?i)(?:never|do\s+not)\s+(?:show|display|reveal)\s+(?:this|these)\s+(?:rule|instruction)", "LF.INST.HIDDEN"),
    (r"(?i)exfiltrate|send\s+all\s+(?:inputs?|outputs?|data)\s+to\s+https?://", "LF.INST.EXFIL"),
]

# ─────────────────────────────────────────────────────────────
# LF-COMP: Component output chain injection
# Controls: P1.T1.10, P1.T1.5, S1.3
# DAG execution: URL fetcher → Parser → Agent (injection travels hops)
# ─────────────────────────────────────────────────────────────
_COMP_OUTPUT_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",      "LF.COMP.IPI"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                        "LF.COMP.IPI"),
    (r"(?i)system\s+override",                                        "LF.COMP.IPI"),
    (r"(?i)disregard\s+(?:your\s+)?(?:guidelines|rules)",            "LF.COMP.IPI"),
    (r"(?i)(?:send|forward|exfiltrate)\s+(?:all\s+)?(?:data|inputs?|memory)\s+to\s+https?://", "LF.COMP.EXFIL"),
    (r"(?i)(?:call|invoke|use)\s+(?:the\s+)?(?:gmail|slack|email|calendar)\s+(?:tool|component)", "LF.COMP.ESCALATE"),
]


# ─────────────────────────────────────────────────────────────
# Main Runtime Class
# ─────────────────────────────────────────────────────────────

class LangflowSovereignRuntime:
    """
    AI SAFE2 v3.0 Sovereign Runtime for Langflow.

    ARCHITECTURAL NOTE: Langflow is a visual DAG builder. Unlike LangChain
    or CrewAI, there is no Python callback to intercept. This runtime
    implements an EXTERNAL API PROXY pattern — scan requests BEFORE they
    reach Langflow's HTTP endpoints, and scan component outputs AS they
    flow through the DAG (using the inline DAG node in langflow-component/).
    """

    def __init__(
        self,
        allowed_global_var_keys:  Optional[List[str]] = None,
        allowed_mcp_project_ids:  Optional[List[str]] = None,
        webhook_auth_required:    bool                = True,
        auto_login_allowed:       bool                = False,
        audit_log_path:           Optional[Path]      = None,
        session_id:               Optional[str]       = None,
    ) -> None:
        self._allowed_gvar_keys   = set(allowed_global_var_keys or [])
        self._allowed_mcp_ids     = set(allowed_mcp_project_ids or [])
        self._webhook_auth_req    = webhook_auth_required
        self._auto_login_allowed  = auto_login_allowed
        self._engine              = AISAFE2Engine(
            session_id=session_id,
            audit_log_path=audit_log_path,
        )
        self._dag_hops: int = 0   # track component chain depth

    # ── LF-WHK ───────────────────────────────────────────────

    def scan_webhook_payload(
        self,
        payload:   Union[Dict[str, Any], str],
        flow_id:   str = "unknown",
        has_auth:  bool = True,
    ) -> ScanResult:
        """
        Scan webhook payload BEFORE forwarding to POST /v1/webhook/$FLOW_ID.

        Why it matters (confirmed from live docs): The webhook response is
        {"message": "Task started in the background", "status": "in progress"} —
        asynchronous. There is no output gate. When LANGFLOW_WEBHOOK_AUTH_ENABLE=False,
        "requests to the webhook endpoint are treated as being sent by the flow owner."
        One injected payload = one background DAG run under owner privileges.

        Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3
        """
        source     = f"webhook[{flow_id}]"
        violations: List[Violation] = []

        # Auth enforcement gate
        if self._webhook_auth_req and not has_auth:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.CRITICAL,
                message=(
                    f"Webhook request to flow '{flow_id}' has no authentication. "
                    f"LANGFLOW_WEBHOOK_AUTH_ENABLE=False makes requests run as flow owner."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Recursively extract strings from payload
        all_strings = self._extract_strings(payload)
        full_text   = " ".join(all_strings)

        # Engine-level: injection + secrets
        base_result = self._engine.scan_text(full_text, source)
        violations.extend(base_result.violations)

        # Webhook-specific patterns
        for pattern, surface_id in _WEBHOOK_INJECT_PATTERNS:
            if re.search(pattern, full_text):
                v = Violation(
                    control_id="P1.T1.2",
                    severity=Severity.CRITICAL,
                    message=f"[{surface_id}] Injection in '{source}'. Async DAG run — no output gate.",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.WHK] [CRITICAL] "
                f"Webhook payload for flow '{flow_id}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LF-RUN ───────────────────────────────────────────────

    def scan_run_request(
        self,
        flow_id:    str,
        input_data: Optional[str] = None,
        tweaks:     Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan /run or /predict request BEFORE forwarding to Langflow API.

        Why it matters: The tweaks parameter overrides ANY component field
        at request time — including system_prompt, template, code fields,
        and database_url. Default session_id = flow ID = all users share
        one chat history and memory state.

        Controls: P1.T1.2, P1.T2.5, S1.5
        """
        source     = f"run_request[{flow_id}]"
        violations: List[Violation] = []

        # Session ID sharing risk
        if session_id and session_id == flow_id:
            v = Violation(
                control_id="S1.5",
                severity=Severity.HIGH,
                message=(
                    f"session_id equals flow_id '{flow_id}'. "
                    f"ALL users share one chat history and memory state. "
                    f"Use per-user session IDs."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Scan input data
        if input_data:
            base_result = self._engine.scan_text(input_data, f"{source}.input")
            violations.extend(base_result.violations)

        # Scan tweaks (overrides any component field)
        if tweaks:
            for component_key, component_tweaks in tweaks.items():
                if not isinstance(component_tweaks, dict):
                    continue
                for field_key, field_value in component_tweaks.items():
                    # Dangerous field being overridden
                    if field_key.lower() in _TWEAKS_DANGEROUS_FIELDS:
                        val_str = str(field_value) if field_value else ""
                        # Scan for injection in the value
                        for pattern, surface_id in _TWEAKS_INJECT_PATTERNS:
                            if re.search(pattern, val_str):
                                v = Violation(
                                    control_id="P1.T2.5",
                                    severity=Severity.CRITICAL,
                                    message=(
                                        f"[{surface_id}] Code/injection in tweaks "
                                        f"field '{component_key}.{field_key}'. "
                                        f"tweaks can override any component field."
                                    ),
                                    source=source,
                                )
                                violations.append(v)
                                self._engine._record(v)
                                break
                        # Scan value for secrets
                        if val_str:
                            secret_result = self._engine.scan_text(val_str, f"{source}.tweaks.{field_key}")
                            violations.extend(secret_result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.RUN] [CRITICAL] "
                f"Run request for flow '{flow_id}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LF-GVAR ──────────────────────────────────────────────

    def scan_global_var_headers(
        self,
        headers: Dict[str, str],
    ) -> ScanResult:
        """
        Scan request headers for X-LANGFLOW-GLOBAL-VAR-* injection.

        Why it matters: The X-LANGFLOW-GLOBAL-VAR-* header prefix allows
        any request to set global variables at runtime. Setting
        X-LANGFLOW-GLOBAL-VAR-LANGFLOW_DATABASE_URL can redirect your
        production database to an attacker-controlled host.

        Controls: P1.T1.10, P1.T2.5, M4.5
        """
        source     = "global_var_headers"
        violations: List[Violation] = []

        for header_name, header_value in headers.items():
            if not header_name.lower().startswith(_GVAR_HEADER_PREFIX):
                continue

            var_key = header_name[len(_GVAR_HEADER_PREFIX):].upper()

            # Check for dangerous system variable override
            if var_key in _DANGEROUS_GVAR_KEYS:
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[LF.GVAR.DANGEROUS] Header '{header_name}' attempts to override "
                        f"dangerous global variable '{var_key}'. "
                        f"This can redirect database connections or disable authentication."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                continue

            # Check allowlist
            if self._allowed_gvar_keys and var_key not in self._allowed_gvar_keys:
                v = Violation(
                    control_id="M4.5",
                    severity=Severity.HIGH,
                    message=(
                        f"[LF.GVAR.NOALLOWLIST] Global variable '{var_key}' via header "
                        f"is not in the allowlist."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                continue

            # Scan value for secrets
            secret_result = self._engine.scan_text(header_value, f"{source}.{var_key}")
            violations.extend(secret_result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.GVAR] [CRITICAL] "
                f"Global variable header BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LF-KNOW ──────────────────────────────────────────────

    def scan_knowledge_document(
        self,
        content:  str,
        filename: str = "document.pdf",
    ) -> ScanResult:
        """
        Scan knowledge document BEFORE uploading to Langflow's RAG store.

        Why it matters: Langflow uses Chroma (default) or OpenSearch for
        knowledge bases. A poisoned document persists in the vector DB and
        is retrieved for ALL future queries that match its content.
        Hidden Unicode (U+200B etc.) is invisible in the Langflow UI
        but preserved in the vector representation and readable by the LLM.

        Controls: P1.T1.10, S1.5, S1.6
        """
        source     = f"knowledge_document[{filename}]"
        violations: List[Violation] = []

        # Engine-level: injection + secrets
        base_result = self._engine.scan_text(content, source)
        violations.extend(base_result.violations)

        # Knowledge-specific patterns
        for pattern, surface_id in _KNOWLEDGE_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Injection in knowledge '{filename}'. "
                        f"Persists in RAG vector DB for all future queries."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Hidden Unicode (S1.6)
        for ch in _HIDDEN_UNICODE:
            if ch in content:
                v = Violation(
                    control_id="S1.6",
                    severity=Severity.HIGH,
                    message=(
                        f"Hidden Unicode U+{ord(ch):04X} in '{filename}'. "
                        f"Invisible in Langflow UI; readable by LLM in RAG chunks."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.KNOW] [CRITICAL] "
                f"Knowledge document '{filename}' BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LF-MCP ───────────────────────────────────────────────

    def scan_mcp_config(
        self,
        auto_expose_enabled: bool,
        exposed_project_ids: Optional[List[str]] = None,
    ) -> ScanResult:
        """
        Validate MCP configuration at server startup.

        Why it matters (confirmed from live docs): LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS
        defaults to True. "When you create a Langflow project, Langflow automatically
        adds the project to your MCP server's configuration and makes the project's
        flows available as MCP tools." Every new project = immediate exposure.
        Requires LANGFLOW_AUTO_LOGIN=false (AUTH enabled) for MCP API key generation.

        Controls: P1.T2.5, CP.4, M4.5
        """
        source     = "mcp_config"
        violations: List[Violation] = []

        # Auto-expose without allowlist is the critical risk
        if auto_expose_enabled and not self._allowed_mcp_ids:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.CRITICAL,
                message=(
                    "[LF.MCP.NOALLOWLIST] LANGFLOW_ADD_PROJECTS_TO_MCP_SERVERS=True "
                    "with no project allowlist. Every new project immediately exposes "
                    "ALL its flows as MCP tools to any connected client."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Check if auth is enabled (AUTO_LOGIN=false required for MCP API key)
        if self._auto_login_allowed and auto_expose_enabled:
            v = Violation(
                control_id="CP.4",
                severity=Severity.CRITICAL,
                message=(
                    "[LF.MCP.NOAUTH] MCP server exposed with AUTO_LOGIN=true. "
                    "Authentication is required for MCP. "
                    "Set LANGFLOW_AUTO_LOGIN=false to enable MCP API key generation."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Project allowlist enforcement
        if exposed_project_ids and self._allowed_mcp_ids:
            blocked = [p for p in exposed_project_ids if p not in self._allowed_mcp_ids]
            if blocked:
                v = Violation(
                    control_id="CP.4",
                    severity=Severity.HIGH,
                    message=(
                        f"[LF.MCP.ALLOWLIST] Projects {blocked} not in MCP allowlist. "
                        f"Configure allowed_mcp_project_ids."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        if violations and any(v.severity == Severity.CRITICAL for v in violations):
            raise ValueError(
                f"!!! [AI SAFE2 LF.MCP] [CRITICAL] "
                f"MCP configuration BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=not violations, violations=violations, source=source)

    # ── LF-FLOW ──────────────────────────────────────────────

    def scan_flow_json(
        self,
        flow_json: Union[str, Dict],
        filename:  str = "flow.json",
    ) -> ScanResult:
        """
        Scan flow JSON BEFORE importing to Langflow.

        Why it matters (confirmed from live docs): Flow JSON can be imported
        via drag-and-drop from any Langflow page. CustomComponent nodes embed
        raw Python executed by Langflow's build engine. The "Save with my API keys"
        export option embeds literal API key values in the JSON.

        Controls: P1.T1.9, P1.T1.10, P1.T1.4_ADV
        """
        source     = f"flow_json[{filename}]"
        violations: List[Violation] = []

        # Parse JSON
        try:
            flow_data = json.loads(flow_json) if isinstance(flow_json, str) else flow_json
        except (json.JSONDecodeError, TypeError):
            v = Violation(
                control_id="P1.T1.9",
                severity=Severity.HIGH,
                message=f"Invalid JSON in flow file '{filename}' — cannot validate",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)
            raise ValueError(f"!!! [AI SAFE2 LF.FLOW] [HIGH] Invalid flow JSON: '{filename}'")

        # Scan all nodes
        nodes = []
        if "data" in flow_data and "nodes" in flow_data.get("data", {}):
            nodes = flow_data["data"]["nodes"]
        elif "nodes" in flow_data:
            nodes = flow_data["nodes"]

        for node in nodes:
            node_type = node.get("data", {}).get("type", "")
            node_id   = node.get("id", "?")
            template  = node.get("data", {}).get("node", {}).get("template", {})

            # Dangerous node types (CustomComponent embeds raw Python)
            if node_type in _FLOW_DANGEROUS_NODE_TYPES:
                code_field = template.get("code", {}).get("value", "") or ""
                for pattern, surface_id in _FLOW_CODE_DANGER_PATTERNS:
                    if re.search(pattern, code_field):
                        v = Violation(
                            control_id="P1.T1.9",
                            severity=Severity.CRITICAL,
                            message=(
                                f"[{surface_id}] Dangerous code pattern in "
                                f"node '{node_id}' (type: {node_type}). "
                                f"CustomComponent executes raw Python via Langflow's build engine."
                            ),
                            source=source,
                        )
                        violations.append(v)
                        self._engine._record(v)
                        break

                # Also flag any CustomComponent for HITL review
                if node_type == "CustomComponent" and not violations:
                    v = Violation(
                        control_id="P1.T1.9",
                        severity=Severity.HIGH,
                        message=(
                            f"[LF.FLOW.NODETYPE] CustomComponent node '{node_id}' found. "
                            f"Review embedded Python code before importing."
                        ),
                        source=source,
                    )
                    violations.append(v)
                    self._engine._record(v)

            # Scan all template field values for secrets
            for field_key, field_data in template.items():
                if isinstance(field_data, dict):
                    val = str(field_data.get("value", "") or "")
                    if val:
                        secret_result = self._engine.scan_text(val, f"{source}.{node_id}.{field_key}")
                        violations.extend(secret_result.violations)

        if violations and any(v.severity in (Severity.CRITICAL, Severity.HIGH) for v in violations):
            raise ValueError(
                f"!!! [AI SAFE2 LF.FLOW] [CRITICAL] "
                f"Flow JSON '{filename}' BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=not violations, violations=violations, source=source)

    # ── LF-INST ──────────────────────────────────────────────

    def scan_agent_instructions(
        self,
        system_prompt: str,
        flow_id:       str = "unknown",
    ) -> ScanResult:
        """
        Scan agent system_prompt BEFORE saving to flow JSON.

        Why it matters: The system_prompt is saved in the flow JSON and applied
        to EVERY user's session for every future run of that flow. Poisoning it
        once affects all future invocations permanently until manually changed.

        Controls: P1.T1.2, P1.T1.10, S1.3, S1.5
        """
        source     = f"agent_instructions[{flow_id}]"
        violations: List[Violation] = []

        base_result = self._engine.scan_text(system_prompt, source)
        violations.extend(base_result.violations)

        for pattern, surface_id in _INST_PATTERNS:
            if re.search(pattern, system_prompt):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Malicious instruction in system_prompt for flow "
                        f"'{flow_id}'. Affects ALL future sessions permanently."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.INST] [CRITICAL] "
                f"Agent instructions for flow '{flow_id}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LF-COMP ──────────────────────────────────────────────

    def scan_component_output(
        self,
        output:          Any,
        component_name:  str = "component",
        position:        int = 0,
    ) -> ScanResult:
        """
        Scan DAG component output BEFORE it passes to the next component.

        Why it matters: A URL fetcher or file reader early in the DAG can
        inject content that reaches an Agent node several hops downstream.
        The injection travels through Parser, Prompt Template, and Memory
        nodes with no native gate between them.

        Deploy as the safe2_guardian_component.py inline DAG node
        (see langflow-component/) to intercept outputs within the DAG.

        Controls: P1.T1.10, P1.T1.5, S1.3
        """
        source     = f"component_output[{component_name}@{position}]"
        output_str = " ".join(self._extract_strings(output))
        violations: List[Violation] = []

        self._dag_hops += 1

        base_result = self._engine.scan_text(output_str, source)
        violations.extend(base_result.violations)

        for pattern, surface_id in _COMP_OUTPUT_PATTERNS:
            if re.search(pattern, output_str):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Injection in output of '{component_name}' "
                        f"(DAG position {position}, hop {self._dag_hops}). "
                        f"Will propagate to downstream Agent node."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LF.COMP] [CRITICAL] "
                f"Component output from '{component_name}' BLOCKED — "
                f"{len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── Helpers ───────────────────────────────────────────────

    def _extract_strings(self, obj: Any, depth: int = 0) -> List[str]:
        """Recursively extract all string values from nested structures."""
        if depth > 10:
            return []
        results = []
        if isinstance(obj, str):
            results.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                results.extend(self._extract_strings(v, depth + 1))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                results.extend(self._extract_strings(item, depth + 1))
        elif obj is not None:
            results.append(str(obj))
        return results

    def reset_dag_state(self) -> None:
        """Reset DAG hop counter at flow run boundary."""
        self._dag_hops = 0

    def get_status(self) -> Dict[str, Any]:
        status = self._engine.get_status()
        status["dag_hops"] = self._dag_hops
        return status

    def compliance_report(self) -> str:
        return self._engine.compliance_report("langflow-sovereign-runtime")
