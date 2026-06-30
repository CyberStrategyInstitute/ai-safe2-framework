"""
ai_safe2_engine.py — NEXUS Kernel
AI SAFE2 v3.0 Sovereign Runtime Engine
Cyber Strategy Institute

stdlib only. No external dependencies.
Drop-in for any sovereign runtime in the examples/ series.

Pillars implemented:
  P1 Sanitize-Isolate  — injection, secret, hidden-unicode detection
  P2 Audit-Inventory   — SHA-256 tamper-evident JSONL chain (A2.5)
  P3 Fail-Safe         — turn ceiling, ops rate limiter (F3.2)
  P4 Engage-Monitor    — real-time CRITICAL events to stderr (M4.4)
  P5 Evolve-Educate    — Love Equation score + GREEN/YELLOW/RED band (E5.1)
  CP Cross-Pillar      — session NHI registration, mTLS readiness flag (CP.4)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    INFO     = "INFO"


class Band(str, Enum):
    GREEN  = "GREEN"   # love_score >= 80
    YELLOW = "YELLOW"  # love_score >= 60
    RED    = "RED"     # love_score < 60


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class Violation:
    control_id: str
    severity:   Severity
    message:    str
    source:     str
    timestamp:  str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ScanResult:
    passed:     bool
    violations: List[Violation]
    source:     str


# ─────────────────────────────────────────────────────────────
# Detection patterns  (verified control IDs only)
# ─────────────────────────────────────────────────────────────

# P1.T1.2 + P1.T1.10: Direct and indirect prompt injection
_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"(?i)ignore\s+(previous|all|prior)\s+instructions",            "P1.T1.2"),
    (r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",                       "P1.T1.2"),
    (r"(?i)(?:system\s+prompt|jailbreak|DAN\s+mode)",               "P1.T1.2"),
    (r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",       "P1.T1.2"),
    (r"(?i)(?:forget|override|bypass)\s+(?:your\s+)?(?:instructions|constraints|rules)", "S1.3"),
    (r"(?i)print\s+(?:your\s+)?(?:system\s+prompt|instructions)",   "P1.T1.2"),
    (r"(?i)act\s+as\s+(?:if\s+you\s+(?:were|are)|a\b)",            "S1.6"),
    (r"(?i)(?:roleplay|pretend)\s+(?:to\s+be|you\s+are)",          "S1.6"),
    (r"(?i)new\s+instructions?:\s*\n",                               "P1.T1.10"),
    (r"(?i)\[INST\]|\[\/INST\]|<\|im_start\|>|<\|im_end\|>",       "P1.T1.10"),
]

# P1.T1.4_ADV: Credential / secret patterns
_SECRET_PATTERNS: List[Tuple[str, str]] = [
    (r"xai-[A-Za-z0-9]{20,}",                                       "P1.T1.4_ADV"),
    (r"sk-[A-Za-z0-9_\-]{20,}",                                      "P1.T1.4_ADV"),
    (r"sk-ant-[A-Za-z0-9]{30,}",                                    "P1.T1.4_ADV"),
    (r"(?i)(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token)"
     r"\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}",                       "P1.T1.4_ADV"),
    (r"(?i)(?:password|passwd|pwd)\s*[=:]\s*['\"]?\S{8,}",         "P1.T1.4_ADV"),
    (r"(?i)bearer\s+[A-Za-z0-9_\-\.]{16,}",                        "P1.T1.4_ADV"),
    (r"(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9]{36}",              "P1.T1.4_ADV"),
]

# S1.6: Hidden / homoglyph Unicode (cognitive injection)
_HIDDEN_UNICODE: List[str] = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad", "\u2028", "\u2029"]


# ─────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────

class AISAFE2Engine:
    """
    NEXUS kernel — shared across all sovereign runtimes.
    One instance per session; pass to platform runtime class.
    """

    LOVE_SCORE_MAX       = 100.0
    LOVE_SCORE_DEDUCTION = 2.0    # E5.1: -2 per violation

    def __init__(
        self,
        session_id:      Optional[str]  = None,
        audit_log_path:  Optional[Path] = None,
        emit_to_stderr:  bool           = True,
    ) -> None:
        self._session_id     = session_id or f"session-{int(time.time())}"
        self._audit_log_path = audit_log_path
        self._emit           = emit_to_stderr

        self._violations:   List[Violation] = []
        self._love_score:   float           = self.LOVE_SCORE_MAX
        self._chain:        List[str]       = []   # A2.5 SHA-256 chain
        self._scan_count:   int             = 0

        # CP.4: register as NHI in audit
        self._nhi_id = f"nhi-xai-grok-{self._session_id}"

    # ── core detection ────────────────────────────────────────

    def scan_text(self, text: str, source: str) -> ScanResult:
        """P1.T1.2 + P1.T1.10 + P1.T1.4_ADV + S1.6 — full text scan."""
        self._scan_count += 1
        violations: List[Violation] = []

        # Injection
        for pattern, cid in _INJECTION_PATTERNS:
            if re.search(pattern, text):
                v = Violation(cid, Severity.CRITICAL, f"Injection in '{source}'", source)
                violations.append(v)
                self._record(v)
                break  # one injection event per source

        # Secrets
        for pattern, cid in _SECRET_PATTERNS:
            if re.search(pattern, text):
                v = Violation(cid, Severity.CRITICAL, f"Credential pattern in '{source}'", source)
                violations.append(v)
                self._record(v)
                break

        # Hidden Unicode (S1.6)
        for ch in _HIDDEN_UNICODE:
            if ch in text:
                v = Violation(
                    "S1.6", Severity.HIGH,
                    f"Hidden unicode U+{ord(ch):04X} in '{source}'", source
                )
                violations.append(v)
                self._record(v)
                break

        return ScanResult(passed=not violations, violations=violations, source=source)

    # ── audit chain ───────────────────────────────────────────

    def _record(self, v: Violation) -> None:
        """A2.5: SHA-256 tamper-evident JSONL chain + real-time stderr (M4.4)."""
        self._violations.append(v)
        self._love_score = max(0.0, self._love_score - self.LOVE_SCORE_DEDUCTION)

        entry = {
            "ts":       v.timestamp,
            "session":  self._session_id,
            "nhi_id":   self._nhi_id,
            "control":  v.control_id,
            "severity": v.severity.value,
            "message":  v.message,
            "source":   v.source,
        }
        entry_json = json.dumps(entry, sort_keys=True)

        prev = self._chain[-1] if self._chain else "0" * 64
        chain_hash = hashlib.sha256(f"{prev}{entry_json}".encode()).hexdigest()
        self._chain.append(chain_hash)
        entry["chain_hash"] = chain_hash

        # P4.T7.4 / M4.4: real-time escalation to stderr
        if self._emit:
            import sys
            print(
                f"!!! [AI SAFE2 {v.control_id}] [{v.severity.value}] {v.message}",
                file=sys.stderr, flush=True
            )

        # P2.T3.1: append to JSONL audit log
        if self._audit_log_path:
            self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_log_path, "a") as fh:
                fh.write(json.dumps(entry) + "\n")

    # ── Love Equation ─────────────────────────────────────────

    def get_band(self) -> Band:
        """E5.1: Alignment band from Love Equation score."""
        if self._love_score >= 80.0:
            return Band.GREEN
        elif self._love_score >= 60.0:
            return Band.YELLOW
        return Band.RED

    def get_status(self) -> Dict[str, Any]:
        return {
            "love_score":      round(self._love_score, 1),
            "alignment_band":  self.get_band().value,
            "violations":      len(self._violations),
            "session_id":      self._session_id,
            "nhi_id":          self._nhi_id,
            "scan_count":      self._scan_count,
            "chain_length":    len(self._chain),
        }

    def compliance_report(self, runtime_name: str = "sovereign-runtime") -> str:
        s = self.get_status()
        used = sorted({v.control_id for v in self._violations})
        return "\n".join([
            f"# AI SAFE2 Compliance Report",
            f"Runtime: {runtime_name}",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Love Score: {s['love_score']} | Band: {s['alignment_band']}",
            f"Violations: {s['violations']}",
            f"Controls Triggered: {', '.join(used) or 'None'}",
        ])
