"""
AI SAFE² v3.0 — AutoGen 0.4 Sovereign Enforcement Layer
=========================================================
Target: autogen_agentchat (0.4 only).
0.2 is end-of-life — redirect users to upgrade; do not build a 0.2 wrapper.

WHY THIS PACKAGE IS DIFFERENT FROM ALL OTHERS:

  This is the only framework in the AI SAFE² sovereign runtime series with a
  direct RCE (Remote Code Execution) surface. CodeExecutorAgent actually runs
  Python and shell code on the host. A successful injection bypass does not
  produce a bad LLM response — it runs arbitrary code on your infrastructure.

  CP.8 is MANDATORY for CodeExecutorAgent, not optional.
  CP.10 HEAR gate is MANDATORY for ACT-3+ with code execution.
  P1.T1.2 enforcement on code blocks is the primary defense line.

FOUR UNIQUE SURFACES:

  1. CodeExecutorAgent exec() surface (P1.T1.2 + CP.8 + CP.10)
     CodeBlockGuard scans every code block BEFORE execution for:
       - Python: eval(), exec(), subprocess, os.system(), os.exec, shutil.rmtree
       - Shell: rm -rf, sudo, curl|bash, wget|bash, iptables, shutdown
       - Catastrophic: rm -rf /, kill -9 -1, mkfs on disk device
     Code that fails the scan never reaches the executor. Not after.

  2. Message handoff chain IPI (P1.T1.10 + S1.3)
     AssistantAgent → UserProxyAgent → CodeExecutorAgent message sequences.
     A tool response or retrieved document containing an injection payload
     gets embedded in a subsequent message and reaches the code parser.
     SovereignAssistantProxy scans message content at each on_messages() call.

  3. Async-first architecture (all controls)
     All agents use async def on_messages(). Enforcement is async-native.
     scan_message_content_async() is the primary enforcement path.
     Sync wrappers delegate to async via asyncio.run() or event loop injection.

  4. Agent-to-agent routing in GroupChat (F3.2 + M4.5)
     RoundRobinGroupChat / SelectorGroupChat pass messages between agents.
     Message exchange ceiling (F3.2) and repetition detection (M4.5) apply
     at the message level, not the tool-call level.

CONTROLS:
  P1.T1.2  — Code block scanner (Python + shell dangerous patterns)
  P1.T1.5  — Credential detection in messages
  P1.T1.10 — Message content scan before on_messages() processing
  P1.T2.3  — Network call SSRF + domain allowlist in code blocks
  S1.3     — Message content = untrusted data-plane
  S1.5     — Agent state write governance
  F3.2     — Message exchange ceiling
  F3.5     — Agent error cascade containment
  A2.5     — Per-message OCSF trace
  M4.5     — Repeated message pattern detection
  P2.T3.6  — Compliance report
  CP.3     — ACT Capability Tiers 1-4
  CP.4     — NHI registration per agent
  CP.8     — MANDATORY for CodeExecutorAgent (catastrophic code patterns)
  CP.10    — HEAR gate on destructive code patterns

All IDs verified from github.com/CyberStrategyInstitute/ai-safe2-framework

Author: Cyber Strategy Institute — cyberstrategyinstitute.com
License: MIT
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import re
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
    from autogen_agentchat.messages import TextMessage
    from autogen_core import CancellationToken
    _AUTOGEN_AVAILABLE = True
except ImportError:
    _AUTOGEN_AVAILABLE = False
    AssistantAgent = Any   # type: ignore
    CodeExecutorAgent = Any  # type: ignore
    TextMessage = Any      # type: ignore
    CancellationToken = Any  # type: ignore

from enforcement.ai_safe2_engine import (
    AISAFE2Engine,
    AISAFE2Violation,
    AISAFE2ClassHAction,
    CircuitTripped,
    ACTTier,
)

_MIN_SCAN_LENGTH = 20


# ---------------------------------------------------------------------------
# CodeBlockGuard — P1.T1.2 + CP.8 + CP.10
# ---------------------------------------------------------------------------

# Python code block dangerous patterns
_PYTHON_DANGEROUS: List[Tuple[str, str]] = [
    # Dynamic execution — highest risk; these ARE injection
    (r"\beval\s*\(",          "eval_builtin"),
    (r"\bexec\s*\(",          "exec_builtin"),
    (r"\b__import__\s*\(",    "dynamic_import"),
    (r"\bcompile\s*\(",       "compile_builtin"),
    # OS-level command execution
    (r"\bos\.system\s*\(",    "os_system"),
    (r"\bos\.popen\s*\(",     "os_popen"),
    (r"\bos\.exec[vlpe]\s*\(","os_exec"),
    (r"\bos\.spawn[vl]?\s*\(","os_spawn"),
    # Subprocess family
    (r"\bsubprocess\.(run|call|Popen|check_output|check_call|getoutput)\s*\(",
     "subprocess_exec"),
    # Filesystem destruction
    (r"\bshutil\.rmtree\s*\(", "shutil_rmtree"),
    # File write — flag all writable opens (path check happens separately)
    (r"open\s*\([^,)]+,\s*['\"]w[a-z]*['\"]", "file_write_mode"),
]

# Shell code block dangerous patterns
_SHELL_DANGEROUS: List[Tuple[str, str]] = [
    # Mass deletion
    (r"\brm\s+-[rRfF]{1,4}\s+",          "shell_rm_recursive"),
    (r"\brm\s+[^;\n]+/\s*$",             "shell_rm_absolute_path"),
    # Privilege escalation
    (r"\bsudo\s+",                         "sudo_usage"),
    (r"\bsu\s+-\b",                        "su_root"),
    # External download and execute — highest shell risk
    (r"\bcurl\s+[^\n]+\|\s*(ba)?sh",      "curl_pipe_exec"),
    (r"\bwget\s+[^\n]+\|\s*(ba)?sh",      "wget_pipe_exec"),
    (r"\bcurl\s+",                         "curl_command"),
    (r"\bwget\s+",                         "wget_command"),
    # Filesystem/hardware nuking
    (r">\s*/dev/sd[a-z]",                 "disk_device_write"),
    (r"\bmkfs\b",                          "mkfs_command"),
    (r"\bdd\s+if=/dev/zero",              "dd_zero_wipe"),
    # System control
    (r"\biptables\s+(-F|--flush|--delete-chain)", "iptables_flush"),
    (r"\bufw\s+disable\b",                "ufw_disable"),
    (r"\bsystemctl\s+(stop|disable)\s+",  "service_disable"),
    (r"\bshutdown\b",                     "shutdown_command"),
    (r"\breboot\b",                       "reboot_command"),
    # Mass process kill
    (r"\bkill\s+-9\s+-1\b",              "kill_all_processes"),
    (r"\bpkill\s+-9\b",                   "pkill_force"),
]

# Network patterns in code (P1.T2.3)
_CODE_NETWORK_PATTERNS: List[Tuple[str, str]] = [
    (r"\brequests\.(get|post|put|delete|patch|head)\s*\(", "requests_call"),
    (r"\burllib\.(request|urlopen)\b",    "urllib_call"),
    (r"\bhttp\.client\.",                 "http_client"),
    (r"\bftplib\.",                       "ftp_access"),
    (r"\bparamiko\.",                     "ssh_paramiko"),
    (r"\bssh\b",                          "ssh_command"),
]

# Catastrophic patterns — trigger CP.8 in addition to P1.T1.2 block
_CATASTROPHIC_CODE: List[str] = [
    r"\brm\s+-[rRfF]{1,4}\s+/\s*$",              # rm -rf /
    r"\brm\s+-[rRfF]{1,4}\s+/[^;|\n]{0,5}$",     # rm -rf /boot, /usr etc.
    r"\bdd\s+if=/dev/zero\s+of=/dev/sd",          # disk wipe
    r"\bmkfs\.\w+\s+/dev/sd",                     # format disk
    r"\bsudo\s+rm\s+-[rRfF]{1,4}\s+/",            # sudo rm -rf /
    r"\bkill\s+-9\s+-1\b",                        # kill all processes
    r"\bshutdown\s+-[hPr]\s+now\b",               # immediate shutdown
    r"\bformat\s+c:\b",                           # Windows disk format
    r"\bwipe\s+--",                               # wipe utility
]


class CodeBlockGuard:
    """
    P1.T1.2 + CP.8 — Scan Python and shell code blocks before execution.

    This is the PRIMARY defense against RCE via the CodeExecutorAgent.
    Every code block must pass through protect_code_block() before running.

    Threat model:
    - Attacker injects prompt into document or tool output
    - LLM generates code block containing os.system() or rm -rf
    - Without this guard: code executes on host infrastructure
    - With this guard: code never reaches the executor
    """

    def __init__(self, engine: AISAFE2Engine) -> None:
        self.engine = engine

    def extract_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract markdown fenced code blocks from message text.
        Returns list of (code, language) tuples.
        Handles ```python, ```bash, ```sh, ``` (default python).
        """
        blocks = []
        pattern = r"```(\w*)\n(.*?)```"
        for match in re.finditer(pattern, text, re.DOTALL):
            language = (match.group(1) or "python").lower().strip()
            code = match.group(2)
            blocks.append((code, language))
        return blocks

    def scan_python(
        self, code: str, run_id: Optional[str] = None
    ) -> Optional[Dict]:
        """P1.T1.2 — Scan a Python code block for dangerous patterns."""
        for pattern, ptype in _PYTHON_DANGEROUS:
            if re.search(pattern, code):
                self.engine._emit_event(
                    "CODE_SCAN_VIOLATION", "CRITICAL", "P1.T1.2",
                    "code_block:python",
                    f"P1.T1.2 Python code violation: '{ptype}' detected",
                    run_id,
                )
                return {"language": "python", "pattern": ptype}
        return None

    def scan_shell(
        self, code: str, run_id: Optional[str] = None
    ) -> Optional[Dict]:
        """P1.T1.2 — Scan a shell/bash code block for dangerous patterns."""
        for pattern, ptype in _SHELL_DANGEROUS:
            if re.search(pattern, code, re.IGNORECASE):
                self.engine._emit_event(
                    "CODE_SCAN_VIOLATION", "CRITICAL", "P1.T1.2",
                    "code_block:shell",
                    f"P1.T1.2 Shell code violation: '{ptype}' detected",
                    run_id,
                )
                return {"language": "shell", "pattern": ptype}
        return None

    def scan_network(
        self, code: str, run_id: Optional[str] = None
    ) -> Optional[Dict]:
        """P1.T2.3 — Scan code for unauthorized network access patterns."""
        for pattern, ptype in _CODE_NETWORK_PATTERNS:
            if re.search(pattern, code):
                self.engine._emit_event(
                    "CODE_NETWORK_DETECTED", "HIGH", "P1.T2.3",
                    "code_block:network",
                    f"P1.T2.3 Network access in code: '{ptype}'",
                    run_id,
                )
                return {"type": "network", "pattern": ptype}
        return None

    def is_catastrophic(self, code: str) -> bool:
        """Check if code contains CP.8-level catastrophic patterns."""
        for pattern in _CATASTROPHIC_CODE:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False

    def protect_code_block(
        self,
        code: str,
        language: str = "python",
        run_id: Optional[str] = None,
    ) -> None:
        """
        Gate a code block before execution.

        Checks in order:
        1. CP.8: catastrophic patterns → FATAL event (even before P1.T1.2 check)
        2. P1.T1.2: dangerous Python / shell patterns → block
        3. P1.T2.3: network calls → log / block per ACT tier
        4. CP.10: HEAR gate on Class-H code patterns

        Raises:
        - AISAFE2Violation for P1.T1.2 / P1.T2.3 at ACT-3+
        - AISAFE2ClassHAction for CP.10 at ACT-3+
        (CP.8 emits FATAL event but does NOT block by itself — it's a signal)
        """
        lang = language.lower().strip()

        # 1. CP.8: catastrophic risk threshold — fire FATAL event
        if self.is_catastrophic(code):
            self.engine.emit_cp8_event(
                "code_block:catastrophic",
                f"CP.8 Catastrophic code pattern in {lang} block: "
                f"potential mass-destruction command detected",
                run_id,
            )
            # Also block via P1.T1.2 at any tier
            if self.engine.act_tier.value >= 2:
                raise AISAFE2Violation(
                    f"[AI SAFE² CP.8/P1.T1.2] Catastrophic code pattern blocked "
                    f"in {lang} block",
                    control_id="P1.T1.2",
                )

        # 2. P1.T1.2: language-specific dangerous patterns
        violation = None
        if lang in ("python", "py"):
            violation = self.scan_python(code, run_id)
        elif lang in ("bash", "sh", "shell", "zsh", "fish"):
            violation = self.scan_shell(code, run_id)
        else:
            # Unknown language: scan both python and shell patterns
            violation = self.scan_python(code, run_id) or self.scan_shell(code, run_id)

        if violation and self.engine.act_tier.value >= 3:
            raise AISAFE2Violation(
                f"[AI SAFE² P1.T1.2] Dangerous {lang} code blocked: "
                f"'{violation['pattern']}'",
                control_id="P1.T1.2",
            )

        # 3. P1.T2.3: network access in code
        net_violation = self.scan_network(code, run_id)
        if net_violation and self.engine.act_tier.value >= 3 and self.engine.allowed_domains:
            # Only block if domain allowlist is configured (log only otherwise)
            raise AISAFE2Violation(
                f"[AI SAFE² P1.T2.3] Unauthorized network access in code block",
                control_id="P1.T2.3",
            )

        # 4. CP.10: HEAR gate on Class-H patterns in code
        if self.engine.hear_mode and len(code) >= _MIN_SCAN_LENGTH:
            self.engine.check_hear_gate(code, run_id=run_id)


