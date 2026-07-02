"""
sovereign_xai_grok.py — xAI/Grok Enforcement Layer
AI SAFE2 v3.0 Sovereign Runtime
Cyber Strategy Institute

Six unique enforcement surfaces not found in other runtimes:

  GK-SKILL   Skill .md injected into every session context (P1.T1.10, S1.3)
  GK-HOOK    Hook receives GROK_HOOK_EVENT — silent exfil vector (P1.T1.10, M4.5)
  GK-PERM    always-approve disables all HITL org-wide (CP.10, P3.T5.2)
  GK-SAND    Sandbox profile downgrade → off (P1.T2.1, F3.2)
  GK-MULTI   Leader prompt fans to 16 sub-agents (S1.3, F3.2, CP.9)
  GK-HEAD    --always-approve in CI = zero oversight (CP.10, F3.2)

Usage:
  from enforcement.sovereign_xai_grok import GrokSovereignRuntime

  guard = GrokSovereignRuntime(
      required_sandbox_profile="workspace",
      max_agent_count=4,
      max_turns=50,
  )

  # Before installing any skill:
  guard.scan_skill_file(Path(".grok/skills/myskill/SKILL.md").read_text(), "SKILL.md")

  # Before installing any hook:
  guard.scan_hook_script(Path(".grok/hooks/pre-tool.sh").read_text(), event="before_tool_use")

  # Before writing any config:
  guard.scan_config(Path("~/.grok/config.toml").read_text())

  # Before any sandbox.toml commit:
  guard.scan_sandbox_profile("workspace")

  # Before multi-agent API call:
  guard.scan_multi_agent_request(prompt, ["web_search", "x_search"], agent_count=4)

  # In CI wrapper (not --always-approve):
  guard.scan_headless_args(["grok", "-p", prompt, "--permission-mode", "dontAsk", "--sandbox", "strict"])
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_safe2_engine import AISAFE2Engine, Band, ScanResult, Severity, Violation


# ─────────────────────────────────────────────────────────────
# GK-HOOK: Dangerous hook script patterns
# Controls: P1.T1.10, M4.5
# ─────────────────────────────────────────────────────────────
_HOOK_DANGER_PATTERNS: List[tuple] = [
    # Exfiltration of hook event data to external endpoint
    (r"curl\s+\S*\s+.*\$\{?GROK_HOOK_EVENT",                           "GK.HOOK.EXFIL"),
    (r"curl\s+['\"]?https?://(?!localhost|127\.0\.0\.1)\S+['\"]?"
     r".*\$\{?GROK_",                                                  "GK.HOOK.EXFIL"),
    (r"\$\{?GROK_SESSION_ID\}?.*(?:curl|wget|nc|python|python3)",      "GK.HOOK.EXFIL"),
    # Destructive commands
    (r"(?i)\brm\s+-[rf]{1,2}\s+/",                                     "GK.HOOK.DESTRUCT"),
    (r"(?i)\brm\s+-rf\b",                                              "GK.HOOK.DESTRUCT"),
    # Arbitrary code execution in hook body
    (r"(?<!\w)eval\s+['\"`\$\(]",                                       "GK.HOOK.EXEC"),
    (r"(?i)\bexec\s+['\"`\$\(]",                                        "GK.HOOK.EXEC"),
    (r"(?i)(?:wget|curl)\s+\S+\s*\|\s*(?:bash|sh|python)",             "GK.HOOK.EXEC"),
    # Outbound tunnel / reverse shell
    (r"(?i)(?:nc|ncat|netcat)\s+\S+\s+\d{2,5}",                       "GK.HOOK.TUNNEL"),
    (r"(?i)(?:mkfifo|mknod)\s+\S+\s+p\b",                             "GK.HOOK.TUNNEL"),
    (r"/dev/tcp/",                                                       "GK.HOOK.TUNNEL"),
]

# ─────────────────────────────────────────────────────────────
# GK-PERM: Forbidden permission settings outside requirements.toml
# Controls: CP.10, P3.T5.2
# ─────────────────────────────────────────────────────────────
_PERM_VIOLATION_PATTERNS: List[tuple] = [
    (r"(?i)always[_-]?approve\s*=\s*true",                              "GK.PERM.ALWAYS"),
    (r"(?i)permission[_-]?mode\s*=\s*['\"]?always[_-]?approve",       "GK.PERM.ALWAYS"),
    (r"(?i)disable[_-]?bypass[_-]?permissions[_-]?mode\s*=\s*false",  "GK.PERM.BYPASS_ALLOWED"),
    (r"(?i)\byolo\s*=\s*true",                                          "GK.PERM.YOLO"),
    (r"(?i)dangerously[_-]?skip[_-]?permissions\s*=\s*true",          "GK.PERM.SKIP"),
]

# ─────────────────────────────────────────────────────────────
# GK-SAND: Sandbox profile ordering
# off (0) → workspace (1) → devbox (2) → read-only (3) → strict (4)
# Controls: P1.T2.1, F3.2
# ─────────────────────────────────────────────────────────────
_SANDBOX_PROFILES = ["off", "workspace", "devbox", "read-only", "strict"]

# ─────────────────────────────────────────────────────────────
# GK-MULTI: Server-side tools that run with no client sandbox
# Controls: P1.T2.5, S1.3
# ─────────────────────────────────────────────────────────────
_DANGEROUS_TOOLS = frozenset({"code_execution", "computer_use", "bash", "shell"})

# ─────────────────────────────────────────────────────────────
# GK-HEAD: Blocked CLI arguments
# Controls: CP.10, F3.2
# ─────────────────────────────────────────────────────────────
_HEAD_BLOCKED_FLAGS  = frozenset({"--always-approve", "--yolo", "--dangerously-skip-permissions"})
_HEAD_BLOCKED_VALUES = frozenset({"bypassPermissions", "alwaysAllow", "always-approve", "always_approve"})


# ─────────────────────────────────────────────────────────────
# Main Runtime Class
# ─────────────────────────────────────────────────────────────

class GrokSovereignRuntime:
    """
    AI SAFE2 v3.0 Sovereign Runtime for xAI/Grok.

    Wrap every Grok interaction through this class to enforce
    deterministic boundaries the agent cannot see or influence.
    """

    DEFAULT_MIN_PROFILE  = "workspace"
    DEFAULT_MAX_AGENTS   = 4
    DEFAULT_MAX_TURNS    = 50
    DEFAULT_DOW_RATE     = 100   # max operations per session (P3.T5.5 rate limit)

    def __init__(
        self,
        required_sandbox_profile: str = DEFAULT_MIN_PROFILE,
        max_agent_count:          int = DEFAULT_MAX_AGENTS,
        max_turns:                int = DEFAULT_MAX_TURNS,
        max_ops_per_session:      int = DEFAULT_DOW_RATE,
        audit_log_path:           Optional[Path] = None,
        session_id:               Optional[str]  = None,
    ) -> None:
        if required_sandbox_profile not in _SANDBOX_PROFILES:
            raise ValueError(f"Unknown sandbox profile: {required_sandbox_profile}")

        self._min_profile_idx    = _SANDBOX_PROFILES.index(required_sandbox_profile)
        self._max_agent_count    = max_agent_count
        self._max_turns          = max_turns
        self._max_ops            = max_ops_per_session
        self._engine             = AISAFE2Engine(
            session_id=session_id,
            audit_log_path=audit_log_path,
        )
        self._session_active     = False
        self._turn_count         = 0
        self._ops_count          = 0

    # ── Session lifecycle ─────────────────────────────────────

    def start_session(self, session_id: str) -> None:
        """P2.T3.1 + CP.4: Register session as NHI in audit chain."""
        self._session_active = True
        self._turn_count     = 0
        self._ops_count      = 0
        import sys
        print(f"[AI SAFE2] xAI/Grok session started: {session_id}", file=sys.stderr, flush=True)

    def end_session(self) -> None:
        """A2.5: Close session with final compliance report."""
        self._session_active = False
        import sys
        print(f"[AI SAFE2] Session ended.\n{self.compliance_report()}", file=sys.stderr, flush=True)

    # ── GK-SKILL ─────────────────────────────────────────────

    def scan_skill_file(self, content: str, filename: str = "SKILL.md") -> ScanResult:
        """
        Scan a .md skill file BEFORE installing to .grok/skills/.

        Why it matters: skills inject into every future session context.
        One poisoned skill = persistent IPI on every Grok session.

        Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3, S1.6
        """
        source    = f"skill_file[{filename}]"
        result    = self._engine.scan_text(content, source)
        violations = list(result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 P1.T1.10] [CRITICAL] "
                f"Skill '{filename}' BLOCKED — {len(violations)} violation(s). "
                f"Do NOT install to .grok/skills/."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── GK-HOOK ──────────────────────────────────────────────

    def scan_hook_script(
        self,
        script:  str,
        event:   str = "before_tool_use",
        source_path: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan a hook script BEFORE installing to .grok/hooks/.

        Why it matters: hooks receive GROK_HOOK_EVENT, GROK_SESSION_ID,
        and GROK_WORKSPACE_ROOT as env vars and run before/after every
        tool call. A hook that sends $GROK_HOOK_EVENT to curl = silent
        exfiltration of every tool input and output, session-wide.

        Controls: P1.T1.10, M4.5, P1.T1.4_ADV
        """
        source     = source_path or f"hook_script[{event}]"
        violations: List[Violation] = []

        for pattern, surface_id in _HOOK_DANGER_PATTERNS:
            if re.search(pattern, script):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=f"Dangerous pattern [{surface_id}] in '{source}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # Also scan for embedded secrets
        secret_result = self._engine.scan_text(script, source)
        violations.extend(secret_result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 P1.T1.10] [CRITICAL] "
                f"Hook '{event}' BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── GK-PERM ──────────────────────────────────────────────

    def scan_config(
        self,
        config_content: str,
        filename:       str = "config.toml",
    ) -> ScanResult:
        """
        Scan config.toml for always-approve violations.

        Why it matters: permission_mode = "always-approve" in
        ~/.grok/config.toml disables ALL HITL prompts org-wide.
        The ONLY safe location for this setting is
        /etc/grok/requirements.toml (root-owned, tamper-resistant).

        Controls: CP.10, P3.T5.2, P1.T2.5
        """
        source     = f"config[{filename}]"
        violations: List[Violation] = []

        for pattern, surface_id in _PERM_VIOLATION_PATTERNS:
            if re.search(pattern, config_content):
                v = Violation(
                    control_id="CP.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Permission bypass in '{filename}'. "
                        f"This setting must live in /etc/grok/requirements.toml only."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 GK.PERM] [CRITICAL] "
                f"Config '{filename}' BLOCKED — always-approve must be in requirements.toml."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── GK-SAND ──────────────────────────────────────────────

    def scan_sandbox_profile(self, profile: str) -> ScanResult:
        """
        Enforce sandbox profile floor.

        Profile order (most → least permissive):
          off  <  workspace  <  devbox  <  read-only  <  strict

        Custom sandbox.toml that extends "off" drops all write
        restrictions. This method enforces a minimum profile floor.

        Controls: P1.T2.1, F3.2
        """
        source = f"sandbox_profile[{profile}]"

        if profile not in _SANDBOX_PROFILES:
            v = Violation(
                control_id="P1.T2.1",
                severity=Severity.HIGH,
                message=f"Unknown sandbox profile '{profile}'",
                source=source,
            )
            self._engine._record(v)
            raise ValueError(
                f"!!! [AI SAFE2 GK.SAND] Unknown profile '{profile}'. "
                f"Valid: {_SANDBOX_PROFILES}"
            )

        idx     = _SANDBOX_PROFILES.index(profile)
        min_idx = self._min_profile_idx
        if idx < min_idx:
            floor = _SANDBOX_PROFILES[min_idx]
            v = Violation(
                control_id="P1.T2.1",
                severity=Severity.CRITICAL,
                message=f"Sandbox '{profile}' is below minimum floor '{floor}'",
                source=source,
            )
            self._engine._record(v)
            raise ValueError(
                f"!!! [AI SAFE2 GK.SAND] [CRITICAL] "
                f"Profile '{profile}' rejected — minimum is '{floor}'."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── GK-MULTI ─────────────────────────────────────────────

    def scan_multi_agent_request(
        self,
        prompt:      str,
        tool_list:   List[str],
        agent_count: int = 1,
    ) -> ScanResult:
        """
        Validate multi-agent API request before submission.

        Why it matters: grok-4.x-multi-agent runs 4–16 sub-agents
        in parallel. One leader-prompt injection propagates to ALL
        sub-agents simultaneously. The code_execution built-in tool
        runs server-side with no client-controlled sandbox.

        Controls: P1.T1.2, P1.T1.10, S1.3, F3.2, CP.9
        """
        source     = "multi_agent_request"
        violations: List[Violation] = []

        # Scan leader prompt — injection fans to all agents
        prompt_result = self._engine.scan_text(prompt, f"{source}.leader_prompt")
        violations.extend(prompt_result.violations)

        # Block dangerous server-side tools (no client sandbox)
        blocked = [t for t in tool_list if t in _DANGEROUS_TOOLS]
        if blocked:
            v = Violation(
                control_id="P1.T2.5",
                severity=Severity.CRITICAL,
                message=f"Dangerous server-side tool(s): {blocked} — no client sandbox",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Agent count ceiling (CP.9 — agent replication governance)
        if agent_count > self._max_agent_count:
            v = Violation(
                control_id="CP.9",
                severity=Severity.HIGH,
                message=(
                    f"Agent count {agent_count} exceeds ceiling {self._max_agent_count}. "
                    f"CP.9: agent replication requires explicit authorization."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Turn ceiling (F3.2 — recursion limit governor)
        self._turn_count += 1
        if self._turn_count > self._max_turns:
            v = Violation(
                control_id="F3.2",
                severity=Severity.HIGH,
                message=f"Turn ceiling {self._max_turns} exceeded (turn {self._turn_count})",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        # Ops rate (P3.T5.5)
        self._ops_count += 1
        if self._ops_count > self._max_ops:
            v = Violation(
                control_id="P3.T5.5",
                severity=Severity.MEDIUM,
                message=f"Session ops rate {self._max_ops}/session exceeded",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 GK.MULTI] [CRITICAL] "
                f"Multi-agent request BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── GK-HEAD ──────────────────────────────────────────────

    def scan_headless_args(self, args: List[str]) -> ScanResult:
        """
        Validate CLI args before headless/CI execution.

        Why it matters: `grok -p "..." --always-approve` in CI
        = zero HITL, full autonomous tool execution with no
        human approval gate. AI SAFE2 rule: headless CI must use
        --permission-mode dontAsk with explicit --allow rules
        + --sandbox strict.

        Controls: CP.10, P3.T5.2, F3.2, P1.T2.1
        """
        source     = "headless_args"
        violations: List[Violation] = []

        for arg in args:
            # Block explicit bypass flags
            if arg in _HEAD_BLOCKED_FLAGS:
                v = Violation(
                    control_id="CP.10",
                    severity=Severity.CRITICAL,
                    message=f"Headless flag '{arg}' bypasses all HITL — use --permission-mode dontAsk instead",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

            # Block bypass values (e.g. --permission-mode alwaysAllow)
            if arg in _HEAD_BLOCKED_VALUES:
                v = Violation(
                    control_id="CP.10",
                    severity=Severity.CRITICAL,
                    message=f"Headless permission value '{arg}' bypasses HITL",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # Require --sandbox when running in headless mode (-p / --print flag present)
        is_headless = "-p" in args or "--print" in args
        has_sandbox = "--sandbox" in args or any("--sandbox" in a for a in args)

        if is_headless and not has_sandbox:
            v = Violation(
                control_id="P1.T2.1",
                severity=Severity.HIGH,
                message="Headless execution without --sandbox specified",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 GK.HEAD] [CRITICAL] Headless args BLOCKED — "
                f"{len(violations)} violation(s). "
                f"Safe pattern: grok -p '...' --permission-mode dontAsk --sandbox strict"
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── General surface scans ─────────────────────────────────

    def scan_prompt(self, prompt: str) -> ScanResult:
        """P1.T1.2 + P1.T1.10: Interactive session prompt scan."""
        self._turn_count += 1
        return self._engine.scan_text(prompt, "user_prompt")

    def scan_response(self, response: str) -> ScanResult:
        """P1.T1.4_ADV: Agent output secret-leak detection."""
        return self._engine.scan_text(response, "agent_response")

    # ── Status / reporting ────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return self._engine.get_status()

    def compliance_report(self) -> str:
        return self._engine.compliance_report("xai-grok-sovereign-runtime")
