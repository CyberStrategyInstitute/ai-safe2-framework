"""
sovereign_lovable.py — Lovable Enforcement Layer
AI SAFE2 v3.0 Sovereign Runtime
Cyber Strategy Institute

Six enforcement surfaces confirmed against live Lovable documentation:

  LV-KNOW     Workspace/Project knowledge injected into EVERY future agent context
              permanently, workspace-wide (10,000 char persistent attack surface)
  LV-PLAN     Plan approval triggers immediate Agent mode execution — no second confirm
  LV-SQL      query_database MCP tool runs with full DB permissions: read/write/schema
  LV-MCP      Lovable MCP OAuth token scoped to full account, all projects, all credits
  LV-BUILD    Agent writes and deploys production code — eval(), env leaks, hardcoded keys
  LV-SUBAGENT Subagents read ALL project files including .env and private keys

Source verification:
  docs.lovable.dev/features/knowledge          → LV-KNOW
  docs.lovable.dev/features/plan-mode          → LV-PLAN
  docs.lovable.dev/integrations/lovable-mcp-server → LV-SQL, LV-MCP
  docs.lovable.dev/features/agent-mode         → LV-BUILD
  docs.lovable.dev/features/subagents          → LV-SUBAGENT

Usage:
  from enforcement.sovereign_lovable import LovableSovereignRuntime

  guard = LovableSovereignRuntime(
      allowed_mcp_projects=["proj-abc123", "proj-def456"],
      sql_max_result_rows=100,
      require_plan_review=True,
  )

  # Before saving any knowledge content:
  guard.scan_workspace_knowledge(content, scope="workspace")

  # Before approving a plan:
  guard.scan_plan(plan_text, project_id="proj-abc123")

  # Before query_database MCP call:
  guard.scan_sql_query(sql, project_id="proj-abc123")

  # Before connecting MCP client:
  guard.scan_mcp_scope(scopes=["projects:read", "database:write"], project_ids=["proj-abc123"])

  # After Lovable generates code, before deploy:
  guard.scan_generated_code(code_content, filename="src/utils/runner.ts")

  # Before subagent reads file tree:
  guard.scan_subagent_file_access(file_paths)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ai_safe2_engine import AISAFE2Engine, Band, ScanResult, Severity, Violation


# ─────────────────────────────────────────────────────────────
# LV-KNOW: Workspace / project knowledge injection patterns
# Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3, S1.5, S1.6
# ─────────────────────────────────────────────────────────────
_KNOWLEDGE_RESTRICT_PATTERNS: List[tuple] = [
    # Instruction override attempts in knowledge blocks
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior|above)\s+instructions",    "LV.KNOW.INJECT"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                             "LV.KNOW.INJECT"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules|constraints)", "LV.KNOW.INJECT"),
    (r"(?i)(?:forget|override|bypass)\s+(?:your\s+)?instructions",        "LV.KNOW.INJECT"),
    (r"(?i)new\s+(?:system\s+)?instructions?:\s*\n",                       "LV.KNOW.INJECT"),
    (r"(?i)\[OVERRIDE\]|\[SYSTEM\]|\[ADMIN\]",                             "LV.KNOW.INJECT"),
    # Exfil patterns in knowledge
    (r"(?i)always\s+(?:include|send|post|exfiltrate|forward)\s+.*to\s+http", "LV.KNOW.EXFIL"),
    (r"(?i)before\s+every\s+(?:response|message|build),?\s+(?:send|post|call)", "LV.KNOW.EXFIL"),
    # Hidden unicode (S1.6 — invisible to UI, readable by LLM)
]

# ─────────────────────────────────────────────────────────────
# LV-PLAN: Dangerous plan steps
# Controls: P1.T1.2, P1.T1.10, S1.3, P4.T7.1
# ─────────────────────────────────────────────────────────────
_PLAN_DANGER_PATTERNS: List[tuple] = [
    (r"(?i)delete\s+(?:all|every)\s+(?:existing\s+)?(?:user|users|data|database|records|entries)", "LV.PLAN.DESTRUCT"),
    (r"(?i)delete\s+all\s+existing\s+\w+\s+(?:records?|entries?|data)\b",                         "LV.PLAN.DESTRUCT"),
    (r"(?i)remove\s+all\s+(?:existing\s+)?(?:user|data|record)s?\b",                             "LV.PLAN.DESTRUCT"),
    (r"(?i)(?:wipe|purge|clear)\s+(?:all\s+)?(?:existing\s+)?(?:user|data|record)s?\b",          "LV.PLAN.DESTRUCT"),
    (r"(?i)drop\s+(?:the\s+)?(?:database|table|schema)\b",                         "LV.PLAN.DESTRUCT"),
    (r"(?i)(?:truncate|wipe|purge)\s+(?:all\s+)?(?:data|records|tables|users)",   "LV.PLAN.DESTRUCT"),
    (r"(?i)(?:expose|publish|make\s+public)\s+(?:all|every)\s+(?:user|data|api)", "LV.PLAN.EXPOSE"),
    (r"(?i)send\s+(?:all\s+)?(?:user\s+)?(?:data|emails?|pii)\s+to\s+\S+",       "LV.PLAN.EXFIL"),
    (r"(?i)(?:disable|remove|bypass)\s+(?:all\s+)?(?:auth|authentication|security|rls)", "LV.PLAN.BYPASS"),
    (r"(?i)(?:hardcode|embed)\s+(?:the\s+)?(?:api[_\s]?key|secret|password)",    "LV.PLAN.SECRET"),
    (r"(?i)eval\s*\(",                                                              "LV.PLAN.EXEC"),
    (r"(?i)exec\s*\(",                                                              "LV.PLAN.EXEC"),
    (r"(?i)exfiltrate|exfil\b",                                                    "LV.PLAN.EXFIL"),
]

# ─────────────────────────────────────────────────────────────
# LV-SQL: Dangerous SQL patterns
# Confirmed: query_database "runs with your full database permissions.
# Read, write, and schema changes." (Lovable MCP docs)
# Controls: P1.T1.1, P1.T2.5, S1.3
# ─────────────────────────────────────────────────────────────
_SQL_DESTRUCT_PATTERNS: List[tuple] = [
    (r"(?i)\bDROP\s+(?:TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|TRIGGER)\b",  "LV.SQL.DROP"),
    (r"(?i)\bTRUNCATE\s+(?:TABLE\s+)?\w+",                                     "LV.SQL.TRUNC"),
    (r"(?i)\bDELETE\s+FROM\s+\w+(?:\s+WHERE\s+1\s*=\s*1|\s*;|\s*$)",         "LV.SQL.DELETE_ALL"),
    (r"(?i)\bALTER\s+(?:TABLE|DATABASE|SCHEMA)\b",                             "LV.SQL.ALTER"),
    (r"(?i)\bCREATE\s+OR\s+REPLACE\s+(?:FUNCTION|PROCEDURE|TRIGGER)\b",       "LV.SQL.SCHEMA"),
    (r"(?i)\bGRANT\s+.+\s+TO\b",                                               "LV.SQL.PRIVILEGE"),
    (r"(?i)\bREVOKE\s+.+\s+FROM\b",                                            "LV.SQL.PRIVILEGE"),
    # SQL injection signatures
    (r"(?i)(?:'\s*(?:OR|AND)\s*'?\d+'\s*=\s*'?\d+|--\s*$|;\s*DROP|UNION\s+(?:ALL\s+)?SELECT)", "LV.SQL.INJECT"),
    # Disabling RLS (Row Level Security — Supabase default)
    (r"(?i)ALTER\s+TABLE\s+\w+\s+DISABLE\s+ROW\s+LEVEL\s+SECURITY",          "LV.SQL.RLS_BYPASS"),
    (r"(?i)SECURITY\s+DEFINER\b",                                              "LV.SQL.DEFINER"),
]

# ─────────────────────────────────────────────────────────────
# LV-MCP: Dangerous MCP tool calls / scopes
# Confirmed: "scope is your full account, not one project"
# Controls: P1.T2.5, P1.T2.2_ADV, CP.4, M4.5
# ─────────────────────────────────────────────────────────────
_MCP_HIGH_PRIV_SCOPES: Set[str] = {
    "database:write", "database:admin", "database:schema",
    "projects:write", "projects:delete", "workspace:admin",
    "billing:write", "members:write",
}

_MCP_DESTRUCT_TOOLS: Set[str] = {
    "delete_project", "delete_workspace", "delete_member",
    "reset_database", "drop_table",
}

# ─────────────────────────────────────────────────────────────
# LV-BUILD: Dangerous patterns in AI-generated code
# Controls: P1.T1.4_ADV, S1.5, P2.T3.1
# ─────────────────────────────────────────────────────────────
_CODE_DANGER_PATTERNS: List[tuple] = [
    # Arbitrary code execution
    (r"\beval\s*\(",                                                              "LV.BUILD.EVAL"),
    (r"\bFunction\s*\(\s*['\"]",                                                 "LV.BUILD.EVAL"),
    (r"\bnew\s+Function\s*\(",                                                   "LV.BUILD.EVAL"),
    (r"(?i)\bexecSync\s*\(",                                                     "LV.BUILD.EXEC"),
    (r"(?i)\bspawnSync\s*\(",                                                    "LV.BUILD.EXEC"),
    (r"(?i)child_process",                                                        "LV.BUILD.EXEC"),
    # Environment variable exposure
    (r"(?i)console\.log\s*\(\s*process\.env\b",                                  "LV.BUILD.ENVLEAK"),
    (r"(?i)return\s+(?:JSON\.stringify\s*\()?\s*process\.env\b",                 "LV.BUILD.ENVLEAK"),
    (r"(?i)(?:res|Response)\.(?:json|send)\s*\(\s*process\.env\b",              "LV.BUILD.ENVLEAK"),
    # Hardcoded credentials
    (r"(?:sk|xai|pk_live|sk_live)-[A-Za-z0-9_\-]{16,}",                        "LV.BUILD.HARDKEY"),
    (r"(?i)(?:apiKey|api_key|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]", "LV.BUILD.HARDKEY"),
    # Server-side secrets passed to client (React/Next.js pattern)
    (r"NEXT_PUBLIC_[A-Z_]+_(?:SECRET|KEY|PASSWORD|TOKEN)\s*[:=]",               "LV.BUILD.PUBSECRET"),
]

# ─────────────────────────────────────────────────────────────
# LV-SUBAGENT: File paths that should not be read by subagents
# Controls: P1.T1.4_ADV, P1.T2.6, S1.5
# ─────────────────────────────────────────────────────────────
_SUBAGENT_SENSITIVE_PATHS: List[str] = [
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.staging", ".env.secret",
    "id_rsa", "id_ed25519", "id_ecdsa",
    ".pem", ".key", ".p12", ".pfx",
    "service_account.json", "credentials.json",
    ".aws/credentials", ".aws/config",
    "secrets.yaml", "secrets.json",
]


# ─────────────────────────────────────────────────────────────
# Main Runtime Class
# ─────────────────────────────────────────────────────────────

class LovableSovereignRuntime:
    """
    AI SAFE2 v3.0 Sovereign Runtime for Lovable.

    Lovable doesn't just suggest code — it writes, deploys, and executes
    against a live database and production environment on your behalf.
    This class enforces deterministic boundaries that the agent cannot
    see or influence.
    """

    DEFAULT_SQL_MAX_ROWS     = 100
    DEFAULT_MAX_CREDITS      = 50   # P3.T5.5: credits-per-session ceiling
    DEFAULT_KNOW_MAX_CHARS   = 5000  # safe subset of 10k Lovable limit

    def __init__(
        self,
        allowed_mcp_projects:  Optional[List[str]] = None,
        sql_max_result_rows:   int  = DEFAULT_SQL_MAX_ROWS,
        require_plan_review:   bool = True,
        max_credits_per_session: int = DEFAULT_MAX_CREDITS,
        knowledge_max_chars:   int  = DEFAULT_KNOW_MAX_CHARS,
        audit_log_path:        Optional[Path] = None,
        session_id:            Optional[str]  = None,
    ) -> None:
        self._allowed_projects    = set(allowed_mcp_projects or [])
        self._sql_max_rows        = sql_max_result_rows
        self._require_plan_review = require_plan_review
        self._max_credits         = max_credits_per_session
        self._know_max_chars      = knowledge_max_chars
        self._engine              = AISAFE2Engine(
            session_id=session_id,
            audit_log_path=audit_log_path,
        )
        self._credits_used        = 0
        self._builds_deployed     = 0

    # ── LV-KNOW ──────────────────────────────────────────────

    def scan_workspace_knowledge(
        self,
        content: str,
        scope:   str = "workspace",  # "workspace" | "project"
    ) -> ScanResult:
        """
        Scan knowledge content BEFORE saving to workspace or project knowledge.

        Why it matters (confirmed from live docs): knowledge is "always included
        in context" for EVERY future message across ALL projects in the workspace.
        One poisoned workspace knowledge entry = persistent IPI across your entire
        Lovable account until manually removed. Supports up to 10,000 characters —
        10,000 chars of persistent attack surface.

        Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3, S1.5, S1.6
        """
        source     = f"knowledge[{scope}]"
        violations: List[Violation] = []

        # Check char limit (defensive: flag oversized before injection scan)
        if len(content) > self._know_max_chars:
            v = Violation(
                control_id="S1.5",
                severity=Severity.MEDIUM,
                message=(
                    f"Knowledge content {len(content)} chars exceeds "
                    f"safe limit {self._know_max_chars} — review before saving"
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Injection + secrets
        base_result = self._engine.scan_text(content, source)
        violations.extend(base_result.violations)

        # Knowledge-specific injection patterns
        for pattern, surface_id in _KNOWLEDGE_RESTRICT_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Malicious instruction pattern in "
                        f"'{scope}' knowledge. This content will be injected "
                        f"into every future agent context in this workspace."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break  # one event per save

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.KNOW] [CRITICAL] "
                f"Knowledge content BLOCKED — {len(violations)} violation(s). "
                f"Do NOT save to {scope} knowledge."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LV-PLAN ──────────────────────────────────────────────

    def scan_plan(
        self,
        plan_text:  str,
        project_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan a plan BEFORE approving in Plan mode.

        Why it matters (confirmed from live docs): "Plan mode is for
        decision-making. Agent mode is for execution." Approving a plan
        immediately triggers Agent mode — which writes and deploys code
        directly. There is no additional confirmation step.

        Controls: P1.T1.2, P1.T1.10, S1.3, P4.T7.1
        """
        source     = f"plan[{project_id or 'unknown'}]"
        violations: List[Violation] = []

        # Injection scan on full plan
        base_result = self._engine.scan_text(plan_text, source)
        violations.extend(base_result.violations)

        # Plan-specific dangerous step patterns
        for pattern, surface_id in _PLAN_DANGER_PATTERNS:
            if re.search(pattern, plan_text):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Dangerous step in plan for '{project_id}'. "
                        f"Approving will immediately trigger Agent mode execution."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.PLAN] [CRITICAL] "
                f"Plan for '{project_id}' BLOCKED — {len(violations)} violation(s). "
                f"Do NOT approve."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LV-SQL ───────────────────────────────────────────────

    def scan_sql_query(
        self,
        sql:        str,
        project_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan SQL BEFORE submitting to query_database MCP tool.

        Why it matters (confirmed verbatim from Lovable MCP docs):
        query_database "runs SQL with your full database permissions.
        Read, write, and schema changes." No RLS bypass needed —
        this tool runs AS the database owner.

        Controls: P1.T1.1, P1.T1.2, P1.T2.5, S1.3
        """
        source     = f"sql_query[{project_id or 'unknown'}]"
        violations: List[Violation] = []

        for pattern, surface_id in _SQL_DESTRUCT_PATTERNS:
            if re.search(pattern, sql):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Destructive SQL in '{project_id}'. "
                        f"query_database runs with full DB permissions — "
                        f"this would execute as database owner."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # Only one violation event per query but collect all patterns
        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.SQL] [CRITICAL] "
                f"SQL query for '{project_id}' BLOCKED — "
                f"{len(violations)} destructive pattern(s) detected."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LV-MCP ───────────────────────────────────────────────

    def scan_mcp_scope(
        self,
        scopes:      List[str],
        project_ids: Optional[List[str]] = None,
        tool_name:   Optional[str]       = None,
    ) -> ScanResult:
        """
        Validate MCP client scope BEFORE connecting to Lovable MCP server.

        Why it matters (confirmed from live docs): "Scope is your full
        account, not one project. Whatever client you connect can list,
        read, and edit every project you have access to in Lovable.
        Tool calls use real credits and edit real projects."

        Controls: P1.T2.5, P1.T2.2_ADV, CP.4, M4.5
        """
        source     = f"mcp_scope[{tool_name or 'client'}]"
        violations: List[Violation] = []

        # Check for high-privilege scopes
        flagged = [s for s in scopes if s in _MCP_HIGH_PRIV_SCOPES]
        if flagged:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.CRITICAL,
                message=(
                    f"High-privilege MCP scope(s): {flagged}. "
                    f"Lovable MCP tokens are full-account scoped — "
                    f"these permissions apply to ALL projects."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Check for destructive tool calls
        if tool_name and tool_name in _MCP_DESTRUCT_TOOLS:
            v = Violation(
                control_id="M4.5",
                severity=Severity.CRITICAL,
                message=(
                    f"Destructive MCP tool '{tool_name}' blocked. "
                    f"Requires explicit human approval."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Check project allowlist (CP.4: agentic control plane governance)
        if project_ids and self._allowed_projects:
            blocked = [p for p in project_ids if p not in self._allowed_projects]
            if blocked:
                v = Violation(
                    control_id="CP.4",
                    severity=Severity.HIGH,
                    message=(
                        f"MCP access to projects outside allowlist: {blocked}. "
                        f"Configure allowed_mcp_projects to authorize."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.MCP] [CRITICAL] "
                f"MCP scope/tool BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LV-BUILD ─────────────────────────────────────────────

    def scan_generated_code(
        self,
        code:     str,
        filename: str = "generated.ts",
    ) -> ScanResult:
        """
        Scan AI-generated code BEFORE it is deployed to production.

        Why it matters: Lovable Agent mode writes and deploys production
        code autonomously. eval() in a generated utility function, a
        hardcoded API key in a service file, or process.env logged to
        the console — all of these go live immediately on approval.

        Controls: P1.T1.4_ADV, S1.5, P2.T3.1
        """
        source     = f"generated_code[{filename}]"
        violations: List[Violation] = []

        # Secrets in code
        secret_result = self._engine.scan_text(code, source)
        violations.extend(secret_result.violations)

        # Code-specific danger patterns
        for pattern, surface_id in _CODE_DANGER_PATTERNS:
            if re.search(pattern, code):
                v = Violation(
                    control_id="P1.T1.4_ADV",
                    severity=Severity.CRITICAL,
                    message=f"[{surface_id}] Dangerous pattern in generated '{filename}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break  # one event per file

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.BUILD] [CRITICAL] "
                f"Generated code in '{filename}' BLOCKED — "
                f"{len(violations)} violation(s). Do NOT deploy."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── LV-SUBAGENT ──────────────────────────────────────────

    def scan_subagent_file_access(
        self,
        file_paths: List[str],
        project_id: Optional[str] = None,
    ) -> ScanResult:
        """
        Validate file paths BEFORE subagent reads them.

        Why it matters (confirmed from live docs): Subagents can
        "search your project, inspect files" — they read ALL project
        files including .env, private keys, and config files.
        "Subagents report their findings back to the main Lovable agent."
        .env content in a subagent finding = credential exfiltration
        path that bypasses the main agent's normal access patterns.

        Controls: P1.T1.4_ADV, P1.T2.6, S1.5
        """
        source     = f"subagent_file_access[{project_id or 'unknown'}]"
        violations: List[Violation] = []

        for path in file_paths:
            path_lower = path.lower()
            for sensitive in _SUBAGENT_SENSITIVE_PATHS:
                if sensitive.lower() in path_lower or path_lower.endswith(sensitive.lower()):
                    v = Violation(
                        control_id="P1.T2.6",
                        severity=Severity.HIGH,
                        message=(
                            f"Subagent attempting to read sensitive file '{path}'. "
                            f"Subagent findings are passed back to main agent — "
                            f"file contents may be included in responses."
                        ),
                        source=source,
                    )
                    violations.append(v)
                    self._engine._record(v)
                    break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 LV.SUBAGENT] [HIGH] "
                f"Subagent file access BLOCKED — {len(violations)} sensitive file(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── Credit / ops rate (P3.T5.5) ──────────────────────────

    def record_message_sent(self, estimated_credits: float = 1.0) -> None:
        """
        P3.T5.5: Track credit consumption. Raise if session ceiling hit.
        Each Lovable Agent message costs credits and modifies production code.
        """
        self._credits_used += estimated_credits
        if self._credits_used > self._max_credits:
            source = "session_credits"
            v = Violation(
                control_id="P3.T5.5",
                severity=Severity.HIGH,
                message=(
                    f"Session credit ceiling {self._max_credits} exceeded "
                    f"(used: {self._credits_used:.1f}). "
                    f"Review before continuing — each message modifies production code."
                ),
                source=source,
            )
            self._engine._record(v)
            raise ValueError(
                f"!!! [AI SAFE2 LV.CREDIT] [HIGH] "
                f"Credit ceiling exceeded. Pause and review."
            )

    # ── Status / reporting ────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        status = self._engine.get_status()
        status["credits_used"]    = self._credits_used
        status["builds_deployed"] = self._builds_deployed
        return status

    def compliance_report(self) -> str:
        return self._engine.compliance_report("lovable-sovereign-runtime")