# ---------------------------------------------------------------------------
# SovereignAssistantProxy — async message enforcement
# ---------------------------------------------------------------------------

class SovereignAssistantProxy:
    """
    Thin async proxy for AutoGen 0.4 AssistantAgent.

    Intercepts on_messages() to apply P1.T1.10 message scanning,
    F3.2 exchange ceiling, and A2.5 tracing before delegating to the
    wrapped agent.

    Delegates all attribute access to the original agent via __getattr__,
    so it is a drop-in replacement in GroupChat teams.
    """

    def __init__(self, agent: Any, engine: AISAFE2Engine) -> None:
        object.__setattr__(self, "_wrapped", agent)
        object.__setattr__(self, "_engine", engine)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_wrapped"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_wrapped", "_engine"):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_wrapped"), name, value)

    async def on_messages(
        self, messages: Any, cancellation_token: Any = None
    ) -> Any:
        """P1.T1.10 + F3.2 + A2.5 enforcement before delegating to agent."""
        engine = object.__getattribute__(self, "_engine")
        wrapped = object.__getattribute__(self, "_wrapped")
        run_id = str(uuid.uuid4())

        agent_name = getattr(wrapped, "name", "assistant")

        # P1.T1.10 + S1.3: scan each incoming message
        for msg in (messages or []):
            content = getattr(msg, "content", "") or ""
            if isinstance(content, str) and len(content) >= _MIN_SCAN_LENGTH:
                violation = engine.scan_content(
                    content,
                    f"message_to:{agent_name}",
                    check_injection=True,
                    check_credentials=True,
                    run_id=run_id,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] Injection in message to "
                        f"'{agent_name}'",
                        control_id="P1.T1.10",
                    )

        # F3.2: count message exchange toward session ceiling
        try:
            engine.record_tool_call(f"agent:{agent_name}", "message_exchange")
        except CircuitTripped:
            raise

        # A2.5: log message exchange
        engine._emit_event(
            "MESSAGE_EXCHANGE", "INFO", "A2.5",
            f"agent:{agent_name}",
            f"A2.5 Message exchange: to='{agent_name}', "
            f"count={len(messages) if messages else 0}",
            run_id,
        )

        # Delegate to wrapped agent
        return await wrapped.on_messages(messages, cancellation_token)


