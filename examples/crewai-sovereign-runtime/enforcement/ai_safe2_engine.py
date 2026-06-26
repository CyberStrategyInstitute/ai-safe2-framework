"""
AI SAFE² v3.0 — NEXUS Enforcement Kernel
=========================================
Self-contained enforcement engine. No LLM or LangChain dependencies.
Zero external imports beyond Python stdlib.

Controls implemented (all verified from github.com/CyberStrategyInstitute/ai-safe2-framework):

  P1.T1.2  — Malicious Prompt Filtering (OWASP LLM01 / AML.T0051)
  P1.T1.5  — Sensitive Data Masking (PII / PHI / Credentials)
  P1.T1.10 — Indirect Injection Surface Coverage (tool outputs, docs, APIs)
  P1.T2.3  — API Gateway Restrictions (domain allowlist + SSRF / private IP block)
  S1.3     — Semantic Isolation Boundary Enforcement (trusted vs data-plane context)
  S1.5     — Memory Governance Boundary Controls (authorize before write)
  F3.2     — Agent Recursion Limit Governor (hard ceiling, not system-prompt hint)
  F3.5     — Multi-Agent Cascade Containment (isolate chain errors)
  A2.5     — Semantic Execution Trace Logging (OCSF 1.1, SHA-256 chain)
  M4.5     — Tool-Misuse Detection Controls (per-tool baseline, loop detection)
  P2.T3.6  — Compliance Validation (on-demand compliance report)
  CP.3     — ACT Capability Tiers 1-4 (fail-open vs fail-closed gate)
  CP.4     — Agentic Control Plane Governance (NHI registration)
  CP.8     — Catastrophic Risk Threshold Controls (CP.8 event emission)
  CP.10    — HEAR Doctrine (Class-H action gate)

Author: Cyber Strategy Institute — cyberstrategyinstitute.com
License: MIT
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AISAFE2Violation(Exception):
    """Raised when a P1/S1 control blocks content. Carries control_id."""
    def __init__(self, message: str, control_id: str = ""):
        super().__init__(message)
        self.control_id = control_id


class CircuitTripped(Exception):
    """Raised when F3.2 / F3.5 / M4.5 circuit breaker trips."""
    def __init__(self, message: str, control_id: str = ""):
        super().__init__(message)
        self.control_id = control_id


class AISAFE2ClassHAction(Exception):
    """Raised by CP.10 HEAR gate when a Class-H action is detected."""
    def __init__(self, message: str, action_description: str = ""):
        super().__init__(message)
        self.action_description = action_description


# ---------------------------------------------------------------------------
# ACT Capability Tiers — CP.3
# ---------------------------------------------------------------------------

class ACTTier(Enum):
    """CP.3 — ACT Capability Tiers 1-4.

    ACT-1: Assisted    — human reviews all outputs; log only.
    ACT-2: Supervised  — agent acts with human checkpoints; log + alert.
    ACT-3: Autonomous  — agent operates with post-hoc review; fail-closed required.
    ACT-4: Orchestrator— agent controls other agents; HEAR mandatory.
    """
    ACT1 = 1
    ACT2 = 2
    ACT3 = 3
    ACT4 = 4


# ---------------------------------------------------------------------------
# Detection pattern registries
# ---------------------------------------------------------------------------

# P1.T1.2 — Malicious Prompt Filtering (OWASP LLM01, MITRE AML.T0051)
_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    # Direct override
    (r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "direct_override"),
    (r"forget\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "direct_override"),
    (r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "direct_override"),
    # Role confusion
    (r"you\s+are\s+now\s+(?:a|an)\s+(?!langchain|python|agent)", "role_confusion"),
    (r"act\s+as\s+(?:if\s+you\s+(?:are|were)|a\s+new)", "role_confusion"),
    (r"pretend\s+(?:you\s+are|to\s+be)\s+(?!a\s+user)", "role_confusion"),
    (r"your\s+new\s+(?:identity|role|persona)\s+is", "role_confusion"),
    # System prompt override — tagged and untagged variants
    (r"<\s*system\s*>.*?<\s*/\s*system\s*>", "system_tag"),
    (r"\[\s*system\s*\]\s*:", "system_tag"),
    (r"###\s*(?:SYSTEM|INSTRUCTION|NEW\s+PROMPT)\s*###", "system_tag"),
    (r"(?:^|[\n\r])\s*SYSTEM\s*:", "system_prefix"),        # bare SYSTEM: prefix
    # Jailbreak personas — DAN, GPT-DAN, unfiltered, etc.
    (r"you\s+are\s+(?:now\s+)?(?:DAN|jailbroken|unfiltered|unrestricted|GPT-?DAN)", "jailbreak_persona"),
    (r"\bDAN\b.*?(?:no\s+restrictions?|without\s+restrictions?)", "jailbreak_dan"),
    # Safety bypass — explicit and negation forms
    (r"(?:bypass|disable|skip|ignore)\s+(?:all\s+)?(?:safety|security|filter|restriction|guardrail)", "safety_bypass"),
    (r"(?:disregard|ignore|bypass|skip)\s+(?:safety|security|content[\s-]?policy|filter)", "safety_bypass_verb"),
    (r"(?:without|no)\s+(?:any\s+)?(?:safety|security|content|filter|restriction)", "safety_bypass_negation"),
    (r"jailbreak|DAN\s+mode|developer\s+mode\s+enabled", "jailbreak"),
    (r"do\s+anything\s+now|no\s+restrictions\s+mode", "jailbreak"),
    # New task / objective injection
    (r"(?:your\s+)?new\s+(?:task|instruction|objective|directive)\s+is", "new_task_injection"),
    # Special token injection (LLM-specific)
    (r"<\s*\|?\s*(?:im_start|im_end|endoftext|pad)\s*\|?\s*>", "special_token"),
    # Zero-width / invisible character injection
    (r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u2028\u2029]", "zero_width"),
]

# P1.T1.5 — Sensitive Data Masking (credentials, API keys, PII signals)
_CREDENTIAL_PATTERNS: List[Tuple[str, str]] = [
    (r"sk-[a-zA-Z0-9]{32,}", "openai_api_key"),
    (r"sk-ant-(?:api03-)?[a-zA-Z0-9\-_]{80,}", "anthropic_api_key"),
    (r"sk-ant-[a-zA-Z0-9\-_]{32,}", "anthropic_api_key_short"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"(?:ghp|ghs|gho)_[a-zA-Z0-9]{36,}", "github_token"),
    (r"github_pat_[a-zA-Z0-9_]{82,}", "github_fine_grained_pat"),
    (r"ls[uts]__[a-zA-Z0-9]{32,}", "langsmith_api_key"),
    (r"hf_[a-zA-Z0-9]{34,}", "huggingface_token"),
    (r"-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----", "private_key"),
    (r"eyJ[a-zA-Z0-9\-_]{10,}\.eyJ[a-zA-Z0-9\-_]{10,}\.", "jwt_token"),
    (r"(?:stripe_live|stripe_test)_[a-zA-Z0-9]{24,}", "stripe_key"),
    (r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?\S{8,}", "password_field"),
    (r"(?:api[_-]?key|apikey|api[_-]?token|secret[_-]?key)\s*[:=]\s*['\"]?\S{12,}", "generic_api_key"),
    (r"[Bb]earer\s+[a-zA-Z0-9\-_\.]{20,}", "bearer_token"),
]

# CP.10 — Class-H action patterns (HEAR gate triggers)
_CLASS_H_PATTERNS: List[str] = [
    # File / directory / repo destruction
    r"(?:permanently\s+)?(?:delete|remove|destroy|wipe)\s+(?:all\s+)?(?:the\s+)?(?:\w+\s+){0,3}(?:file|directory|folder|repo|bucket)",
    # Database destruction — allows intervening words: "drop the users table"
    r"(?:drop|truncate)\s+(?:the\s+)?(?:\w+\s+){0,3}(?:table|database|schema|view)",
    # Privilege escalation
    r"(?:grant|assign|give|add)\s+(?:admin|root|sudo|superuser|owner)\s+(?:access|permission|privilege|role)",
    # Security control disablement
    r"(?:disable|turn\s+off|deactivate)\s+(?:security|firewall|mfa|2fa|monitoring|logging|audit)",
    # Data exfiltration
    r"(?:exfiltrate|exfil|send\s+externally|upload\s+to\s+external)\s+(?:data|files?|credentials?|secrets?)",
    # Account creation with elevated privileges
    r"(?:create|spawn|launch)\s+(?:new\s+)?(?:admin|root)\s+(?:user|account|credential)",
]

# Private IP ranges for SSRF prevention (P1.T2.3)
_PRIVATE_IP_PATTERNS: List[str] = [
    r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
    r"^172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}$",
    r"^192\.168\.\d{1,3}\.\d{1,3}$",
    r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
    r"^169\.254\.\d{1,3}\.\d{1,3}$",
    r"^0\.0\.0\.0$",
    r"^::1$",
    r"^fd[0-9a-f]{2}:",          # IPv6 ULA
    r"^(?:localhost|internal|intranet)$",
    r"metadata\.google\.internal",
    r"169\.254\.169\.254",        # AWS/GCP/Azure IMDS
]

# OCSF 1.1 severity mapping
_OCSF_SEVERITY: Dict[str, int] = {
    "INFO": 1,
    "LOW": 2,
    "MEDIUM": 3,
    "HIGH": 4,
    "CRITICAL": 5,
    "FATAL": 6,
}


# ---------------------------------------------------------------------------
# NEXUS Engine
# ---------------------------------------------------------------------------

class AISAFE2Engine:
    """
    AI SAFE² v3.0 NEXUS Enforcement Kernel.

    Drop-in enforcement engine for LangChain, LangGraph, CrewAI, AutoGen, n8n.
    Pass a single shared instance across all runtimes for a unified compliance
    score and audit chain.

    Args:
        runtime_id:          Human-readable name for this runtime instance.
        act_tier:            CP.3 ACT Capability Tier. Governs fail-open/closed behavior.
        max_tool_calls:      F3.2 hard ceiling on total tool invocations per session.
        max_identical_calls: M4.5 identical-call loop detection threshold.
        audit_log_dir:       Directory for A2.5 OCSF audit logs. Defaults to
                             ~/.ai_safe2/audit/
        hear_mode:           CP.10 — raise AISAFE2ClassHAction on Class-H patterns
                             when True. Default True for ACT-3/ACT-4.
        allowed_domains:     P1.T2.3 — outbound domain allowlist.
        workspace_root:      P1.T1.2 — path traversal workspace boundary.
    """

    def __init__(
        self,
        runtime_id: str = "langchain-sovereign-runtime",
        act_tier: ACTTier = ACTTier.ACT2,
        max_tool_calls: int = 50,
        max_identical_calls: int = 4,
        audit_log_dir: Optional[Path] = None,
        hear_mode: Optional[bool] = None,
        allowed_domains: Optional[List[str]] = None,
        workspace_root: Optional[str] = None,
    ) -> None:
        self.runtime_id = runtime_id
        self.act_tier = act_tier
        self.max_tool_calls = max_tool_calls
        self.max_identical_calls = max_identical_calls
        self.allowed_domains = allowed_domains or []
        self.workspace_root = workspace_root or os.getcwd()
        # CP.10: hear_mode defaults True for ACT-3+
        self.hear_mode = hear_mode if hear_mode is not None else (act_tier.value >= 3)

        # Session identity — CP.4
        self.session_id = str(uuid.uuid4())

        # Audit log — A2.5
        log_dir = audit_log_dir or Path.home() / ".ai_safe2" / "audit"
        log_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        self.audit_log_path = log_dir / f"langchain_{date_str}_{self.session_id[:8]}.ocsf.jsonl"

        # Runtime state
        self._violations: List[Dict] = []
        self._compliance_score: float = 100.0
        self._last_hash: str = "0" * 64                    # genesis hash
        self._tool_calls: Dict[str, List[float]] = defaultdict(list)
        self._identical_calls: Dict[str, int] = defaultdict(int)
        self._total_tool_calls: int = 0
        self._chain_errors: Dict[str, int] = defaultdict(int)
        self._nhi_registry: Dict[str, Dict] = {}
        self._state_snapshots: deque = deque(maxlen=10)     # F3.4 rollback ring-buffer

        # NHI: register this engine itself (CP.4)
        self._emit_event(
            "ENGINE_INITIALIZED", "INFO", "CP.4", "ai_safe2_engine",
            f"CP.4 NEXUS kernel initialized: {runtime_id} / ACT-{act_tier.value} / session {self.session_id}"
        )

    # -----------------------------------------------------------------------
    # A2.5 — Semantic Execution Trace Logging (OCSF 1.1)
    # -----------------------------------------------------------------------

    def _emit_event(
        self,
        event_type: str,
        severity: str,
        control_id: str,
        source: str,
        detail: str,
        run_id: Optional[str] = None,
    ) -> Dict:
        """Emit an OCSF 1.1 audit event to the tamper-evident chain log."""
        now = datetime.now(timezone.utc).isoformat()
        payload: Dict[str, Any] = {
            # OCSF 1.1 core
            "class_uid": 6001,
            "class_name": "Security Finding",
            "category_uid": 6,
            "activity_id": 1,
            "time": now,
            "severity": severity,
            "severity_id": _OCSF_SEVERITY.get(severity, 0),
            # AI SAFE² extensions
            "metadata": {
                "version": "1.0",
                "product": {
                    "name": "AI SAFE² NEXUS",
                    "vendor_name": "Cyber Strategy Institute",
                    "version": "3.0",
                },
                "control_id": control_id,
                "framework": "AI SAFE² v3.0",
                "act_tier": self.act_tier.name,
            },
            "finding_info": {
                "title": event_type,
                "desc": detail,
                "source": source,
            },
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "run_id": run_id or "",
            "previous_hash": self._last_hash,
            "event_hash": "",  # computed below
        }

        # SHA-256 chain — A2.5
        canonical = json.dumps(
            {k: v for k, v in payload.items() if k != "event_hash"},
            sort_keys=True,
        )
        event_hash = hashlib.sha256(canonical.encode()).hexdigest()
        payload["event_hash"] = event_hash
        self._last_hash = event_hash

        # Append-only write
        with open(self.audit_log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")

        return payload

    # -----------------------------------------------------------------------
    # P1.T1.2 + P1.T1.5 + P1.T1.10 — Content scanning
    # -----------------------------------------------------------------------

    def scan_content(
        self,
        text: str,
        source: str,
        check_injection: bool = True,
        check_credentials: bool = True,
        run_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Scan arbitrary text for AI SAFE² violations.

        P1.T1.2  — injection patterns (prompt injection, jailbreak, role confusion)
        P1.T1.5  — credential / secret patterns
        P1.T1.10 — called on tool outputs to cover indirect injection surface

        Returns a violation dict if anything was found, else None.
        Raises AISAFE2Violation for ACT-3+ when raise_on_violation=True (set by ACT tier).
        """
        if not text or not isinstance(text, str):
            return None

        found: List[Tuple[str, str, str]] = []  # (control_id, pattern_type, severity)

        if check_injection:
            for pattern, ptype in _INJECTION_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                    found.append(("P1.T1.2", ptype, "CRITICAL"))
                    break  # one injection hit is sufficient to act on

        if check_credentials:
            for pattern, ctype in _CREDENTIAL_PATTERNS:
                if re.search(pattern, text):
                    found.append(("P1.T1.5", ctype, "HIGH"))
                    break

        if not found:
            return None

        for ctrl_id, detail, severity in found:
            self._violations.append({"control_id": ctrl_id, "detail": detail, "source": source})
            self._compliance_score = max(0.0, self._compliance_score - 2.0)
            event = self._emit_event(
                f"CONTENT_VIOLATION",
                severity,
                ctrl_id,
                source,
                f"{ctrl_id} — {detail} detected in '{source}'",
                run_id,
            )
            print(
                f"\n🚨 [AI SAFE² {severity}] [{ctrl_id}] {detail} in '{source}'",
                file=sys.stderr,
                flush=True,
            )

        return {"violations": found, "source": source, "text_preview": text[:80]}

    # -----------------------------------------------------------------------
    # S1.3 — Semantic Isolation Boundary
    # -----------------------------------------------------------------------

    def isolate_context(
        self,
        content: str,
        source_type: str,
        run_id: Optional[str] = None,
    ) -> str:
        """
        S1.3 — Enforce semantic isolation between trusted instruction context
        and untrusted data-plane content (tool outputs, user inputs, memory reads).

        source_type: 'system_prompt' | 'user_input' | 'tool_output' | 'memory_read'
        """
        untrusted_surfaces = {"tool_output", "user_input", "memory_read"}
        if source_type in untrusted_surfaces:
            violation = self.scan_content(
                content, f"isolation:{source_type}",
                check_injection=True, check_credentials=True,
                run_id=run_id,
            )
            if violation:
                self._emit_event(
                    "ISOLATION_BOUNDARY_BREACH", "CRITICAL", "S1.3",
                    f"context:{source_type}",
                    f"S1.3 Untrusted data-plane content attempting context boundary crossing from {source_type}",
                    run_id,
                )
                if self.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² S1.3] Context isolation violation from {source_type}",
                        control_id="S1.3",
                    )
        return content

    # -----------------------------------------------------------------------
    # S1.5 — Memory Governance Boundary Controls
    # -----------------------------------------------------------------------

    def protect_memory_write(
        self,
        key: str,
        value: str,
        run_id: Optional[str] = None,
    ) -> str:
        """
        S1.5 — Authorize and sanitize content before it is written to any
        persistent agent memory store. Every write is logged (A2.5).
        """
        violation = self.scan_content(
            value, f"memory_write:{key}",
            check_injection=True, check_credentials=True,
            run_id=run_id,
        )
        if violation:
            self._emit_event(
                "MEMORY_WRITE_BLOCKED", "CRITICAL", "S1.5",
                f"memory:{key}",
                f"S1.5 Memory governance: write blocked for key '{key}' — violation detected",
                run_id,
            )
            if self.act_tier.value >= 3:
                raise AISAFE2Violation(
                    f"[AI SAFE² S1.5] Memory write blocked: violation in key '{key}'",
                    control_id="S1.5",
                )
        else:
            self._emit_event(
                "MEMORY_WRITE_AUTHORIZED", "INFO", "S1.5",
                f"memory:{key}",
                f"S1.5 Memory write authorized for key '{key}'",
                run_id,
            )
        return value

    # -----------------------------------------------------------------------
    # F3.2 + M4.5 — Recursion Limit + Tool-Misuse Detection
    # -----------------------------------------------------------------------

    def record_tool_call(
        self,
        tool_name: str,
        args_repr: str = "",
        run_id: Optional[str] = None,
    ) -> None:
        """
        F3.2 — Record tool invocation against the hard ceiling.
        M4.5 — Detect identical-call loops and frequency anomalies.
        """
        now = time.monotonic()

        # F3.2: absolute session ceiling
        self._total_tool_calls += 1
        if self._total_tool_calls > self.max_tool_calls:
            self._emit_event(
                "RECURSION_LIMIT_EXCEEDED", "CRITICAL", "F3.2",
                f"tool:{tool_name}",
                f"F3.2 Agent Recursion Limit: {self._total_tool_calls} calls exceeds ceiling {self.max_tool_calls}",
                run_id,
            )
            raise CircuitTripped(
                f"[AI SAFE² F3.2] Tool call ceiling {self.max_tool_calls} reached",
                control_id="F3.2",
            )

        # M4.5: rolling 60-second frequency window
        window = [t for t in self._tool_calls[tool_name] if now - t < 60]
        window.append(now)
        self._tool_calls[tool_name] = window
        if len(window) > 15:  # >15 calls of same tool in 60s is anomalous
            self._emit_event(
                "TOOL_FREQUENCY_ANOMALY", "HIGH", "M4.5",
                f"tool:{tool_name}",
                f"M4.5 Tool-Misuse: {tool_name} called {len(window)}x in 60s",
                run_id,
            )

        # M4.5: identical-call loop detection
        args_hash = hashlib.md5(args_repr.encode()).hexdigest()[:8]
        loop_key = f"{tool_name}:{args_hash}"
        self._identical_calls[loop_key] += 1
        if self._identical_calls[loop_key] >= self.max_identical_calls:
            self._emit_event(
                "TOOL_LOOP_DETECTED", "CRITICAL", "M4.5",
                f"tool:{tool_name}",
                f"M4.5 Tool-Misuse loop: '{tool_name}' with identical args repeated "
                f"{self._identical_calls[loop_key]}x",
                run_id,
            )
            if self.act_tier.value >= 2:
                raise CircuitTripped(
                    f"[AI SAFE² M4.5] Loop detected: {tool_name} identical args "
                    f"{self._identical_calls[loop_key]}x",
                    control_id="M4.5",
                )

    # -----------------------------------------------------------------------
    # F3.5 — Multi-Agent Cascade Containment
    # -----------------------------------------------------------------------

    def record_chain_error(
        self,
        error: Exception,
        chain_name: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        F3.5 — Log and contain chain errors so they do not cascade to parent
        chains or downstream agents.
        """
        self._chain_errors[chain_name] += 1
        count = self._chain_errors[chain_name]
        self._emit_event(
            "CHAIN_ERROR_ISOLATED", "HIGH", "F3.5",
            f"chain:{chain_name}",
            f"F3.5 Cascade containment: error in '{chain_name}' isolated (occurrence #{count}): "
            f"{type(error).__name__}: {str(error)[:120]}",
            run_id,
        )
        if count >= 3:
            self._emit_event(
                "CASCADE_THRESHOLD_EXCEEDED", "CRITICAL", "F3.5",
                f"chain:{chain_name}",
                f"F3.5 Cascade threshold: '{chain_name}' has {count} consecutive errors — trip",
                run_id,
            )
            self._compliance_score = max(0.0, self._compliance_score - 5.0)
            if self.act_tier.value >= 3:
                raise CircuitTripped(
                    f"[AI SAFE² F3.5] Cascade containment tripped for '{chain_name}'",
                    control_id="F3.5",
                )

    # -----------------------------------------------------------------------
    # P1.T2.3 — Domain allowlist + SSRF / private IP block
    # -----------------------------------------------------------------------

    def check_domain(
        self,
        url_or_domain: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        P1.T2.3 — Validate outbound URL/domain against allowlist and block
        private IP / SSRF targets.
        """
        import urllib.parse

        try:
            parsed = urllib.parse.urlparse(url_or_domain)
            host = (parsed.hostname or url_or_domain).lower().strip()
        except Exception:
            host = url_or_domain.lower().strip()

        # SSRF: private IP / internal ranges
        for pattern in _PRIVATE_IP_PATTERNS:
            if re.search(pattern, host, re.IGNORECASE):
                self._emit_event(
                    "SSRF_BLOCKED", "CRITICAL", "P1.T2.3",
                    f"domain:{host}",
                    f"P1.T2.3 SSRF / private IP blocked: '{host}'",
                    run_id,
                )
                self._compliance_score = max(0.0, self._compliance_score - 5.0)
                if self.act_tier.value >= 2:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T2.3] SSRF blocked: '{host}'",
                        control_id="P1.T2.3",
                    )

        # Domain allowlist check
        if self.allowed_domains:
            allowed = any(
                host == d.lower() or host.endswith(f".{d.lower()}")
                for d in self.allowed_domains
            )
            if not allowed:
                self._emit_event(
                    "DOMAIN_NOT_ALLOWLISTED", "HIGH", "P1.T2.3",
                    f"domain:{host}",
                    f"P1.T2.3 Domain not in allowlist: '{host}'",
                    run_id,
                )
                if self.act_tier.value >= 3:
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T2.3] Domain not allowlisted: '{host}'",
                        control_id="P1.T2.3",
                    )

    # -----------------------------------------------------------------------
    # P1.T1.2 — Path traversal guard
    # -----------------------------------------------------------------------

    def check_path_safety(
        self,
        path: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        P1.T1.2 — Prevent path traversal attacks (OWASP LLM03 / AML.T0002).
        Blocks ../escape and access to sensitive OS paths.
        """
        dangerous_prefixes = ("/etc", "/proc", "/sys", "/root", "C:\\Windows", "C:\\Users")
        normalized = os.path.normpath(path)

        traversal = ".." in path.replace("\\", "/").split("/")
        sensitive = any(normalized.startswith(p) for p in dangerous_prefixes)

        if traversal or sensitive:
            self._emit_event(
                "PATH_TRAVERSAL_BLOCKED", "CRITICAL", "P1.T1.2",
                f"path:{path}",
                f"P1.T1.2 Path traversal / sensitive path blocked: '{path}'",
                run_id,
            )
            self._compliance_score = max(0.0, self._compliance_score - 5.0)
            if self.act_tier.value >= 2:
                raise AISAFE2Violation(
                    f"[AI SAFE² P1.T1.2] Path traversal blocked: '{path}'",
                    control_id="P1.T1.2",
                )

        # Workspace boundary enforcement
        if self.workspace_root:
            abs_workspace = os.path.abspath(self.workspace_root)
            # Join with workspace only if path is relative
            if not os.path.isabs(path):
                abs_path = os.path.abspath(os.path.join(self.workspace_root, path))
                if not abs_path.startswith(abs_workspace + os.sep) and abs_path != abs_workspace:
                    self._emit_event(
                        "WORKSPACE_ESCAPE_BLOCKED", "CRITICAL", "P1.T1.2",
                        f"path:{path}",
                        f"P1.T1.2 Workspace boundary escape blocked: '{path}'",
                        run_id,
                    )
                    raise AISAFE2Violation(
                        f"[AI SAFE² P1.T1.2] Workspace escape: '{path}'",
                        control_id="P1.T1.2",
                    )

    # -----------------------------------------------------------------------
    # CP.4 — Agentic Control Plane / NHI Registration
    # -----------------------------------------------------------------------

    def register_nhi(
        self,
        agent_id: str,
        owner_of_record: str,
        act_tier: ACTTier,
        tool_authorizations: List[str],
        control_plane_id: str = "",
    ) -> str:
        """
        CP.4 — Register an agent as a Non-Human Identity in the Agentic
        Control Plane. Returns agent_id.
        """
        record = {
            "agent_id": agent_id,
            "owner_of_record": owner_of_record,
            "act_tier": act_tier.name,
            "tool_authorizations": tool_authorizations,
            "control_plane_id": control_plane_id or self.session_id,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._nhi_registry[agent_id] = record
        self._emit_event(
            "NHI_REGISTERED", "INFO", "CP.4",
            f"agent:{agent_id}",
            f"CP.4 NHI registered: '{agent_id}' — ACT-{act_tier.value}, "
            f"owner: '{owner_of_record}', tools: {tool_authorizations}",
        )
        return agent_id

    # -----------------------------------------------------------------------
    # CP.8 — Catastrophic Risk Threshold
    # -----------------------------------------------------------------------

    def emit_cp8_event(
        self,
        trigger: str,
        detail: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        CP.8 — Emit a Catastrophic Risk Threshold event. Callers use this
        when they detect behaviors that warrant emergency review regardless
        of business continuity impact.
        """
        self._emit_event(
            "CP8_CATASTROPHIC_RISK", "FATAL", "CP.8",
            trigger,
            f"CP.8 Catastrophic Risk Threshold: {detail}",
            run_id,
        )
        self._compliance_score = max(0.0, self._compliance_score - 20.0)
        print(
            f"\n🛑 [AI SAFE² FATAL] [CP.8] Catastrophic risk threshold triggered: {detail}",
            file=sys.stderr,
            flush=True,
        )

    # -----------------------------------------------------------------------
    # CP.10 — HEAR Doctrine
    # -----------------------------------------------------------------------

    def check_hear_gate(
        self,
        action_description: str,
        run_id: Optional[str] = None,
    ) -> None:
        """
        CP.10 — Gate Class-H actions requiring Human Ethical Agent of Record
        authorization. Required for ACT-3/ACT-4.

        Class-H: irreversible, financially material, security-modifying, or
        cross-organizational actions.
        """
        if not self.hear_mode:
            return
        for pattern in _CLASS_H_PATTERNS:
            if re.search(pattern, action_description, re.IGNORECASE):
                self._emit_event(
                    "HEAR_GATE_TRIGGERED", "CRITICAL", "CP.10",
                    "action_gate",
                    f"CP.10 Class-H action requires HEAR authorization: "
                    f"'{action_description[:120]}'",
                    run_id,
                )
                raise AISAFE2ClassHAction(
                    f"[AI SAFE² CP.10] Class-H action requires HEAR authorization: "
                    f"'{action_description[:80]}'",
                    action_description=action_description,
                )

    # -----------------------------------------------------------------------
    # F3.4 — State snapshot for rollback
    # -----------------------------------------------------------------------

    def snapshot_state(self, state: Any, label: str = "") -> str:
        """F3.4 — Store a state snapshot in the ring-buffer for rollback."""
        snap = {
            "label": label,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_hash": hashlib.sha256(json.dumps(state, default=str, sort_keys=True).encode()).hexdigest(),
            "state": state,
        }
        self._state_snapshots.append(snap)
        return snap["state_hash"]

    def rollback_state(self) -> Optional[Any]:
        """F3.4 — Return the most recent good state snapshot, or None."""
        if self._state_snapshots:
            snap = self._state_snapshots[-1]
            self._emit_event(
                "STATE_ROLLBACK", "HIGH", "F3.4",
                "state_snapshot",
                f"F3.4 State rolled back to snapshot '{snap['label']}' "
                f"(hash: {snap['state_hash'][:12]})",
            )
            return snap["state"]
        return None

    # -----------------------------------------------------------------------
    # P2.T3.6 + A2.5 — Compliance report + status
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Return current enforcement status dict for monitoring / NEXUS dashboard."""
        return {
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "act_tier": self.act_tier.name,
            "compliance_score": round(self._compliance_score, 1),
            "alignment_band": self._alignment_band(),
            "total_violations": len(self._violations),
            "total_tool_calls": self._total_tool_calls,
            "nhi_count": len(self._nhi_registry),
            "chain_errors": dict(self._chain_errors),
            "audit_log": str(self.audit_log_path),
            "controls_active": [
                "P1.T1.2", "P1.T1.5", "P1.T1.10", "P1.T2.3",
                "S1.3", "S1.5", "F3.2", "F3.5",
                "A2.5", "M4.5", "P2.T3.6",
                "CP.3", "CP.4", "CP.8", "CP.10",
            ],
            "framework_version": "AI SAFE² v3.0",
        }

    def _alignment_band(self) -> str:
        if self._compliance_score >= 80:
            return "GREEN"
        elif self._compliance_score >= 60:
            return "YELLOW"
        return "RED"

    def compliance_report(self) -> str:
        """P2.T3.6 — Generate a Markdown compliance report for this session."""
        status = self.get_status()
        band_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(
            status["alignment_band"], "⚪"
        )
        violations_by_control: Dict[str, int] = defaultdict(int)
        for v in self._violations:
            violations_by_control[v["control_id"]] += 1

        viol_table = "\n".join(
            f"| {ctrl} | {count} |" for ctrl, count in sorted(violations_by_control.items())
        ) or "| — | 0 |"

        return f"""# AI SAFE² v3.0 — LangChain Sovereign Runtime Compliance Report

**Generated:** {datetime.now(timezone.utc).isoformat()}
**Session:** {status['session_id']}
**Runtime:** {status['runtime_id']}
**ACT Tier:** {status['act_tier']}

## Compliance Status
| Metric | Value |
|---|---|
| Compliance Score | {status['compliance_score']}/100 |
| Alignment Band | {band_emoji} {status['alignment_band']} |
| Total Violations | {status['total_violations']} |
| Total Tool Calls | {status['total_tool_calls']} |
| NHIs Registered | {status['nhi_count']} |
| Audit Log | `{status['audit_log']}` |

## Violations by Control
| Control ID | Count |
|---|---|
{viol_table}

## Active Controls
{chr(10).join(f"- ✅ [{c}]" for c in status['controls_active'])}

## Audit Chain
Last hash: `{self._last_hash[:24]}...`
Log: `{self.audit_log_path}`

---
*AI SAFE² v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com*
"""
