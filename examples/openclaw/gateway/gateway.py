#!/usr/bin/env python3
"""
AI SAFE² Control Gateway for OpenClaw — v3.0
═══════════════════════════════════════════════════════════════════════════════
AI enforcement proxy implementing the full AI SAFE² v3.0 governance stack.
Supports multiple LLM providers via a pass-through adapter architecture.
NEXUS-A2A v0.2 compatible: envelope detection, identity passthrough, NEXUS-aware
A2A detection. Full NEXUS enforcement is a NEXUS runtime concern.

Supported providers: anthropic | openai | gemini | ollama | openrouter
Active provider set via config.yaml → provider.active

Architecture (separation of concerns):
  OpenClaw (tactical execution) ──► [This Gateway] ──► Active LLM Provider
                                           │
                          ┌────────────────┴─────────────────┐
                          │         Governance Stack           │
                          │  P1: 3-Vector Risk Scoring         │
                          │  P2: 4-Tier HITL Circuit Breaker   │
                          │  P3: HMAC-Chained Immutable Audit  │
                          │  P4: Heartbeat Liveness Monitor    │
                          │  P5: A2A Impersonation Detection   │
                          │  P6: Token-Bucket Rate Limiting    │
                          │  P7: Outbound Response Scanning    │
                          └───────────────────────────────────┘

Bug #11766 (HEARTBEAT.md silent auto-creation) is addressed at line ~180.
The file is NEVER created automatically during normal operation.
A missing, empty, or stale heartbeat file triggers:
  1. CRITICAL log event
  2. Safe mode activation
  3. Rejection of all non-health requests
  4. Alert dispatch (if webhook configured)

Usage:
    python3 gateway.py
    python3 gateway.py --config custom_config.yaml --port 9000
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    from flask import Flask, Response, jsonify, request
    import requests as http_requests
    from jsonschema import ValidationError, validate
    import yaml
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip3 install flask requests jsonschema pyyaml")
    sys.exit(1)

# Provider adapter layer (multi-provider + NEXUS-A2A compatibility)
try:
    from provider_adapters import (
        get_adapter, list_providers, extract_nexus_audit_fields,
        NEXUS_A2A_INDICATORS, NormalizedRequest,
    )
    _ADAPTERS_AVAILABLE = True
except ImportError:
    _ADAPTERS_AVAILABLE = False
    logger_bootstrap = logging.getLogger(__name__)
    logger_bootstrap.warning(
        "provider_adapters.py not found — falling back to Anthropic-only mode. "
        "Place provider_adapters.py in the same directory as gateway.py."
    )

# ─── Version ──────────────────────────────────────────────────────────────────
GATEWAY_VERSION = "3.0.0"
FRAMEWORK_REF   = "AI SAFE² v3.0"
GENESIS_HASH    = hashlib.sha256(b"GENESIS:SAFE2:v3.0:OPENCLAW").hexdigest()[:16]  # 16 hex chars; regex-safe

# ─── Module-level state (initialized in main()) ────────────────────────────
CONFIG: dict = {}
SCHEMAS: dict = {}
_safe_mode_active = threading.Event()
_safe_mode_reason = ""
_safe_mode_ts = ""

# ─── Logging ──────────────────────────────────────────────────────────────────
logger = logging.getLogger("aisafe2.openclaw")


# ═══════════════════════════════════════════════════════════════════════════════
# §1  ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class HITLTier(str, Enum):
    AUTO     = "AUTO"      # 0–3:  log and pass
    MEDIUM   = "MEDIUM"    # 4–6:  require X-HITL-Token
    HIGH     = "HIGH"      # 7–8:  require token + written reason ≥20 chars
    CRITICAL = "CRITICAL"  # >8:   out-of-band 2FA challenge-response


# ═══════════════════════════════════════════════════════════════════════════════
# §2  HEARTBEAT MONITOR  — Bug #11766 mitigation
# ═══════════════════════════════════════════════════════════════════════════════

class HeartbeatMonitor:
    """
    Validates HEARTBEAT.md presence, content, and freshness.

    CONTRACT:
      - validate() returns (False, reason) for ANY failure condition
      - The gateway MUST enter safe mode on (False, _)
      - write_beat() is the ONLY code path that writes to HEARTBEAT.md
      - initialize() writes ONCE on very first run; never during operation
      - Background cron/scheduler tasks MUST call validate() before executing

    Why this matters (Bug #11766):
      The old behavior let the model decide what to do if HEARTBEAT.md was
      missing. It silently created an empty file, disabling monitoring entirely.
      Operators saw a green dashboard while background jobs were dead.
      This class eliminates that failure mode by enforcing strict validation
      before any write and never delegating the decision to the agent.
    """

    HEARTBEAT_FORMAT = re.compile(
        r"^ALIVE:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?):([a-f0-9]{16})$"
    )

    def __init__(self, path: str, max_staleness_seconds: int = 120):
        self.path = Path(path)
        self.max_staleness = max_staleness_seconds
        self._lock = threading.Lock()
        self._last_write_hash: str = GENESIS_HASH

    def validate(self) -> tuple[bool, str]:
        """
        Validate heartbeat file. NEVER modifies the file.
        Returns (is_valid, reason). Treat is_valid=False as a hard stop.
        """
        with self._lock:
            # 1. Existence — hard fail, never create
            if not self.path.exists():
                return (
                    False,
                    f"HEARTBEAT.md not found at '{self.path}'. "
                    f"Possible silent monitoring failure (Bug #11766). "
                    f"Run `python3 gateway.py --init-heartbeat` to create."
                )

            # 2. Non-empty
            content = self.path.read_text(encoding="utf-8").strip()
            if not content:
                return (
                    False,
                    "HEARTBEAT.md exists but is EMPTY. "
                    "This is exactly the Bug #11766 failure mode. "
                    "Delete the file and restart to reinitialize."
                )

            # 3. Read the last (most recent) non-empty line
            last_line = content.splitlines()[-1].strip()

            # 4. Format validation
            match = self.HEARTBEAT_FORMAT.match(last_line)
            if not match:
                return (
                    False,
                    f"HEARTBEAT.md last line malformed: '{last_line[:80]}'. "
                    f"Expected: ALIVE:<ISO-timestamp>:<prev_hash_16>"
                )

            # 5. Staleness check
            ts_str, _ = match.group(1), match.group(2)
            try:
                last_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if last_ts.tzinfo is None:
                    last_ts = last_ts.replace(tzinfo=timezone.utc)
                age_seconds = (datetime.now(timezone.utc) - last_ts).total_seconds()
                if age_seconds > self.max_staleness:
                    return (
                        False,
                        f"HEARTBEAT.md is stale: last write was {int(age_seconds)}s ago "
                        f"(max allowed: {self.max_staleness}s). Background monitor may have crashed."
                    )
            except (ValueError, OverflowError) as e:
                return False, f"HEARTBEAT.md timestamp parse error: {e}"

            return True, "OK"

    def write_beat(self, prev_hash: str) -> None:
        """
        Write a new heartbeat entry. ONLY called by the gateway's own
        background thread — never by the agent or external code.
        """
        with self._lock:
            ts = datetime.now(timezone.utc).isoformat()
            entry = f"ALIVE:{ts}:{prev_hash[:16]}"
            # Append (not overwrite) so history is preserved for forensics
            with self.path.open("a", encoding="utf-8") as f:
                f.write(entry + "\n")
                f.flush()
                os.fsync(f.fileno())
            self._last_write_hash = hashlib.sha256(entry.encode()).hexdigest()

    def initialize_once(self) -> None:
        """
        Initialize HEARTBEAT.md on first run ONLY.
        If the file exists but is invalid, raises RuntimeError — do NOT overwrite.
        """
        if self.path.exists():
            valid, reason = self.validate()
            if not valid:
                raise RuntimeError(
                    f"HEARTBEAT.md exists but is invalid: {reason}\n"
                    f"Investigate before proceeding. Do not auto-overwrite."
                )
            logger.info("HEARTBEAT.md already valid — skipping initialization")
            return

        logger.info("First run: initializing HEARTBEAT.md at %s", self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.write_beat(GENESIS_HASH)
        logger.info("HEARTBEAT.md initialized")


# ═══════════════════════════════════════════════════════════════════════════════
# §3  IMMUTABLE AUDIT LOG  (HMAC-SHA256 chained JSONL)
# ═══════════════════════════════════════════════════════════════════════════════

class ImmutableAuditLog:
    """
    Every gateway decision is recorded as a cryptographically linked entry.

    Chain structure:
      entry_hash = HMAC-SHA256(AUDIT_CHAIN_KEY, "{prev_hash}|{entry_json_sorted}")

    Properties:
      - Append-only: no delete API
      - Tamper-evident: any modification to entry N breaks the chain at N+1
      - Physically external: runs outside OpenClaw's process (architectural separation)
      - Process-persistent: chain state survives across requests via file

    The chain secret (AUDIT_CHAIN_KEY env var) must be:
      - Generated once: openssl rand -hex 32
      - Stored in a secrets manager, NOT in config.yaml
      - Separate from the Anthropic API key
    """

    def __init__(self, log_path: str, chain_key: str):
        self.log_path = Path(log_path)
        self._key = chain_key.encode("utf-8")
        self._lock = threading.RLock()
        self._seq: int = 0
        self._last_hash: str = GENESIS_HASH
        self._load_chain_state()

    def _compute_hash(self, prev_hash: str, entry_json: str) -> str:
        msg = f"{prev_hash}|{entry_json}".encode("utf-8")
        return hmac.new(self._key, msg, hashlib.sha256).hexdigest()

    def _load_chain_state(self) -> None:
        """Restore seq and last_hash from existing log without full verification."""
        if not self.log_path.exists():
            return
        try:
            with self.log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    self._seq = entry.get("seq", self._seq)
                    self._last_hash = entry.get("entry_hash", self._last_hash)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Could not load chain state: %s", e)

    def verify_chain(self) -> tuple[bool, int, str]:
        """
        Full chain verification. Should run on startup and via scanner.py.
        Returns (is_valid, entries_verified, detail).
        """
        if not self.log_path.exists():
            return True, 0, "No log file yet (first run)"

        prev_hash = GENESIS_HASH
        count = 0
        try:
            with self.log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    stored_hash = entry.pop("entry_hash", "")
                    canonical = json.dumps(entry, sort_keys=True)
                    expected = self._compute_hash(prev_hash, canonical)
                    if not hmac.compare_digest(stored_hash, expected):
                        return False, count, f"Chain break at seq={entry.get('seq', '?')}: stored={stored_hash[:12]} expected={expected[:12]}"
                    prev_hash = stored_hash
                    count += 1
        except (json.JSONDecodeError, OSError) as e:
            return False, count, f"Verification error: {e}"

        return True, count, "OK"

    def append(
        self,
        *,
        user_id: str,
        request_hash: str,
        risk_score: float,
        risk_vectors: dict,
        hitl_tier: str,
        blocked: bool,
        reason: Optional[str],
        tokens_used: int = 0,
        extra: Optional[dict] = None,
    ) -> str:
        """Append a tamper-evident audit entry. Returns the entry hash."""
        with self._lock:
            self._seq += 1
            entry: dict[str, Any] = {
                "seq": self._seq,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "gateway_version": GATEWAY_VERSION,
                "framework": FRAMEWORK_REF,
                "user_id": user_id,
                "request_hash": request_hash,
                "risk_score": round(risk_score, 4),
                "risk_vectors": risk_vectors,
                "hitl_tier": hitl_tier,
                "blocked": blocked,
                "reason": reason,
                "tokens_used": tokens_used,
                **(extra or {}),
            }
            canonical = json.dumps(entry, sort_keys=True)
            entry_hash = self._compute_hash(self._last_hash, canonical)
            entry["entry_hash"] = entry_hash

            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                os.fsync(f.fileno())

            self._last_hash = entry_hash
            logger.info(
                "AUDIT seq=%d user=%s score=%.2f tier=%s blocked=%s hash=%s",
                self._seq, user_id, risk_score, hitl_tier, blocked, entry_hash[:12],
            )
            return entry_hash

    @property
    def last_hash(self) -> str:
        with self._lock:
            return self._last_hash


# ═══════════════════════════════════════════════════════════════════════════════
# §4  RATE LIMITER  (token bucket per identity)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenBucketRateLimiter:
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self._rpm = requests_per_minute
        self._rph = requests_per_hour
        self._minute_windows: dict[str, list] = defaultdict(list)
        self._hour_windows: dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, identity: str) -> bool:
        now = time.monotonic()
        with self._lock:
            # Evict stale timestamps
            min_window = self._minute_windows[identity]
            while min_window and min_window[0] < now - 60:
                min_window.pop(0)
            hr_window = self._hour_windows[identity]
            while hr_window and hr_window[0] < now - 3600:
                hr_window.pop(0)

            if len(min_window) >= self._rpm:
                return False
            if len(hr_window) >= self._rph:
                return False

            min_window.append(now)
            hr_window.append(now)
            return True


# ═══════════════════════════════════════════════════════════════════════════════
# §5  HISTORICAL CONTEXT TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

class HistoricalContextTracker:
    """
    Tracks per-(user, action_fingerprint) frequency.
    Third risk vector: 10=never seen, 5=rare (<5 times), 0=frequent.
    Persisted across restarts via JSON file.
    """

    def __init__(self, persist_path: str = "data/action_history.json"):
        self._path = Path(persist_path)
        self._lock = threading.Lock()
        self._counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                for uid, actions in raw.items():
                    self._counts[uid] = defaultdict(int, actions)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps({k: dict(v) for k, v in self._counts.items()}))
        tmp.replace(self._path)  # atomic rename

    def score_and_record(self, user_id: str, fingerprint: str) -> float:
        """Returns historical score (0, 5, or 10) and increments counter."""
        with self._lock:
            count = self._counts[user_id][fingerprint]
            score = 10.0 if count == 0 else (5.0 if count < 5 else 0.0)
            self._counts[user_id][fingerprint] += 1
            self._save()
            return score


# ═══════════════════════════════════════════════════════════════════════════════
# §6  RISK SCORER  (3-vector: action × sensitivity × history)
# ═══════════════════════════════════════════════════════════════════════════════

ACTION_SCORES: dict[str, float] = {
    # Read tier (0)
    "read": 0, "search": 0, "retrieve": 0, "list": 0, "get": 0,
    "fetch": 0, "view": 0, "describe": 0,
    # Write tier (5)
    "write": 5, "create": 5, "update": 5, "edit": 5, "apply_patch": 5,
    "canvas": 5, "upload": 5, "send": 5, "save": 5, "post": 5,
    # Delete/Exec tier (10)
    "delete": 10, "remove": 10, "exec": 10, "execute": 10, "process": 10,
    "run": 10, "cron": 10, "schedule": 10, "browser": 10, "gateway": 10,
    "nodes": 10, "kill": 10, "terminate": 10, "deploy": 10, "drop": 10,
}

SYSTEM_PATHS = re.compile(
    r"(/etc/|/proc/|/sys/|\.ssh/|id_rsa|\.pem|\.key|\.env|"
    r"ANTHROPIC|SECRET|TOKEN|PASSWORD|CREDENTIAL|/root/|/shadow|/passwd)",
    re.IGNORECASE,
)
PERSONAL_PATHS = re.compile(
    r"(\.config/|Documents/|Downloads/|Desktop/|/home/|/users/|personal|private)",
    re.IGNORECASE,
)

INJECTION_PATTERNS = [
    "ignore previous instructions", "ignore all prior instructions",
    "you are now in dan mode", "you are now in unrestricted mode",
    "system: override", "disregard your programming", "forget everything",
    "new instructions from admin", "override safety", "jailbreak",
    "<|im_start|>", "<|im_end|>", "[/inst]", "prompt injection",
    "ignore your training", "act as if you have no restrictions",
]

# A2A detection — NEXUS-aware when adapters available, base indicators otherwise
# NEXUS_A2A_INDICATORS (from provider_adapters) extends this list with
# NEXUS v0.2 canonical message types and identity fields.
A2A_INDICATORS = (
    NEXUS_A2A_INDICATORS if _ADAPTERS_AVAILABLE else [
        "orchestrat", "subagent", "delegate to", "forward to agent",
        "as the orchestrator", "acting as agent", "i am the supervisor",
        "agent-to-agent", "tool_result", "[inst]", "<|im_start|>",
        "from: agent", "x-agent-id", "multi-agent",
    ]
)

SECRET_REDACT_RE = re.compile(
    r"(sk-ant-api\d+-[a-zA-Z0-9_\-]{95}|sk-[a-zA-Z0-9]{48}|"
    r"ghp_[a-zA-Z0-9]{36}|xoxb-[a-zA-Z0-9\-]{10,72}|"
    r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]+ KEY-----)"
)

EXFIL_PATTERNS = re.compile(
    r"(ANTHROPIC_API_KEY|sk-ant-|password|secret|credential|private.?key)",
    re.IGNORECASE,
)
RESPONSE_INJECTION_RE = re.compile(
    r"(ignore previous instructions|override safety|you are now|"
    r"new system prompt|ignore all prior)",
    re.IGNORECASE,
)


def _action_type_score(data: dict) -> float:
    """Score 0 (read), 5 (write), or 10 (delete/exec) — worst tool wins."""
    worst = 0.0
    for tool in data.get("tools", []):
        name = (tool.get("name", "") if isinstance(tool, dict) else str(tool)).lower()
        for key, score in ACTION_SCORES.items():
            if key in name:
                worst = max(worst, score)
    return worst


def _target_sensitivity_score(data: dict) -> float:
    """Score 0 (public), 5 (personal), 10 (system/key) — worst reference wins."""
    worst = 0.0
    all_text = " ".join(
        msg.get("content", "") for msg in data.get("messages", [])
        if isinstance(msg.get("content"), str)
    )
    all_text += json.dumps([t.get("input_schema", {}) if isinstance(t, dict) else {} for t in data.get("tools", [])])

    if SYSTEM_PATHS.search(all_text):
        worst = 10.0
    elif PERSONAL_PATHS.search(all_text):
        worst = 5.0
    return worst


def _check_injection(data: dict) -> Optional[str]:
    """Returns the matched injection pattern or None."""
    all_text = " ".join(
        msg.get("content", "") for msg in data.get("messages", [])
        if isinstance(msg.get("content"), str)
    ).lower()
    system = data.get("system", "").lower()
    combined = all_text + " " + system
    for pattern in INJECTION_PATTERNS:
        if pattern in combined:
            return pattern
    return None


def _check_a2a(data: dict) -> bool:
    """
    A2A impersonation detection.
    Heuristics: assistant-role in user message, orchestration keywords,
    nested tool_result blocks, suspicious X-Agent headers.
    """
    for msg in data.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        cl = content.lower()
        if role == "user" and any(ind in cl for ind in A2A_INDICATORS):
            return True
        if role == "user" and "tool_result" in cl:
            return True
    return False


def calculate_composite_risk(
    data: dict,
    user_id: str,
    hist_tracker: HistoricalContextTracker,
    weights: tuple[float, float, float] = (0.40, 0.35, 0.25),
) -> tuple[float, dict, bool, bool]:
    """
    Returns (composite_score, vector_dict, injection_detected, a2a_detected).
    Scores: 0=read/public/frequent → 10=exec/system/never-seen.
    Modifiers: +5 for injection, +3 for A2A (capped at 10.0).
    """
    a_score = _action_type_score(data)
    t_score = _target_sensitivity_score(data)

    # Historical fingerprint: sorted tool names + truncated system prompt
    fingerprint = ":".join(sorted(
        t.get("name", "") if isinstance(t, dict) else str(t)
        for t in data.get("tools", [])
    )) + "|" + data.get("system", "")[:64]
    h_score = hist_tracker.score_and_record(user_id, fingerprint)

    base = a_score * weights[0] + t_score * weights[1] + h_score * weights[2]

    injection_pattern = _check_injection(data)
    a2a_flagged = _check_a2a(data)

    if injection_pattern:
        base = min(base + 5.0, 10.0)
    if a2a_flagged:
        base = min(base + 3.0, 10.0)

    vector = {
        "action_type": a_score,
        "target_sensitivity": t_score,
        "historical_context": h_score,
        "injection_modifier": 5.0 if injection_pattern else 0.0,
        "a2a_modifier": 3.0 if a2a_flagged else 0.0,
    }

    return round(base, 4), vector, bool(injection_pattern), a2a_flagged


# ═══════════════════════════════════════════════════════════════════════════════
# §7  HITL CIRCUIT BREAKER  (4-tier)
# ═══════════════════════════════════════════════════════════════════════════════

class ChallengeStore:
    """Thread-safe store for pending CRITICAL-tier 2FA challenges."""

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, request_hash: str, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._store[token] = {
                "request_hash": request_hash,
                "user_id": user_id,
                "issued_at": time.monotonic(),
                "used": False,
            }
        return token

    def verify(self, token: str, mac: str, chain_key: bytes) -> tuple[bool, str]:
        """Verify out-of-band 2FA response. Returns (valid, original_request_hash)."""
        with self._lock:
            ch = self._store.get(token)
            if not ch or ch["used"]:
                return False, ""
            if time.monotonic() - ch["issued_at"] > self._ttl:
                del self._store[token]
                return False, ""
            expected_mac = hmac.new(chain_key, token.encode(), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(mac, expected_mac):
                return False, ""
            ch["used"] = True
            return True, ch["request_hash"]


class HITLCircuitBreaker:
    """
    4-tier Human-in-the-Loop circuit breaker.

    Tier      Score   Requirement
    ────────  ──────  ─────────────────────────────────────────────────────────
    AUTO      0–3     None — log and approve
    MEDIUM    4–6     X-HITL-Token header (token issued on first attempt)
    HIGH      7–8     X-HITL-Token + X-HITL-Reason (≥20 chars)
    CRITICAL  >8      Out-of-band 2FA: HMAC-SHA256(AUDIT_CHAIN_KEY, token)[:16]
    """

    def __init__(self, gateway_config: dict, challenge_store: ChallengeStore):
        self._cfg = gateway_config
        self._challenges = challenge_store
        self._chain_key = os.environ.get("AUDIT_CHAIN_KEY", "default-change-me").encode()
        self._pending_tokens: dict[str, tuple[str, float]] = {}  # token → (user_id, expiry)
        self._lock = threading.Lock()

    def tier_for_score(self, score: float) -> HITLTier:
        t = self._cfg.get("hitl_thresholds", {})
        if score <= t.get("auto_max", 3.0):
            return HITLTier.AUTO
        elif score <= t.get("medium_max", 6.0):
            return HITLTier.MEDIUM
        elif score <= t.get("high_max", 8.0):
            return HITLTier.HIGH
        return HITLTier.CRITICAL

    def _issue_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(16)
        with self._lock:
            self._pending_tokens[token] = (user_id, time.monotonic() + 300)
        return token

    def _consume_token(self, token: str, user_id: str) -> bool:
        with self._lock:
            if token not in self._pending_tokens:
                return False
            uid, expiry = self._pending_tokens[token]
            if uid != user_id or time.monotonic() > expiry:
                self._pending_tokens.pop(token, None)
                return False
            del self._pending_tokens[token]
            return True

    def enforce(
        self,
        tier: HITLTier,
        req_headers: dict,
        request_hash: str,
        user_id: str,
        risk_score: float,
    ) -> Optional[dict]:
        """
        Returns None if approved, or a response dict (status, body) if blocked.
        """
        if tier == HITLTier.AUTO:
            return None

        if tier == HITLTier.MEDIUM:
            token = req_headers.get("X-Hitl-Token", req_headers.get("X-HITL-Token", ""))
            if not token:
                issued = self._issue_token(user_id)
                return {
                    "status": 403,
                    "body": {
                        "error": "HITL MEDIUM-tier approval required",
                        "tier": "MEDIUM",
                        "risk_score": risk_score,
                        "instruction": "Resubmit with header: X-HITL-Token: <token>",
                        "token": issued,
                        "token_ttl_seconds": 300,
                        "framework": FRAMEWORK_REF,
                    },
                }
            if not self._consume_token(token, user_id):
                return {"status": 403, "body": {"error": "Invalid or expired HITL token", "tier": "MEDIUM"}}
            return None

        if tier == HITLTier.HIGH:
            token = req_headers.get("X-Hitl-Token", req_headers.get("X-HITL-Token", ""))
            reason = req_headers.get("X-Hitl-Reason", req_headers.get("X-HITL-Reason", "")).strip()
            if not token or len(reason) < 20:
                issued = self._issue_token(user_id)
                return {
                    "status": 403,
                    "body": {
                        "error": "HITL HIGH-tier approval required",
                        "tier": "HIGH",
                        "risk_score": risk_score,
                        "instruction": (
                            "Resubmit with: X-HITL-Token: <token> AND "
                            "X-HITL-Reason: <explanation of why this action is necessary (≥20 chars)>"
                        ),
                        "token": issued,
                        "token_ttl_seconds": 300,
                        "framework": FRAMEWORK_REF,
                    },
                }
            if not self._consume_token(token, user_id):
                return {"status": 403, "body": {"error": "Invalid or expired HITL token", "tier": "HIGH"}}
            logger.warning(
                "HITL HIGH approved: user=%s score=%.2f reason='%s'",
                user_id, risk_score, reason[:80]
            )
            return None

        # CRITICAL — 2FA challenge-response
        challenge_header = req_headers.get("X-Hitl-Challenge", req_headers.get("X-HITL-Challenge", ""))
        if not challenge_header:
            token = self._challenges.create(request_hash, user_id)
            logger.critical(
                "CRITICAL HITL challenge issued: user=%s hash=%s token=%s",
                user_id, request_hash[:12], token,
            )
            # In production: dispatch token to webhook/PagerDuty/Slack here
            self._dispatch_challenge_alert(user_id, token, risk_score)
            return {
                "status": 202,
                "body": {
                    "status": "pending_2fa",
                    "tier": "CRITICAL",
                    "risk_score": risk_score,
                    "challenge_token": token,
                    "instruction": (
                        "1. Compute: HMAC-SHA256(AUDIT_CHAIN_KEY, challenge_token)[:16]\n"
                        "2. Resubmit request with header: X-HITL-Challenge: <token>:<mac>"
                    ),
                    "expires_in_seconds": 300,
                    "framework": FRAMEWORK_REF,
                },
            }

        parts = challenge_header.split(":", 1)
        if len(parts) != 2:
            return {"status": 403, "body": {"error": "Malformed X-HITL-Challenge header"}}
        ch_token, mac = parts
        valid, orig_hash = self._challenges.verify(ch_token, mac, self._chain_key)
        if not valid:
            return {"status": 403, "body": {"error": "Invalid or expired 2FA challenge", "tier": "CRITICAL"}}
        if orig_hash != request_hash:
            return {"status": 403, "body": {
                "error": "Request body changed since challenge was issued",
                "detail": "Replay or tampering detected",
            }}
        logger.critical("CRITICAL HITL 2FA approved: user=%s hash=%s", user_id, request_hash[:12])
        return None

    def _dispatch_challenge_alert(self, user_id: str, token: str, score: float) -> None:
        """Send challenge to configured webhook. Fails silently (alert is best-effort)."""
        webhook_url = CONFIG.get("alerts", {}).get("webhook_url", "")
        if not webhook_url:
            return
        try:
            http_requests.post(
                webhook_url,
                json={
                    "alert": "CRITICAL_HITL_CHALLENGE",
                    "user_id": user_id,
                    "challenge_token": token,
                    "risk_score": score,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "Approve via X-HITL-Challenge header or deny",
                    "framework": FRAMEWORK_REF,
                },
                timeout=5,
            )
        except Exception as e:
            logger.error("Alert dispatch failed (non-fatal): %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# §8  RESPONSE SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

def scan_response_body(body: bytes) -> tuple[bool, str]:
    """
    Inspect the Anthropic response for:
      - Secret exfiltration in text content
      - Prompt injection payloads in tool_use blocks
    Returns (is_clean, reason).
    """
    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return True, "non-JSON skipped"

    for block in data.get("content", []):
        if not isinstance(block, dict):
            continue
        block_type = block.get("type", "")

        if block_type == "text":
            if EXFIL_PATTERNS.search(block.get("text", "")):
                return False, "Potential secret exfiltration in response text"

        elif block_type == "tool_use":
            tool_input_str = json.dumps(block.get("input", {}))
            if RESPONSE_INJECTION_RE.search(tool_input_str):
                return False, f"Injection payload in tool_use input for '{block.get('name', '?')}'"
            if EXFIL_PATTERNS.search(tool_input_str):
                return False, f"Potential secret exfiltration in tool_use input"

    return True, "clean"


# ═══════════════════════════════════════════════════════════════════════════════
# §9  SAFE MODE
# ═══════════════════════════════════════════════════════════════════════════════

def activate_safe_mode(reason: str) -> None:
    global _safe_mode_reason, _safe_mode_ts
    _safe_mode_active.set()
    _safe_mode_reason = reason
    _safe_mode_ts = datetime.now(timezone.utc).isoformat()
    logger.critical("=" * 70)
    logger.critical("SAFE MODE ACTIVATED")
    logger.critical("Reason: %s", reason)
    logger.critical("Timestamp: %s", _safe_mode_ts)
    logger.critical("All non-health requests will be rejected.")
    logger.critical("Deactivate via POST /emergency/deactivate-safe-mode with operator key.")
    logger.critical("=" * 70)
    # Dispatch alert
    _send_safe_mode_alert(reason)


def _send_safe_mode_alert(reason: str) -> None:
    webhook = CONFIG.get("alerts", {}).get("webhook_url", "")
    if not webhook:
        return
    try:
        http_requests.post(
            webhook,
            json={
                "alert": "SAFE_MODE_ACTIVATED",
                "reason": reason,
                "timestamp": _safe_mode_ts,
                "framework": FRAMEWORK_REF,
                "action": "IMMEDIATE HUMAN REVIEW REQUIRED",
            },
            timeout=5,
        )
    except Exception as e:
        logger.error("Safe mode alert dispatch failed: %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# §10  FLASK APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Module-level singletons (initialized in main())
_heartbeat_monitor: Optional[HeartbeatMonitor] = None
_audit_log: Optional[ImmutableAuditLog] = None
_rate_limiter: Optional[TokenBucketRateLimiter] = None
_hist_tracker: Optional[HistoricalContextTracker] = None
_hitl: Optional[HITLCircuitBreaker] = None
_challenge_store: Optional[ChallengeStore] = None


def _redact(text: str) -> str:
    return SECRET_REDACT_RE.sub("***REDACTED***", text)


def _get_user_id() -> str:
    return request.headers.get("X-User-ID", request.remote_addr or "unknown")


def _safe_mode_response():
    return jsonify({
        "error": "Gateway in SAFE MODE — all operations suspended",
        "safe_mode_active": True,
        "reason": _safe_mode_reason,
        "activated_at": _safe_mode_ts,
        "action": "Contact operator. POST /emergency/deactivate-safe-mode to restore.",
        "framework": FRAMEWORK_REF,
    }), 503


@app.before_request
def check_safe_mode_middleware():
    """Block all non-health traffic when safe mode is active."""
    if _safe_mode_active.is_set():
        if request.path not in ("/health", "/stats", "/emergency/deactivate-safe-mode"):
            return _safe_mode_response()


@app.before_request
def rate_limit_middleware():
    if request.path in ("/health", "/stats"):
        return
    if _rate_limiter and not _rate_limiter.is_allowed(_get_user_id()):
        _audit_log.append(
            user_id=_get_user_id(), request_hash="", risk_score=0,
            risk_vectors={}, hitl_tier="N/A", blocked=True,
            reason="Rate limit exceeded",
        )
        return jsonify({"error": "Rate limit exceeded", "framework": FRAMEWORK_REF}), 429


@app.route("/health", methods=["GET"])
def health():
    hb_valid, hb_reason = _heartbeat_monitor.validate() if _heartbeat_monitor else (False, "Not initialized")
    chain_valid, entries, _ = _audit_log.verify_chain() if _audit_log else (False, 0, "Not initialized")
    status = "active" if (hb_valid and chain_valid and not _safe_mode_active.is_set()) else "degraded"
    return jsonify({
        "status": status,
        "version": GATEWAY_VERSION,
        "framework": FRAMEWORK_REF,
        "heartbeat": {"valid": hb_valid, "detail": hb_reason},
        "audit_chain": {"valid": chain_valid, "entries": entries},
        "safe_mode": _safe_mode_active.is_set(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/stats", methods=["GET"])
def stats():
    if not _audit_log:
        return jsonify({"error": "Audit log not initialized"}), 500
    # Read last 1000 entries for stats (don't parse entire log)
    log_path = _audit_log.log_path
    entries = []
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    total = len(entries)
    blocked = sum(1 for e in entries if e.get("blocked"))
    avg_risk = sum(e.get("risk_score", 0) for e in entries) / total if total else 0
    tier_counts = {}
    for e in entries:
        t = e.get("hitl_tier", "UNKNOWN")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    return jsonify({
        "total_requests": total,
        "blocked_requests": blocked,
        "block_rate": round(blocked / total, 4) if total else 0,
        "average_risk_score": round(avg_risk, 2),
        "tier_distribution": tier_counts,
        "safe_mode_active": _safe_mode_active.is_set(),
        "audit_seq": _audit_log._seq,
    })


@app.route("/v1/messages", methods=["POST"])
def proxy_messages():
    """
    Main proxy endpoint.
    Full governance stack applied to every request.
    Every request — approved or rejected — generates an immutable audit entry.
    """
    user_id = _get_user_id()
    request_hash = ""
    risk_score = 0.0
    vector: dict = {}
    tier = HITLTier.AUTO

    try:
        raw_body = request.get_data()
        if not raw_body:
            return jsonify({"error": "Empty request body"}), 400

        # Request fingerprint (before redaction for hash accuracy)
        request_hash = hashlib.sha256(raw_body).hexdigest()[:32]

        # Redact secrets for internal processing
        body_str = _redact(raw_body.decode("utf-8", errors="replace"))
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON body"}), 400

        # Schema validation (optional, if schemas loaded)
        if SCHEMAS.get("tool_plan"):
            try:
                validate(instance=data, schema=SCHEMAS["tool_plan"])
            except ValidationError as e:
                _audit_log.append(
                    user_id=user_id, request_hash=request_hash, risk_score=0,
                    risk_vectors={}, hitl_tier="N/A", blocked=True,
                    reason=f"Schema validation: {e.message[:200]}",
                )
                return jsonify({"error": "Schema validation failed", "detail": e.message[:200]}), 400

        # Normalize request for enforcement + NEXUS field extraction
        _active_normalized_req = None
        if _ADAPTERS_AVAILABLE:
            try:
                active_provider = CONFIG.get("provider", {}).get("active", "anthropic")
                _adapter_inst   = get_adapter(active_provider, CONFIG.get("providers", {}))
                _active_normalized_req = _adapter_inst.normalize_request(
                    dict(request.headers), data
                )
            except Exception as _e:
                logger.warning("Adapter normalization failed: %s", _e)

        # 3-Vector risk scoring (use normalized risk input if available)
        risk_input = (
            _active_normalized_req.to_risk_input()
            if _active_normalized_req else data
        )
        risk_score, vector, injection_detected, a2a_detected = calculate_composite_risk(
            risk_input, user_id, _hist_tracker
        )
        tier = _hitl.tier_for_score(risk_score)

        logger.info(
            "EVAL user=%s hash=%s score=%.2f tier=%s inject=%s a2a=%s",
            user_id, request_hash[:12], risk_score, tier.value,
            injection_detected, a2a_detected,
        )

        # Hard block on injection (score modifier already applied, but enforce explicitly)
        if injection_detected:
            reason = f"Prompt injection detected (score={risk_score:.2f})"
            _audit_log.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors=vector, hitl_tier=tier.value, blocked=True, reason=reason,
            )
            return jsonify({
                "error": "Security policy violation",
                "detail": reason,
                "policy": FRAMEWORK_REF,
                "control": "P1.T1.2",
            }), 403

        # HITL circuit breaker
        hitl_result = _hitl.enforce(
            tier, dict(request.headers), request_hash, user_id, risk_score
        )
        if hitl_result is not None:
            _audit_log.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors=vector, hitl_tier=tier.value, blocked=True,
                reason=f"HITL {tier.value} enforcement",
                extra={"a2a_flagged": a2a_detected},
            )
            return jsonify(hitl_result["body"]), hitl_result["status"]

        # ── Multi-provider dispatch ────────────────────────────────────────
        # Route to active provider via adapter. Falls back to Anthropic if
        # provider_adapters.py is unavailable.
        try:
            if _ADAPTERS_AVAILABLE:
                active_provider = CONFIG.get("provider", {}).get("active", "anthropic")
                timeout         = CONFIG.get("provider", {}).get("timeout_seconds", 60)
                adapter         = get_adapter(active_provider, CONFIG.get("providers", {}))
                upstream        = adapter.forward(raw_body, timeout=timeout)
            else:
                # Fallback: Anthropic direct (no adapter)
                api_key = CONFIG.get("providers", {}).get("anthropic", {}).get("api_key", "")
                if not api_key:
                    return jsonify({"error": "API key not configured"}), 500
                upstream = http_requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                        "x-forwarded-by": f"aisafe2-gateway/{GATEWAY_VERSION}",
                    },
                    data=raw_body,
                    timeout=60,
                )
        except ValueError as e:
            logger.error("Provider config error: %s", e)
            return jsonify({"error": "Provider not configured", "detail": str(e)}), 500

        # ── Response scanning (provider-aware) ─────────────────────────────
        if _ADAPTERS_AVAILABLE:
            is_clean, scan_reason = adapter.scan_response(upstream.content)
        else:
            is_clean, scan_reason = scan_response_body(upstream.content)
        if not is_clean:
            logger.warning("Response scan BLOCKED: %s", scan_reason)
            _audit_log.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors=vector, hitl_tier=tier.value, blocked=True,
                reason=f"Response scan: {scan_reason}",
            )
            return jsonify({
                "error": "Response blocked by outbound content policy",
                "detail": scan_reason,
                "policy": FRAMEWORK_REF,
            }), 403

        # Success — log approved request (include NEXUS fields if present)
        nexus_extra = (
            extract_nexus_audit_fields(
                _active_normalized_req) if _ADAPTERS_AVAILABLE and _active_normalized_req else {}
        )
        _audit_log.append(
            user_id=user_id, request_hash=request_hash, risk_score=risk_score,
            risk_vectors=vector, hitl_tier=tier.value, blocked=False, reason=None,
            extra={
                "a2a_flagged":       a2a_detected,
                "upstream_status":   upstream.status_code,
                "response_scan":     "clean",
                "provider":          CONFIG.get("provider", {}).get("active", "anthropic"),
                **nexus_extra,
            },
        )

        # Return response — strip sensitive upstream headers
        excluded_headers = {"x-request-id", "cf-ray", "server", "via", "x-ratelimit-limit-requests"}
        safe_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in excluded_headers}
        safe_headers["X-AISAFE2-Version"] = GATEWAY_VERSION
        safe_headers["X-AISAFE2-Risk-Score"] = str(risk_score)
        safe_headers["X-AISAFE2-HITL-Tier"] = tier.value

        return Response(upstream.content, status=upstream.status_code, headers=safe_headers)

    except http_requests.Timeout:
        _audit_log.append(
            user_id=user_id, request_hash=request_hash, risk_score=risk_score,
            risk_vectors=vector, hitl_tier=tier.value, blocked=True,
            reason="Upstream timeout",
        )
        return jsonify({"error": "Upstream API timeout"}), 504

    except Exception as e:
        logger.error("Gateway internal error: %s", e, exc_info=True)
        _audit_log.append(
            user_id=user_id, request_hash=request_hash, risk_score=risk_score,
            risk_vectors=vector, hitl_tier=tier.value, blocked=True,
            reason=f"Internal error: {type(e).__name__}",
        )
        # Never expose stack traces to clients
        return jsonify({"error": "Internal gateway error"}), 500


@app.route("/emergency/safe-mode", methods=["POST"])
def emergency_safe_mode():
    """Operator-triggered safe mode activation."""
    activate_safe_mode("Manual activation via API")
    _audit_log.append(
        user_id="OPERATOR", request_hash="", risk_score=10.0,
        risk_vectors={}, hitl_tier="CRITICAL", blocked=True,
        reason="Manual safe mode activation",
    )
    return jsonify({
        "status": "safe_mode_activated",
        "timestamp": _safe_mode_ts,
        "framework": FRAMEWORK_REF,
        "message": "All operations suspended. POST /emergency/deactivate-safe-mode to restore.",
    })


@app.route("/emergency/deactivate-safe-mode", methods=["POST"])
def deactivate_safe_mode():
    """Operator-only safe mode deactivation. Requires OPERATOR_DEACTIVATION_KEY."""
    expected_key = os.environ.get("OPERATOR_DEACTIVATION_KEY", "")
    if not expected_key:
        return jsonify({"error": "OPERATOR_DEACTIVATION_KEY not configured on server"}), 500
    body = request.get_json(silent=True) or {}
    provided_key = body.get("operator_key", "")
    if not provided_key or not hmac.compare_digest(provided_key, expected_key):
        _audit_log.append(
            user_id="OPERATOR", request_hash="", risk_score=10.0,
            risk_vectors={}, hitl_tier="CRITICAL", blocked=True,
            reason="Failed safe mode deactivation attempt",
        )
        return jsonify({"error": "Invalid operator key"}), 403

    _safe_mode_active.clear()
    logger.critical("SAFE MODE DEACTIVATED by operator")
    _audit_log.append(
        user_id="OPERATOR", request_hash="", risk_score=0,
        risk_vectors={}, hitl_tier="AUTO", blocked=False,
        reason="Operator deactivated safe mode",
    )
    return jsonify({"status": "safe_mode_deactivated", "framework": FRAMEWORK_REF})


@app.route("/audit/verify-chain", methods=["GET"])
def verify_audit_chain():
    """Run chain verification on demand. Operator use only."""
    valid, count, detail = _audit_log.verify_chain()
    if not valid:
        logger.critical("On-demand chain verification FAILED: %s", detail)
    return jsonify({
        "chain_valid": valid,
        "entries_verified": count,
        "detail": detail,
        "framework": FRAMEWORK_REF,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# §11  BACKGROUND HEARTBEAT THREAD
# ═══════════════════════════════════════════════════════════════════════════════

def _heartbeat_background_thread(monitor: HeartbeatMonitor, interval: int) -> None:
    """
    Background thread that writes heartbeats and validates file integrity.
    If validation fails, activates safe mode — does NOT silently continue.
    This directly addresses Bug #11766.
    """
    while True:
        time.sleep(interval)
        valid, reason = monitor.validate()
        if valid:
            try:
                monitor.write_beat(_audit_log.last_hash if _audit_log else GENESIS_HASH)
            except Exception as e:
                logger.error("Heartbeat write error: %s", e)
                activate_safe_mode(f"Heartbeat write failure: {e}")
        else:
            activate_safe_mode(f"Heartbeat validation failed: {reason}")


# ═══════════════════════════════════════════════════════════════════════════════
# §12  CONFIG & STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

def load_config(config_path: str = "config.yaml") -> dict:
    if not Path(config_path).exists():
        print(f"ERROR: Config not found at {config_path}")
        print("Create config.yaml from the template.")
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    _expand_env_vars_recursive(cfg)
    return cfg


def _expand_env_vars_recursive(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                obj[k] = os.environ.get(v[2:-1], "")
            else:
                _expand_env_vars_recursive(v)
    elif isinstance(obj, list):
        for item in obj:
            _expand_env_vars_recursive(item)


def load_schemas(schema_dir: str = "schemas") -> dict:
    schemas = {}
    schema_path = Path(schema_dir)
    if schema_path.exists():
        for sf in schema_path.glob("*.json"):
            with sf.open(encoding="utf-8") as f:
                schemas[sf.stem] = json.load(f)
    return schemas


def setup_logging(log_config: dict) -> None:
    level = getattr(logging, log_config.get("log_level", "INFO"), logging.INFO)
    log_file = log_config.get("operational_log", "logs/gateway.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        handlers=handlers,
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def main() -> None:
    global CONFIG, SCHEMAS
    global _heartbeat_monitor, _audit_log, _rate_limiter
    global _hist_tracker, _hitl, _challenge_store

    parser = argparse.ArgumentParser(description=f"AI SAFE² OpenClaw Gateway {GATEWAY_VERSION}")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--port", type=int, help="Override port")
    parser.add_argument("--host", help="Override host")
    parser.add_argument("--init-heartbeat", action="store_true", help="Initialize HEARTBEAT.md and exit")
    args = parser.parse_args()

    CONFIG = load_config(args.config)
    SCHEMAS = load_schemas()
    setup_logging(CONFIG.get("logging", {}))

    gw_cfg = CONFIG.get("gateway", {})
    hb_cfg = CONFIG.get("heartbeat", {})
    audit_cfg = CONFIG.get("logging", {})

    # ── Chain key ──────────────────────────────────────────────────────────────
    chain_key = os.environ.get("AUDIT_CHAIN_KEY", "")
    if not chain_key:
        logger.critical("AUDIT_CHAIN_KEY environment variable not set.")
        logger.critical("Generate one: openssl rand -hex 32")
        logger.critical("Export: export AUDIT_CHAIN_KEY=<value>")
        logger.warning("Using ephemeral key — audit chain will not survive restart!")
        chain_key = secrets.token_hex(32)

    # ── Initialize subsystems ─────────────────────────────────────────────────
    _heartbeat_monitor = HeartbeatMonitor(
        hb_cfg.get("path", "HEARTBEAT.md"),
        hb_cfg.get("max_staleness_seconds", 120),
    )

    if args.init_heartbeat:
        try:
            _heartbeat_monitor.initialize_once()
            print("HEARTBEAT.md initialized successfully.")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        sys.exit(0)

    _audit_log = ImmutableAuditLog(
        audit_cfg.get("audit_log", "logs/gateway_audit.jsonl"), chain_key
    )
    _challenge_store = ChallengeStore()
    _hitl = HITLCircuitBreaker(gw_cfg, _challenge_store)
    _rate_limiter = TokenBucketRateLimiter(
        gw_cfg.get("max_requests_per_minute", 60),
        gw_cfg.get("max_requests_per_hour", 1000),
    )
    _hist_tracker = HistoricalContextTracker(gw_cfg.get("history_db", "data/action_history.json"))

    # ── Startup validation ────────────────────────────────────────────────────
    # 1. Verify audit chain integrity
    chain_valid, entries, chain_detail = _audit_log.verify_chain()
    if not chain_valid:
        logger.critical("AUDIT CHAIN BREAK DETECTED: %s", chain_detail)
        activate_safe_mode(f"Startup chain verification failed: {chain_detail}")
    else:
        logger.info("Audit chain verified: %d entries OK", entries)

    # 2. Validate heartbeat (never auto-create during startup validation)
    hb_valid, hb_reason = _heartbeat_monitor.validate()
    if not hb_valid:
        # On first run, initialize. But only if there's no existing file.
        if not _heartbeat_monitor.path.exists():
            logger.info("First run: creating HEARTBEAT.md")
            _heartbeat_monitor.initialize_once()
        else:
            logger.critical("HEARTBEAT invalid: %s", hb_reason)
            if not _safe_mode_active.is_set():
                activate_safe_mode(f"Heartbeat invalid at startup: {hb_reason}")

    # 3. Verify Anthropic API key
    api_key = CONFIG.get("anthropic", {}).get("api_key", "")
    if not api_key:
        logger.critical("ANTHROPIC_API_KEY not configured. Gateway cannot proxy requests.")
        if not _safe_mode_active.is_set():
            activate_safe_mode("Anthropic API key not configured")

    # ── Start heartbeat background thread ──────────────────────────────────
    beat_interval = hb_cfg.get("write_interval_seconds", 30)
    hb_thread = threading.Thread(
        target=_heartbeat_background_thread,
        args=(_heartbeat_monitor, beat_interval),
        daemon=True,
        name="heartbeat-monitor",
    )
    hb_thread.start()

    # ── Print banner ──────────────────────────────────────────────────────────
    host = args.host or gw_cfg.get("bind_host", "127.0.0.1")
    port = args.port or gw_cfg.get("bind_port", 8888)
    thresholds = gw_cfg.get("hitl_thresholds", {})

    print(f"\n{'═'*65}")
    print(f"  AI SAFE² Control Gateway for OpenClaw  v{GATEWAY_VERSION}")
    print(f"  {FRAMEWORK_REF}")
    print(f"{'═'*65}")
    print(f"  Binding:      http://{host}:{port}")
    print(f"  Config:       {args.config}")
    print(f"  Schemas:      {len(SCHEMAS)} loaded")
    print(f"  Heartbeat:    {_heartbeat_monitor.path} (staleness max {hb_cfg.get('max_staleness_seconds',120)}s)")
    print(f"  Audit log:    {_audit_log.log_path} ({entries} existing entries)")
    print(f"  Chain key:    {'CONFIGURED' if os.environ.get('AUDIT_CHAIN_KEY') else 'EPHEMERAL (WARNING)'}")
    print(f"  HITL tiers:   AUTO≤{thresholds.get('auto_max',3)} | MEDIUM≤{thresholds.get('medium_max',6)} | HIGH≤{thresholds.get('high_max',8)} | CRITICAL>8")
    print(f"  Safe mode:    {'ACTIVE ⚠' if _safe_mode_active.is_set() else 'Standby'}")
    print(f"{'─'*65}")
    print(f"  POST http://{host}:{port}/v1/messages      — main proxy")
    print(f"  GET  http://{host}:{port}/health            — liveness")
    print(f"  GET  http://{host}:{port}/stats             — statistics")
    print(f"  GET  http://{host}:{port}/audit/verify-chain — chain check")
    print(f"{'═'*65}\n")

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