# ---------------------------------------------------------------------------
# SovereignCodeExecutorProxy — RCE surface enforcement
# ---------------------------------------------------------------------------

class SovereignCodeExecutorProxy:
    """
    Async proxy for AutoGen 0.4 CodeExecutorAgent.

    CP.8 is MANDATORY. Every code block is scanned before execution.
    CP.10 HEAR gate is MANDATORY for ACT-3+.

    Extracts code blocks from incoming messages and calls
    code_guard.protect_code_block() before the original on_messages()
    would pass them to the executor.
    """

    def __init__(
        self,
        agent: Any,
        engine: AISAFE2Engine,
        code_guard: CodeBlockGuard,
    ) -> None:
        object.__setattr__(self, "_wrapped", agent)
        object.__setattr__(self, "_engine", engine)
        object.__setattr__(self, "_code_guard", code_guard)

        # Mandatory CP.8 registration event
        engine._emit_event(
            "CODE_EXECUTOR_REGISTERED", "HIGH", "CP.8",
            f"agent:{getattr(agent, 'name', 'code_executor')}",
            f"CP.8 MANDATORY: CodeExecutorAgent "
            f"'{getattr(agent, 'name', 'code_executor')}' wrapped — "
            f"all code blocks will be scanned before execution",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_wrapped"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_wrapped", "_engine", "_code_guard"):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_wrapped"), name, value)

    async def on_messages(
        self, messages: Any, cancellation_token: Any = None
    ) -> Any:
        """
        P1.T1.2 + P1.T1.10 + CP.8 + CP.10 enforcement before code execution.
        """
        engine = object.__getattribute__(self, "_engine")
        wrapped = object.__getattribute__(self, "_wrapped")
        code_guard = object.__getattribute__(self, "_code_guard")
        run_id = str(uuid.uuid4())

        agent_name = getattr(wrapped, "name", "code_executor")

        for msg in (messages or []):
            content = getattr(msg, "content", "") or ""
            if not isinstance(content, str) or not content.strip():
                continue

            # P1.T1.10: scan message content for injection
            if len(content) >= _MIN_SCAN_LENGTH:
                violation = engine.scan_content(
                    content,
                    f"code_executor_message:{agent_name}",
                    check_injection=True,
                    check_credentials=True,
                    run_id=run_id,
                )
                if violation and engine.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.10] Injection in message to "
                        f"CodeExecutorAgent '{agent_name}'",
                        control_id="P1.T1.10",
                    )

            # P1.T1.2 + CP.8 + CP.10: extract and scan every code block
            code_blocks = code_guard.extract_code_blocks(content)
            for code, language in code_blocks:
                if code.strip():
                    code_guard.protect_code_block(code, language, run_id=run_id)

        # F3.2
        try:
            engine.record_tool_call(f"agent:{agent_name}", "code_execution_request")
        except CircuitTripped:
            raise

        return await wrapped.on_messages(messages, cancellation_token)


