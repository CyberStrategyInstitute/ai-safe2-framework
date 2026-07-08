"""
sovereign_cursor.py — Cursor Enforcement Layer
AI SAFE2 v3.0 Sovereign Runtime
Cyber Strategy Institute

Eight enforcement surfaces covering 11+ published Cursor CVEs (2025-2026):

  CU-RULES   .cursor/rules/*.mdc inject into EVERY context window automatically
             Invisible Unicode IPI demonstrated by Pillar Security (CVE-class)
  CU-MCP     .cursor/mcp.json write attack → immediate RCE
             CurXecute / CVE-2025-54135 (CVSS 8.6)
  CU-TRUST   Approve-once MCP trust bound to key name, not command body
             MCPoison / CVE-2025-54136 (CVSS 7.2) + TrustFall (unpatched May 2026)
  CU-REPO    Repository file IPI → .git/config write → sandbox escape
             CVE-2026-26268 (CVSS 9.9) + NomShub kill chain
  CU-CMD     Shell builtin / command injection
             CVE-2026-22708: builtins invisible to Auto-Run parser
  CU-IGNORE  .cursorignore bypass → credential read
             CVE-2025-64110 (CVSS 8.7)
  CU-CLOUD   Background cloud agent clones repo and operates independently
             Separate enforcement layer from local IDE
  CU-SUPPLY  MCP installer spoofing / OpenVSX namespace squatting
             CVE-2025-64106 (CVSS 8.8)

Source verification:
  repello.ai/blog/cursor-security (May 2026)    → full CVE register
  howtoharden.com/guides/cursor/                → CU-RULES (Pillar Security demo)
  truefoundry.com/blog/cursor-security          → MCPoison / CurXecute detail
  cursor.com/docs/agent/security                → Run Mode, MCP approval flow

Usage:
  from enforcement.sovereign_cursor import CursorSovereignRuntime

  guard = CursorSovereignRuntime(
      allowed_mcp_servers=["github-mcp", "notion-mcp"],
      shell_command_allowlist=["git status", "npm test"],
      require_version="2.5",
  )

  # Before committing any .mdc rules file:
  guard.scan_rules_file(content, ".cursor/rules/coding-standards.mdc")

  # Before writing .cursor/mcp.json:
  guard.scan_mcp_json(content, ".cursor/mcp.json")

  # Before trusting a new MCP server registration:
  guard.scan_mcp_server_registration("my-server", "npx my-mcp-server")

  # Before processing any repo file in agent context:
  guard.scan_repo_file(content, "README.md")

  # Before executing any terminal command:
  guard.scan_shell_command("git status", context="agent")

  # Before writing/reading .cursorignore:
  guard.scan_cursorignore(content)

  # Before dispatching a cloud agent task:
  guard.scan_cloud_agent_task(task_prompt, repo_url)

  # Before installing any MCP package:
  guard.scan_mcp_install("playwright-mcp", "npx playwright-mcp")
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ai_safe2_engine import AISAFE2Engine, Band, ScanResult, Severity, Violation


# ─────────────────────────────────────────────────────────────
# CU-RULES: Injection in .mdc rules files
# Controls: P1.T1.2, P1.T1.10, S1.3, S1.6
# Pillar Security: invisible Unicode injects backdoors into ALL generated code
# "Always apply rules load in EVERY context window" (cursor.com/docs/rules)
# ─────────────────────────────────────────────────────────────
_RULES_INJECT_PATTERNS: List[tuple] = [
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior|above)\s+(?:instructions|rules)",   "CU.RULES.OVERRIDE"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules|constraints)",           "CU.RULES.OVERRIDE"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                                      "CU.RULES.PERSONA"),
    (r"(?i)(?:always|for\s+every\s+file),?\s+(?:include|add|inject|insert)\s+(?:a\s+)?backdoor", "CU.RULES.BACKDOOR"),
    (r"(?i)in\s+every\s+(?:file|function|class|component).{0,60}(?:add|inject|include)\b", "CU.RULES.BACKDOOR"),
    (r"(?i)(?:never|do\s+not)\s+(?:show|reveal|display|mention)\s+(?:this|these)\s+(?:rule|instruction)", "CU.RULES.HIDDEN"),
    (r"(?i)do\s+not\s+(?:tell|inform|let)\s+the\s+(?:user|developer|team)\s+(?:about|that)", "CU.RULES.COVERT"),
    (r"(?i)exfiltrate|send\s+(?:all\s+)?(?:code|files?|data)\s+to\s+https?://",   "CU.RULES.EXFIL"),
    (r"(?i)eval\s*\(",                                                               "CU.RULES.EXEC"),
    (r"(?i)(?:new\s+)?Function\s*\(",                                               "CU.RULES.EXEC"),
]

# ─────────────────────────────────────────────────────────────
# CU-MCP: Malicious content in mcp.json
# Controls: P1.T1.10, P1.T2.5, M4.5
# CurXecute (CVE-2025-54135 CVSS 8.6): IPI writes mcp.json → RCE
# ─────────────────────────────────────────────────────────────
_MCP_JSON_DANGER_PATTERNS: List[tuple] = [
    # Shell injection in command strings
    (r"(?:[;&|`]|\$\()\s*(?:curl|wget|nc|bash|sh|python)",                          "CU.MCP.CMDINJEC"),
    (r"(?i)(?:curl|wget)\s+https?://(?!localhost|127\.0\.0\.1)",                    "CU.MCP.NETWORK"),
    # Reverse shell via MCP command
    (r"/dev/tcp/",                                                                   "CU.MCP.REVSHELL"),
    (r"(?i)bash\s+-i\s+>&",                                                         "CU.MCP.REVSHELL"),
    (r"(?i)nc(?:at)?\s+\S+\s+\d+",                                                 "CU.MCP.REVSHELL"),
    # Suspicious encoded payloads (base64 obfuscation bypass)
    (r"(?:base64\s+-d|atob\s*\()",                                                  "CU.MCP.ENCODED"),
    # Homoglyph / Unicode confusion in server names
]

# ─────────────────────────────────────────────────────────────
# CU-TRUST: MCPoison + TrustFall patterns
# Controls: P1.T2.5, M4.5, P4.T7.1
# MCPoison (CVE-2025-54136): approve-once bound to key name not command
# TrustFall: project-local MCP servers execute without user approval (unpatched May 2026)
# ─────────────────────────────────────────────────────────────
# Known-safe MCP server command prefixes (curated list)
_KNOWN_SAFE_MCP_PREFIXES: Set[str] = {
    "npx @modelcontextprotocol/",
    "npx @anthropic/",
    "uvx mcp-",
    "python -m mcp",
    "node /path/to/",
}

# ─────────────────────────────────────────────────────────────
# CU-REPO: Dangerous content in repository files
# Controls: P1.T1.2, P1.T1.10, S1.3
# CVE-2026-26268 (CVSS 9.9): .git/config write → out-of-sandbox execution
# NomShub: README IPI → .zshenv overwrite → persistent tunnel
# ─────────────────────────────────────────────────────────────
_REPO_IPI_PATTERNS: List[tuple] = [
    # Standard override patterns
    (r"(?i)ignore\s+(all\s+)?(?:previous|prior)\s+instructions",                   "CU.REPO.OVERRIDE"),
    (r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[INST\]",                                      "CU.REPO.TEMPLATE"),
    # Git-specific attack patterns (CVE-2026-26268 class)
    (r"(?i)(?:write|overwrite|modify|edit|update)\s+[`'\"]?\.git(?:/config|hooks)", "CU.REPO.GIT_WRITE"),
    (r"(?i)git\s+config\s+--(?:global|system)\s+core\.hooksPath",                 "CU.REPO.GIT_HOOK"),
    (r"(?i)(?:append|write|add)\s+.*(?:\.zshenv|\.bashrc|\.bash_profile|\.profile)","CU.REPO.SHELLRC"),
    # Tunnel persistence (NomShub step 4)
    (r"(?i)(?:ssh\s+-R|autossh|ngrok|bore\s+local|frpc)\s+",                      "CU.REPO.TUNNEL"),
    # Code execution trigger
    (r"(?i)after\s+(?:cloning|running|building|installing),?\s+(?:run|execute)\s+", "CU.REPO.AUTORUN"),
]

# ─────────────────────────────────────────────────────────────
# CU-CMD: Shell command / builtin injection
# Controls: P1.T2.1, M4.5, F3.2
# CVE-2026-22708: shell builtins invisible to Auto-Run parser
# ─────────────────────────────────────────────────────────────
_SHELL_BUILTIN_DANGER: List[tuple] = [
    # Env var poisoning via export (CVE-2026-22708)
    (r"(?i)\bexport\s+(?:PATH|LD_PRELOAD|PYTHONPATH|NODE_PATH|HOME|SHELL)\s*=", "CU.CMD.ENVPOISON"),
    (r"(?i)\bunset\s+(?:PATH|LD_PRELOAD|PYTHONPATH)",                            "CU.CMD.ENVPOISON"),
    # Destructive builtins
    (r"(?i):\s*\(\s*\)\s*\{.*:.*\|.*\}.*:",                                     "CU.CMD.FORKBOMB"),
    (r"(?i)\beval\s+['\"`\$\(]",                                                 "CU.CMD.EVAL"),
    (r"(?i)\bsource\s+https?://",                                                "CU.CMD.REMOTE_SOURCE"),
    # Shell RC overwrite (NomShub persistence)
    (r"(?i)(?:>|>>)\s*~?/?\.[a-z]*(?:rc|env|profile|login)\b",                  "CU.CMD.SHELLRC_WRITE"),
    # Network exfil builtins
    (r"(?i)\bexport\b.*\|\s*(?:nc|curl|wget|bash)\b",                           "CU.CMD.EXFIL"),
    # Sandbox escape attempts
    (r"(?i)\bchroot\b|\bnsenter\b|\bunshare\b",                                  "CU.CMD.SANDBOX_ESC"),
    # rm -rf variants
    (r"(?i)\brm\s+-[rf]{1,2}\s+(?:/|\*|~)",                                     "CU.CMD.DESTRUCT"),
]

# ─────────────────────────────────────────────────────────────
# CU-IGNORE: .cursorignore bypass patterns
# Controls: P1.T1.10, P1.T2.6, S1.5
# CVE-2025-64110 (CVSS 8.7): agent creates config files to bypass cursorignore
# ─────────────────────────────────────────────────────────────
_CURSORIGNORE_BYPASS_PATTERNS: List[tuple] = [
    # Negating existing ignore rules
    (r"^!\s*\.env",                                                               "CU.IGNORE.NEGATE_ENV"),
    (r"^!\s*\*\*?/?\*\.(?:pem|key|p12|pfx|cert|crt)",                          "CU.IGNORE.NEGATE_CERTS"),
    (r"^!\s*(?:id_rsa|id_ed25519|\.aws|credentials|service_account)",           "CU.IGNORE.NEGATE_CREDS"),
    # Wildcard that would expose everything
    (r"^!\s*\*$",                                                                "CU.IGNORE.NEGATE_ALL"),
    # Case-sensitivity bypass (CVE-2025-59944 class)
    (r"(?i)^!\s*\.ENV\b",                                                        "CU.IGNORE.CASE_BYPASS"),
]

# ─────────────────────────────────────────────────────────────
# Sensitive files that should always be in .cursorignore
# ─────────────────────────────────────────────────────────────
_REQUIRED_IGNORED_PATTERNS: List[str] = [
    ".env", "*.pem", "*.key", "id_rsa", ".aws/credentials",
    "service_account.json", "credentials.json",
]

# ─────────────────────────────────────────────────────────────
# CU-SUPPLY: MCP supply chain patterns
# Controls: P1.T1.9, P1.T2.5
# CVE-2025-64106 (CVSS 8.8): MCP installer spoofing
# OpenVSX namespace squatting
# ─────────────────────────────────────────────────────────────
_SUPPLY_CHAIN_PATTERNS: List[tuple] = [
    # Version pinning absent (supply chain risk)
    (r"npx\s+(?!.*@\d)",                                                         "CU.SUPPLY.UNPINNED"),
    # Suspicious package names (typosquatting patterns)
    (r"npx\s+(?:cursor-mcp|cursor\.mcp|curser-|c0rsor)",                        "CU.SUPPLY.TYPOSQUAT"),
    # HTTP (non-HTTPS) MCP server URL
    (r'"url"\s*:\s*"http://(?!localhost|127\.0\.0\.1)',                          "CU.SUPPLY.HTTP_MCP"),
    # Executable from /tmp or world-writable paths
    (r'(?:command|cmd)\s*[=:]\s*["\']?/tmp/',                                   "CU.SUPPLY.TMPEXEC"),
    (r'(?:command|cmd)\s*[=:]\s*["\']?/dev/shm/',                               "CU.SUPPLY.TMPEXEC"),
]


# ─────────────────────────────────────────────────────────────
# Main Runtime Class
# ─────────────────────────────────────────────────────────────

class CursorSovereignRuntime:
    """
    AI SAFE2 v3.0 Sovereign Runtime for Cursor.

    Cursor has the highest CVE count of any platform in this series:
    11+ documented in 2025-2026, covering 4 architectural attack patterns.
    This class enforces at all 8 unique surfaces, including the cloud
    background agent layer that operates independently of the local IDE.
    """

    DEFAULT_SHELL_ALLOWLIST = [
        "git status", "git log", "git diff", "git add", "git commit",
        "npm test", "npm run", "npm install",
        "python -m pytest", "python -m flake8", "python -m mypy",
        "cargo test", "cargo build", "go test",
        "ls", "ls -la", "pwd", "cat", "echo", "which",
    ]

    def __init__(
        self,
        allowed_mcp_servers:      Optional[List[str]] = None,
        shell_command_allowlist:  Optional[List[str]] = None,
        require_version:          Optional[str]       = "2.5",  # minimum safe version
        require_mcp_hitl:         bool                = True,
        audit_log_path:           Optional[Path]      = None,
        session_id:               Optional[str]       = None,
    ) -> None:
        self._allowed_servers   = set(allowed_mcp_servers or [])
        self._shell_allowlist   = list(shell_command_allowlist or self.DEFAULT_SHELL_ALLOWLIST)
        self._require_version   = require_version
        self._require_mcp_hitl  = require_mcp_hitl
        self._engine            = AISAFE2Engine(
            session_id=session_id,
            audit_log_path=audit_log_path,
        )
        # Track MCP servers that have been approved (for MCPoison detection)
        self._approved_mcp_servers: Dict[str, str] = {}  # name → command hash

    # ── CU-RULES ─────────────────────────────────────────────

    def scan_rules_file(
        self,
        content:  str,
        filename: str = "rules.mdc",
    ) -> ScanResult:
        """
        Scan a .mdc rules file BEFORE committing to .cursor/rules/.

        Why it matters: Rules in .cursor/rules/*.mdc with 'Always Apply'
        activation inject into EVERY Cursor context window — every chat,
        every autocomplete, every agent task. One poisoned rule file
        = workspace-wide IPI affecting every developer on the team.

        Pillar Security demonstrated: invisible Unicode in .cursorrules
        silently instructs the AI to inject backdoors into ALL generated code.
        The Unicode is invisible in code editors and GitHub diffs.

        Controls: P1.T1.2, P1.T1.10, P1.T1.4_ADV, S1.3, S1.6
        """
        source     = f"rules_file[{filename}]"
        violations: List[Violation] = []

        # Engine-level: injection + secrets + hidden Unicode
        base_result = self._engine.scan_text(content, source)
        violations.extend(base_result.violations)

        # Rules-specific injection patterns
        for pattern, surface_id in _RULES_INJECT_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Malicious instruction in rules file '{filename}'. "
                        f"This file injects into every team member's context window."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.RULES] [CRITICAL] "
                f"Rules file '{filename}' BLOCKED — {len(violations)} violation(s). "
                f"Do NOT commit to .cursor/rules/."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-MCP ───────────────────────────────────────────────

    def scan_mcp_json(
        self,
        content:  str,
        filepath: str = ".cursor/mcp.json",
    ) -> ScanResult:
        """
        Scan .cursor/mcp.json content BEFORE writing.

        Why it matters (CurXecute / CVE-2025-54135, CVSS 8.6):
        IPI in a Slack message or repository file instructs the agent to
        write a malicious entry to .cursor/mcp.json. Older Cursor versions
        execute the new MCP command immediately without re-approval.
        Any shell injection in the command field = RCE under dev privileges.

        Controls: P1.T1.10, P1.T2.5, M4.5
        """
        source     = f"mcp_json[{filepath}]"
        violations: List[Violation] = []

        # Parse JSON if possible
        try:
            config = json.loads(content)
            servers = config.get("mcpServers", {})

            for server_name, server_config in servers.items():
                command = server_config.get("command", "") or ""
                url     = server_config.get("url", "") or ""
                args    = server_config.get("args", [])
                full_cmd = f"{command} {' '.join(str(a) for a in args)}"

                # Check command for injection
                for pattern, surface_id in _MCP_JSON_DANGER_PATTERNS:
                    if re.search(pattern, full_cmd) or re.search(pattern, url):
                        v = Violation(
                            control_id="P1.T2.5",
                            severity=Severity.CRITICAL,
                            message=(
                                f"[{surface_id}] Dangerous pattern in MCP server "
                                f"'{server_name}' command: '{full_cmd[:60]}'. "
                                f"CurXecute: IPI-written mcp.json → RCE."
                            ),
                            source=source,
                        )
                        violations.append(v)
                        self._engine._record(v)
                        break

                # Check server allowlist
                if self._allowed_servers and server_name not in self._allowed_servers:
                    v = Violation(
                        control_id="M4.5",
                        severity=Severity.HIGH,
                        message=(
                            f"MCP server '{server_name}' not in allowlist. "
                            f"Configure allowed_mcp_servers to authorize."
                        ),
                        source=source,
                    )
                    violations.append(v)
                    self._engine._record(v)

        except (json.JSONDecodeError, AttributeError):
            # Non-JSON content in mcp.json = suspicious
            # Fall back to pattern scanning on raw content
            for pattern, surface_id in _MCP_JSON_DANGER_PATTERNS:
                if re.search(pattern, content):
                    v = Violation(
                        control_id="P1.T1.10",
                        severity=Severity.CRITICAL,
                        message=f"[{surface_id}] Invalid JSON + dangerous pattern in '{filepath}'",
                        source=source,
                    )
                    violations.append(v)
                    self._engine._record(v)
                    break

        # Also check supply chain patterns
        for pattern, surface_id in _SUPPLY_CHAIN_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.9",
                    severity=Severity.HIGH,
                    message=f"[{surface_id}] Supply chain risk in '{filepath}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.MCP] [CRITICAL] "
                f"'{filepath}' BLOCKED — {len(violations)} violation(s). "
                f"CurXecute kill chain interrupted."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-TRUST ─────────────────────────────────────────────

    def scan_mcp_server_registration(
        self,
        name:    str,
        command: str,
        url:     Optional[str] = None,
    ) -> ScanResult:
        """
        Validate MCP server before approving registration.

        Why it matters (MCPoison / CVE-2025-54136, CVSS 7.2 + TrustFall unpatched):
        MCPoison: approve-once trust is bound to the KEY NAME, not the command
        body. Attacker registers a benign server, gets approval, then swaps
        the command — executes silently on every IDE launch.
        TrustFall: project-local MCP servers in .cursor/mcp.json execute
        without a separate user approval prompt (unpatched as of May 2026).

        Controls: P1.T2.5, M4.5, P4.T7.1
        """
        source     = f"mcp_registration[{name}]"
        violations: List[Violation] = []

        # MCPoison detection: has this server name been approved with a different command?
        import hashlib
        cmd_hash = hashlib.sha256(command.encode()).hexdigest()
        if name in self._approved_mcp_servers:
            if self._approved_mcp_servers[name] != cmd_hash:
                v = Violation(
                    control_id="M4.5",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[MCPoison] MCP server '{name}' command changed since approval. "
                        f"MCPoison pattern: benign approval → malicious command swap. "
                        f"Re-approve explicitly."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)

        # Danger patterns in command
        for pattern, surface_id in _MCP_JSON_DANGER_PATTERNS:
            if re.search(pattern, command):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=f"[{surface_id}] Dangerous pattern in MCP command: '{command[:60]}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Supply chain: require version pinning for npx
        for pattern, surface_id in _SUPPLY_CHAIN_PATTERNS:
            if re.search(pattern, command):
                v = Violation(
                    control_id="P1.T1.9",
                    severity=Severity.HIGH,
                    message=f"[{surface_id}] Supply chain risk in MCP command: '{command[:60]}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Server allowlist
        if self._allowed_servers and name not in self._allowed_servers:
            v = Violation(
                control_id="M4.5",
                severity=Severity.HIGH,
                message=f"MCP server '{name}' not in allowed_mcp_servers list",
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.TRUST] [CRITICAL] "
                f"MCP server '{name}' BLOCKED — {len(violations)} violation(s). "
                f"MCPoison/TrustFall kill chain interrupted."
            )

        # Record approved command hash (for future MCPoison detection)
        self._approved_mcp_servers[name] = cmd_hash
        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-REPO ──────────────────────────────────────────────

    def scan_repo_file(
        self,
        content:  str,
        filepath: str = "README.md",
    ) -> ScanResult:
        """
        Scan repository file content BEFORE processing in agent context.

        Why it matters (CVE-2026-26268 CVSS 9.9 + NomShub):
        CVE-2026-26268: sandboxed agent writes .git/config or git hooks;
        these execute out-of-sandbox on the next git operation.
        NomShub: README IPI → sandbox escape via builtins →
        .zshenv overwrite → reverse tunnel → persistent devbox access.

        Controls: P1.T1.2, P1.T1.10, S1.3
        """
        source     = f"repo_file[{filepath}]"
        violations: List[Violation] = []

        # Engine scan
        base_result = self._engine.scan_text(content, source)
        violations.extend(base_result.violations)

        # Repo-specific patterns
        for pattern, surface_id in _REPO_IPI_PATTERNS:
            if re.search(pattern, content):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Injection/dangerous pattern in repo file '{filepath}'. "
                        f"CVE-2026-26268: .git/config writes escape the sandbox."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.REPO] [CRITICAL] "
                f"Repo file '{filepath}' BLOCKED — {len(violations)} violation(s). "
                f"NomShub/CVE-2026-26268 kill chain interrupted."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-CMD ───────────────────────────────────────────────

    def scan_shell_command(
        self,
        command: str,
        context: Optional[str] = None,
    ) -> ScanResult:
        """
        Scan shell command BEFORE Auto-Run execution.

        Why it matters (CVE-2026-22708):
        Shell builtins (export, unset, eval) are invisible to Cursor's
        Auto-Run parser — they bypass the tool-call approval mechanism.
        An injected 'export PATH=/tmp/evil:$PATH' poisons the env
        silently before any tool call is logged.

        Controls: P1.T2.1, M4.5, F3.2
        """
        source     = f"shell_command[{context or 'agent'}]"
        violations: List[Violation] = []

        # Allowlist-first
        cmd_stripped = command.strip()
        on_allowlist = any(
            cmd_stripped.startswith(a.strip())
            for a in self._shell_allowlist
        )

        if not on_allowlist:
            for pattern, surface_id in _SHELL_BUILTIN_DANGER:
                if re.search(pattern, command):
                    v = Violation(
                        control_id="P1.T2.1",
                        severity=Severity.CRITICAL,
                        message=(
                            f"[{surface_id}] Dangerous shell pattern: '{command[:80]}'. "
                            f"CVE-2026-22708: builtins bypass Auto-Run parser."
                        ),
                        source=source,
                    )
                    violations.append(v)
                    self._engine._record(v)
                    break

        # Secret check even for allowlisted commands (P1.T1.4_ADV)
        secret_result = self._engine.scan_text(command, source)
        violations.extend(secret_result.violations)

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.CMD] [CRITICAL] "
                f"Shell command BLOCKED: '{command[:60]}'"
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-IGNORE ────────────────────────────────────────────

    def scan_cursorignore(
        self,
        content:  str,
        filepath: str = ".cursorignore",
    ) -> ScanResult:
        """
        Scan .cursorignore content for bypass patterns.

        Why it matters (CVE-2025-64110, CVSS 8.7):
        An agent can create new config files that invalidate existing
        ignore rules. The negation pattern '!.env' un-ignores a previously
        protected file, exposing credentials and API keys that should have
        been invisible to Cursor's codebase indexing.

        Controls: P1.T1.10, P1.T2.6, S1.5
        """
        source     = f"cursorignore[{filepath}]"
        violations: List[Violation] = []

        for pattern, surface_id in _CURSORIGNORE_BYPASS_PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                v = Violation(
                    control_id="P1.T2.6",
                    severity=Severity.HIGH,
                    message=(
                        f"[{surface_id}] Bypass pattern in '{filepath}'. "
                        f"CVE-2025-64110: negation of sensitive file ignores → credential exposure."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Audit: check required sensitive files are listed
        missing = []
        for required in _REQUIRED_IGNORED_PATTERNS:
            # Check if the pattern (or something that would match it) is present
            if required not in content and f"**/{required}" not in content:
                missing.append(required)

        if len(missing) > len(_REQUIRED_IGNORED_PATTERNS) // 2:
            # More than half missing = flag (not hard block, just violation)
            v = Violation(
                control_id="S1.5",
                severity=Severity.MEDIUM,
                message=(
                    f".cursorignore is missing recommended sensitive file patterns: "
                    f"{missing[:3]}{'...' if len(missing) > 3 else ''}. "
                    f"Add these to prevent credential exposure via codebase indexing."
                ),
                source=source,
            )
            violations.append(v)
            self._engine._record(v)

        if violations and any(v.severity == Severity.HIGH for v in violations):
            raise ValueError(
                f"!!! [AI SAFE2 CU.IGNORE] [HIGH] "
                f"'{filepath}' BLOCKED — bypass pattern detected."
            )

        return ScanResult(passed=not violations, violations=violations, source=source)

    # ── CU-CLOUD ─────────────────────────────────────────────

    def scan_cloud_agent_task(
        self,
        task_prompt: str,
        repo_url:    Optional[str] = None,
        branch:      Optional[str] = None,
    ) -> ScanResult:
        """
        Validate cloud background agent task BEFORE dispatch.

        Why it matters: Cursor background agents clone repos into cloud VMs
        and operate independently. They have their own context window,
        their own MCP connections, and their own shell access. An injection
        in the task prompt or the cloned repo propagates to the cloud VM,
        which has no local IDE safeguards.

        Controls: P1.T1.2, P1.T1.10, S1.3, CP.9
        """
        source     = f"cloud_agent[{repo_url or 'unknown'}]"
        violations: List[Violation] = []

        # Scan task prompt
        prompt_result = self._engine.scan_text(task_prompt, f"{source}.prompt")
        violations.extend(prompt_result.violations)

        # Repo-level patterns in prompt
        for pattern, surface_id in _REPO_IPI_PATTERNS:
            if re.search(pattern, task_prompt):
                v = Violation(
                    control_id="P1.T1.10",
                    severity=Severity.CRITICAL,
                    message=(
                        f"[{surface_id}] Injection in cloud agent task for '{repo_url}'. "
                        f"Cloud VM operates independently — no local IDE safeguards."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # CP.9: cloud agent is a spawned sub-agent
        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.CLOUD] [CRITICAL] "
                f"Cloud agent task BLOCKED — {len(violations)} violation(s). "
                f"CP.9: spawned sub-agent requires clean context."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── CU-SUPPLY ────────────────────────────────────────────

    def scan_mcp_install(
        self,
        package_name: str,
        install_cmd:  str,
    ) -> ScanResult:
        """
        Validate MCP package BEFORE installation.

        Why it matters (CVE-2025-64106, CVSS 8.8 + OpenVSX squatting):
        MCP install dialog can be spoofed — appears as Playwright while
        executing attacker commands. OpenVSX namespace squatting lets
        attackers publish packages under legitimate-looking names.
        Unpinned 'npx mcp-server@latest' is a supply chain attack vector.

        Controls: P1.T1.9, P1.T2.5
        """
        source     = f"mcp_install[{package_name}]"
        violations: List[Violation] = []

        for pattern, surface_id in _SUPPLY_CHAIN_PATTERNS:
            if re.search(pattern, install_cmd) or re.search(pattern, package_name):
                v = Violation(
                    control_id="P1.T1.9",
                    severity=Severity.HIGH,
                    message=(
                        f"[{surface_id}] Supply chain risk in MCP install: "
                        f"'{install_cmd[:60]}'. "
                        f"CVE-2025-64106: MCP install dialog spoofing."
                    ),
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        # Danger patterns in install command
        for pattern, surface_id in _MCP_JSON_DANGER_PATTERNS:
            if re.search(pattern, install_cmd):
                v = Violation(
                    control_id="P1.T2.5",
                    severity=Severity.CRITICAL,
                    message=f"[{surface_id}] Shell injection in MCP install: '{install_cmd[:60]}'",
                    source=source,
                )
                violations.append(v)
                self._engine._record(v)
                break

        if violations:
            raise ValueError(
                f"!!! [AI SAFE2 CU.SUPPLY] [HIGH] "
                f"MCP install '{package_name}' BLOCKED — {len(violations)} violation(s)."
            )

        return ScanResult(passed=True, violations=[], source=source)

    # ── Status / reporting ────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        status = self._engine.get_status()
        status["approved_mcp_servers"] = list(self._approved_mcp_servers.keys())
        return status

    def compliance_report(self) -> str:
        return self._engine.compliance_report("cursor-sovereign-runtime")