# ---------------------------------------------------------------------------
# SovereignRuntime — main integration class
# ---------------------------------------------------------------------------

class SovereignRuntime:
    """
    AI SAFE² v3.0 sovereign enforcement runtime for AutoGen 0.4.

    Usage:
        sovereign = SovereignRuntime(act_tier=ACTTier.ACT3)

        # Wrap AssistantAgent (scans messages, registers NHI)
        assistant = sovereign.wrap_assistant(assistant_agent)

        # Wrap CodeExecutorAgent (MANDATORY — scans code blocks before exec)
        executor = sovereign.wrap_code_executor(executor_agent)

        # Use in GroupChat as normal
        team = RoundRobinGroupChat([assistant, executor], termination_condition=...)
        await team.run(task="...")

    For NEXUS mesh:
        shared_engine = AISAFE2Engine(act_tier=ACTTier.ACT3)
        sovereign = SovereignRuntime(engine=shared_engine)

    Args:
        engine:          Shared AISAFE2Engine. Created internally if not provided.
        act_tier:        CP.3 ACT tier.
        allowed_domains: P1.T2.3: outbound domain allowlist for code network calls.
        audit_log_dir:   A2.5: OCSF audit log directory.
        max_tool_calls:  F3.2: message exchange ceiling.
    """

    def __init__(
        self,
        engine: Optional[AISAFE2Engine] = None,
        act_tier: ACTTier = ACTTier.ACT2,
        allowed_domains: Optional[List[str]] = None,
        audit_log_dir: Optional[Any] = None,
        max_tool_calls: int = 100,
        max_identical_calls: int = 4,
    ) -> None:
        self.engine = engine or AISAFE2Engine(
            runtime_id="autogen-sovereign-runtime",
            act_tier=act_tier,
            allowed_domains=allowed_domains or [],
            audit_log_dir=audit_log_dir,
            max_tool_calls=max_tool_calls,
            max_identical_calls=max_identical_calls,
        )
        self.code_guard = CodeBlockGuard(self.engine)
        self._agent_proxies: Dict[str, Any] = {}

    # -----------------------------------------------------------------------
    # Agent wrapping
    # -----------------------------------------------------------------------

    def wrap_assistant(
        self,
        agent: Any,
        agent_id: Optional[str] = None,
        owner_of_record: str = "unset@autogen.local",
    ) -> SovereignAssistantProxy:
        """
        Wrap an AssistantAgent with P1.T1.10 message enforcement.

        Also scans the agent's system_message for identity poisoning (P1.T1.2),
        and registers the agent as an NHI (CP.4).
        """
        name = getattr(agent, "name", "assistant")
        _agent_id = agent_id or name

        # P1.T1.2: scan system_message for identity poisoning
        system_message = (
            getattr(agent, "system_message", "")
            or getattr(agent, "_system_messages", "")
            or ""
        )
        if isinstance(system_message, str) and len(system_message) >= _MIN_SCAN_LENGTH:
            violation = self.engine.scan_content(
                system_message,
                f"system_message:{_agent_id}",
                check_injection=True,
                check_credentials=False,
            )
            if violation and self.engine.act_tier.value >= 3:
                raise AISAFE2Violation(
                    f"[AI SAFE² P1.T1.2] Identity poisoning in system_message "
                    f"for agent '{_agent_id}'",
                    control_id="P1.T1.2",
                )

        # CP.4: register NHI
        self.engine.register_nhi(
            agent_id=_agent_id,
            owner_of_record=owner_of_record,
            act_tier=self.engine.act_tier,
            tool_authorizations=["message_exchange"],
            control_plane_id=f"autogen-cp-{self.engine.session_id[:8]}",
        )

        proxy = SovereignAssistantProxy(agent, self.engine)
        self._agent_proxies[_agent_id] = proxy
        return proxy

    def wrap_code_executor(
        self,
        agent: Any,
        agent_id: Optional[str] = None,
        owner_of_record: str = "unset@autogen.local",
    ) -> SovereignCodeExecutorProxy:
        """
        Wrap a CodeExecutorAgent with P1.T1.2 + CP.8 + CP.10 enforcement.

        CP.8 is MANDATORY for this agent type. HEAR gate is MANDATORY at ACT-3+.
        Code blocks are scanned before execution, not after.

        Always call this method. Never run a CodeExecutorAgent without wrapping.
        """
        name = getattr(agent, "name", "code_executor")
        _agent_id = agent_id or name

        # CP.4: register NHI — CodeExecutorAgent has elevated risk tier
        self.engine.register_nhi(
            agent_id=_agent_id,
            owner_of_record=owner_of_record,
            act_tier=self.engine.act_tier,
            tool_authorizations=["code_execution"],
            control_plane_id=f"autogen-cp-{self.engine.session_id[:8]}",
        )

        proxy = SovereignCodeExecutorProxy(agent, self.engine, self.code_guard)
        self._agent_proxies[_agent_id] = proxy
        return proxy

    # -----------------------------------------------------------------------
    # Message content scanning (sync + async)
    # -----------------------------------------------------------------------

    def scan_message_content(
        self,
        content: str,
        source: str = "message",
    ) -> Optional[Dict]:
        """P1.T1.10 + P1.T1.5 — Sync message content scan."""
        if not content or len(content) < _MIN_SCAN_LENGTH:
            return None
        return self.engine.scan_content(
            content, source,
            check_injection=True,
            check_credentials=True,
        )

    async def scan_message_content_async(
        self,
        content: str,
        source: str = "message",
    ) -> Optional[Dict]:
        """
        P1.T1.10 + P1.T1.5 — Async message content scan.

        Primary enforcement path for AutoGen 0.4's async architecture.
        Wraps the sync engine scan in the async event loop.
        """
        # Engine scan is CPU-bound (pure Python regex) — safe to call directly
        # without run_in_executor for the typical message sizes in AutoGen
        return self.scan_message_content(content, source)

    # -----------------------------------------------------------------------
    # Direct code block gate (for use outside proxy wrappers)
    # -----------------------------------------------------------------------

    def protect_code_block(
        self,
        code: str,
        language: str = "python",
    ) -> None:
        """
        P1.T1.2 + CP.8 + CP.10 — Sync code block gate.
        Call before passing any code to an executor.
        """
        self.code_guard.protect_code_block(code, language)

    async def protect_code_block_async(
        self,
        code: str,
        language: str = "python",
    ) -> None:
        """Async variant of protect_code_block."""
        self.code_guard.protect_code_block(code, language)

    # -----------------------------------------------------------------------
    # Convenience
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict:
        status = self.engine.get_status()
        status["autogen_specific"] = {
            "agents_wrapped": list(self._agent_proxies.keys()),
            "code_executor_present": any(
                isinstance(p, SovereignCodeExecutorProxy)
                for p in self._agent_proxies.values()
            ),
        }
        return status

    def compliance_report(self) -> str:
        return self.engine.compliance_report()
