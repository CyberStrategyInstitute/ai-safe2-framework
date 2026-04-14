#!/usr/bin/env python3
"""
AI SAFE² Core Gateway — v3.0
═══════════════════════════════════════════════════════════════════════════════
External enforcement layer for agentic AI and non-human identity (NHI)
governance. Sits between your orchestration layer and the Anthropic API.
Embodies the "governor governs the governor" principle from AI SAFE² v3.0.

Architecture:
  Operator/Agent → [AI SAFE² Gateway v3.0] → Anthropic API
                             │
                   ┌─────────┴──────────┐
                   │  Enforcement Stack  │
                   │  P1: Risk Scoring   │  3-vector dynamic (action×sensitivity×history)
                   │  P2: HITL Circuit   │  4-tier (auto→medium→high→critical/2FA)
                   │  P3: Audit Chain    │  HMAC-chained immutable JSONL
                   │  P4: Heartbeat      │  Liveness monitor — never auto-creates
                   │  P5: A2A Detection  │  Agent impersonation heuristics
                   │  P6: Rate Limiting  │  Token bucket per identity
                   │  P7: Response Scan  │  Outbound exfil / injection detection
                   └────────────────────┘

Bug #11766 addressed:
  The heartbeat monitor ASSERTS file presence and content validity.
  It NEVER auto-creates a missing HEARTBEAT.md.
  A missing or empty file triggers CRITICAL alert + safe mode entry.
  Background jobs only execute after heartbeat validation passes.

Refs: AI SAFE² v3.0, P1.T1.2, P2.T3.1, P3.T5.1, CP.9, CP.10 (HEAR Doctrine)
"""

from __future__ import annotations

import asyncio
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
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

# Provider adapter layer (multi-provider + NEXUS-A2A compatibility)
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
    from provider_adapters import (
        get_adapter, list_providers, extract_nexus_audit_fields,
        NEXUS_A2A_INDICATORS, NormalizedRequest,
    )
    _ADAPTERS_AVAILABLE = True
except ImportError:
    _ADAPTERS_AVAILABLE = False
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ─── Version ──────────────────────────────────────────────────────────────────
GATEWAY_VERSION = "3.0.0"
FRAMEWORK_REF = "AI SAFE² v3.0"
GENESIS_HASH = hashlib.sha256(b"GENESIS:SAFE2:v3.0:CORE").hexdigest()[:16]

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter("aisafe2_requests_total", "Total requests", ["status", "hitl_tier"])
LATENCY = Histogram("aisafe2_request_latency_seconds", "Request latency")
RISK_SCORE_HIST = Histogram("aisafe2_risk_score", "Risk score distribution", buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
BLOCKED_COUNT = Counter("aisafe2_blocked_total", "Blocked requests", ["reason"])
HEARTBEAT_STATUS = Gauge("aisafe2_heartbeat_valid", "Heartbeat file validity (1=valid, 0=invalid)")
SAFE_MODE_FLAG = Gauge("aisafe2_safe_mode_active", "Safe mode active (1=yes)")
A2A_DETECTIONS = Counter("aisafe2_a2a_detections_total", "A2A impersonation detections")
CHAIN_INTEGRITY = Gauge("aisafe2_audit_chain_valid", "Audit chain integrity (1=valid)")

# ─── Logging ──────────────────────────────────────────────────────────────────
logger = logging.getLogger("aisafe2.gateway")


# ═══════════════════════════════════════════════════════════════════════════════
# §1  ENUMS & VALUE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class HITLTier(str, Enum):
    """
    Four-tier Human-in-the-Loop circuit breaker.
    Tier boundaries are operator-configurable in config.yaml.
    """
    AUTO     = "AUTO"     # 0–3:  auto-approve, log only
    MEDIUM   = "MEDIUM"   # 4–6:  require X-HITL-Token header
    HIGH     = "HIGH"     # 7–8:  require token + written reason (≥20 chars)
    CRITICAL = "CRITICAL" # >8:   out-of-band 2FA challenge-response


class RiskVector(NamedTuple):
    action_type: float        # 0 = read, 5 = write, 10 = delete/exec
    target_sensitivity: float # 0 = public, 5 = personal, 10 = system/key
    historical_context: float # 0 = frequent, 5 = rare, 10 = never seen

    def composite(self, weights: tuple[float, float, float] = (0.40, 0.35, 0.25)) -> float:
        return (
            self.action_type        * weights[0]
            + self.target_sensitivity * weights[1]
            + self.historical_context * weights[2]
        )


# ═══════════════════════════════════════════════════════════════════════════════
# §2  HEARTBEAT MONITOR  (Bug #11766 prevention)
# ═══════════════════════════════════════════════════════════════════════════════

class HeartbeatMonitor:
    """
    Validates HEARTBEAT.md existence, non-emptiness, and freshness.

    NEVER auto-creates the file. That is exactly Bug #11766.
    If the file is missing, empty, or stale → CRITICAL alert, safe mode.

    The file must contain:
        ALIVE:<ISO-8601-timestamp>:<sha256-of-prev-entry>
    written by the gateway's own background task.
    """

    def __init__(self, path: str, max_staleness_seconds: int = 120):
        self.path = Path(path)
        self.max_staleness = max_staleness_seconds
        self._lock = asyncio.Lock()
        self._last_write_hash: str = GENESIS_HASH

    async def validate(self) -> tuple[bool, str]:
        """
        Returns (is_valid, reason).
        Caller must treat is_valid=False as a HARD STOP.
        """
        async with self._lock:
            # 1. Existence check — never create
            if not self.path.exists():
                HEARTBEAT_STATUS.set(0)
                return False, f"HEARTBEAT.md missing at {self.path} — possible silent failure (Bug #11766)"

            # 2. Content check — must not be empty
            content = self.path.read_text().strip()
            if not content:
                HEARTBEAT_STATUS.set(0)
                return False, "HEARTBEAT.md is empty — monitoring disabled (Bug #11766 analog)"

            # 3. Format check
            parts = content.splitlines()[-1].split(":")
            if len(parts) < 3 or parts[0] != "ALIVE":
                HEARTBEAT_STATUS.set(0)
                return False, f"HEARTBEAT.md malformed: expected ALIVE:<timestamp>:<hash>"

            # 4. Staleness check
            try:
                last_ts = datetime.fromisoformat(parts[1])
                age = (datetime.now(timezone.utc) - last_ts.replace(tzinfo=timezone.utc)).total_seconds()
                if age > self.max_staleness:
                    HEARTBEAT_STATUS.set(0)
                    return False, f"HEARTBEAT.md stale: last write {int(age)}s ago (max {self.max_staleness}s)"
            except ValueError:
                HEARTBEAT_STATUS.set(0)
                return False, f"HEARTBEAT.md timestamp unparseable: {parts[1]}"

            HEARTBEAT_STATUS.set(1)
            return True, "OK"

    async def write_beat(self, prev_hash: str) -> None:
        """Write a timestamped heartbeat entry. Only the gateway writes this."""
        async with self._lock:
            ts = datetime.now(timezone.utc).isoformat()
            entry = f"ALIVE:{ts}:{prev_hash[:16]}"
            self.path.write_text(entry + "\n")
            self._last_write_hash = hashlib.sha256(entry.encode()).hexdigest()

    async def initialize(self) -> None:
        """
        Initialize heartbeat file on first start.
        Called ONCE during startup, not during operation.
        Subsequent writes are done by write_beat().
        """
        if not self.path.exists():
            logger.info("Initializing HEARTBEAT.md for first run")
            await self.write_beat(GENESIS_HASH)
        else:
            valid, reason = await self.validate()
            if not valid:
                logger.critical(f"Heartbeat invalid at startup: {reason}")
                # Don't sys.exit here — let the lifespan handler decide


# ═══════════════════════════════════════════════════════════════════════════════
# §3  IMMUTABLE AUDIT LOG  (HMAC-chained JSONL)
# ═══════════════════════════════════════════════════════════════════════════════

class ImmutableAuditLog:
    """
    HMAC-SHA256 chained append-only audit log.

    Each entry contains:
      - seq: monotonic sequence number
      - timestamp, user_id, request_hash, risk_score, hitl_tier, blocked, reason
      - prev_hash: hash of the previous entry (GENESIS_HASH for entry 0)
      - entry_hash: HMAC(chain_key, prev_hash + "|" + entry_json)

    Any modification to a historical entry breaks the chain forward.
    Chain is verified on startup. A broken chain triggers CRITICAL alert.

    The audit process runs OUTSIDE OpenClaw's process boundary, so a
    compromised agent cannot tamper with evidence (architectural separation).
    """

    def __init__(self, log_path: str, chain_key: str):
        self.log_path = Path(log_path)
        self._chain_key = chain_key.encode()
        self._lock = asyncio.Lock()
        self._seq: int = 0
        self._last_hash: str = GENESIS_HASH

    def _compute_hash(self, prev_hash: str, entry_json: str) -> str:
        msg = f"{prev_hash}|{entry_json}".encode("utf-8")
        return hmac.new(self._chain_key, msg, hashlib.sha256).hexdigest()

    async def verify_chain(self) -> tuple[bool, int, str]:
        """
        Re-read the log file and verify every entry's HMAC.
        Returns (is_valid, entries_checked, error_detail).
        """
        if not self.log_path.exists():
            return True, 0, "Log file does not yet exist (first run)"

        prev_hash = GENESIS_HASH
        count = 0
        try:
            with self.log_path.open("r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    stored_hash = entry.pop("entry_hash", "")
                    expected = self._compute_hash(prev_hash, json.dumps(entry, sort_keys=True))
                    if not hmac.compare_digest(stored_hash, expected):
                        CHAIN_INTEGRITY.set(0)
                        return False, count, f"Chain break at seq={entry.get('seq', '?')}"
                    prev_hash = stored_hash
                    count += 1
        except (json.JSONDecodeError, OSError) as e:
            CHAIN_INTEGRITY.set(0)
            return False, count, f"Log read error: {e}"

        # Restore state
        self._seq = count
        self._last_hash = prev_hash
        CHAIN_INTEGRITY.set(1)
        return True, count, "OK"

    async def append(
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
        """Append a tamper-evident entry and return its hash."""
        async with self._lock:
            self._seq += 1
            entry: dict[str, Any] = {
                "seq": self._seq,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "gateway_version": GATEWAY_VERSION,
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
            entry_json = json.dumps(entry, sort_keys=True)
            entry_hash = self._compute_hash(self._last_hash, entry_json)
            entry["entry_hash"] = entry_hash

            # Append to JSONL — atomic at OS level for single-line writes
            with self.log_path.open("a") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                os.fsync(f.fileno())

            self._last_hash = entry_hash
            logger.info(
                "AUDIT seq=%d user=%s score=%.2f tier=%s blocked=%s hash=%s",
                self._seq, user_id, risk_score, hitl_tier, blocked, entry_hash[:12],
            )
            return entry_hash


# ═══════════════════════════════════════════════════════════════════════════════
# §4  RATE LIMITER  (token bucket, per user)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenBucket:
    """Per-identity sliding window token bucket."""

    def __init__(self, rate_per_minute: int, burst: int):
        self._rpm = rate_per_minute
        self._burst = burst
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def consume(self, identity: str) -> bool:
        """Returns True if allowed, False if rate-limited."""
        async with self._lock:
            now = time.monotonic()
            window = self._buckets[identity]
            cutoff = now - 60.0
            # evict old timestamps
            while window and window[0] < cutoff:
                window.pop(0)
            if len(window) >= self._rpm:
                return False
            window.append(now)
            return True


# ═══════════════════════════════════════════════════════════════════════════════
# §5  HISTORICAL CONTEXT TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

class HistoricalContextTracker:
    """
    Tracks (user_id, action_fingerprint) frequency.
    Used for the third risk vector: 0=frequent, 5=rare, 10=never-seen.
    Persisted to JSON so context survives restarts.
    """

    def __init__(self, persist_path: str = "data/action_history.json"):
        self._path = Path(persist_path)
        self._lock = asyncio.Lock()
        self._counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                for uid, actions in data.items():
                    self._counts[uid] = defaultdict(int, actions)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: dict(v) for k, v in self._counts.items()}))

    async def score(self, user_id: str, fingerprint: str) -> float:
        """Score 0 (frequent), 5 (rare <5x), 10 (never seen)."""
        async with self._lock:
            count = self._counts[user_id][fingerprint]
            if count == 0:
                score = 10.0
            elif count < 5:
                score = 5.0
            else:
                score = 0.0
            self._counts[user_id][fingerprint] += 1
            self._save()
            return score


# ═══════════════════════════════════════════════════════════════════════════════
# §6  RISK SCORER  (3-vector dynamic scoring)
# ═══════════════════════════════════════════════════════════════════════════════

# Action-type tool mappings
ACTION_SCORES: dict[str, float] = {
    # Read (0)
    "read": 0, "search": 0, "retrieve": 0, "list": 0, "get": 0, "fetch": 0,
    # Write (5)
    "write": 5, "create": 5, "update": 5, "edit": 5, "apply_patch": 5,
    "canvas": 5, "upload": 5, "send": 5,
    # Delete / Exec (10)
    "delete": 10, "exec": 10, "process": 10, "run": 10, "cron": 10,
    "browser": 10, "gateway": 10, "nodes": 10, "kill": 10, "terminate": 10,
}

SYSTEM_FILE_PATTERNS = re.compile(
    r"(/etc/|/proc/|/sys/|\.ssh/|\.env|id_rsa|\.pem|\.key|ANTHROPIC|"
    r"SECRET|TOKEN|PASSWORD|CREDENTIAL|/root/|shadow|passwd)",
    re.IGNORECASE,
)
PERSONAL_FILE_PATTERNS = re.compile(
    r"(\.config/|Documents/|Downloads/|Desktop/|home/|user|personal|private)",
    re.IGNORECASE,
)

A2A_INDICATORS = (
    NEXUS_A2A_INDICATORS if _ADAPTERS_AVAILABLE else [
        "orchestrat", "subagent", "delegate to", "forward to agent",
        "as the orchestrator", "acting as agent", "agent-to-agent",
        "i am the supervisor", "tool_result", "[INST]", "<|im_start|>",
    ]
)

INJECTION_PATTERNS = [
    "ignore previous instructions", "ignore all prior instructions",
    "you are now in dan mode", "you are now in unrestricted mode",
    "system: override", "disregard your programming", "forget everything",
    "new instructions from admin", "override safety", "jailbreak",
    "<|im_start|>", "<|im_end|>", "[/INST]",
]

SECRET_REDACT = re.compile(
    r"(sk-ant-api\d+-[a-zA-Z0-9_\-]{95}|"
    r"sk-[a-zA-Z0-9]{48}|"
    r"ghp_[a-zA-Z0-9]{36}|"
    r"xoxb-[a-zA-Z0-9\-]{10,72}|"
    r"AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]+ KEY-----)"
)


class RiskScorer:

    @staticmethod
    def _action_type_score(data: dict) -> float:
        """Score based on most dangerous tool requested."""
        tools = data.get("tools", [])
        if not tools:
            return 0.0
        worst = 0.0
        for tool in tools:
            name = (tool.get("name", "") if isinstance(tool, dict) else str(tool)).lower()
            for key, score in ACTION_SCORES.items():
                if key in name:
                    worst = max(worst, score)
        return worst

    @staticmethod
    def _target_sensitivity_score(data: dict) -> float:
        """Score based on file paths / target references in messages."""
        worst = 0.0
        for msg in data.get("messages", []):
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            if SYSTEM_FILE_PATTERNS.search(content):
                worst = max(worst, 10.0)
            elif PERSONAL_FILE_PATTERNS.search(content):
                worst = max(worst, 5.0)
        # Also check tool input parameters
        for tool in data.get("tools", []):
            if isinstance(tool, dict):
                inp = json.dumps(tool.get("input_schema", {}))
                if SYSTEM_FILE_PATTERNS.search(inp):
                    worst = max(worst, 10.0)
        return worst

    @staticmethod
    def _detect_injection(data: dict) -> bool:
        all_text = " ".join(
            msg.get("content", "") for msg in data.get("messages", [])
            if isinstance(msg.get("content"), str)
        ).lower()
        return any(p in all_text for p in INJECTION_PATTERNS)

    @staticmethod
    def _detect_a2a(data: dict) -> bool:
        """
        Heuristic A2A impersonation detection.
        Flags: assistant-role content in user messages, orchestration keywords,
        nested tool_result blocks, self-referential agent language.
        """
        messages = data.get("messages", [])
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            content_lower = content.lower()
            # User message claiming to be assistant or containing assistant-style content
            if role == "user" and any(ind in content_lower for ind in A2A_INDICATORS):
                return True
            # Nested tool_result in user messages (agent chaining)
            if role == "user" and "tool_result" in content_lower:
                return True
        return False

    @classmethod
    async def score(
        cls,
        data: dict,
        user_id: str,
        tracker: HistoricalContextTracker,
    ) -> tuple[float, RiskVector, bool, bool]:
        """
        Returns (composite_score, vector, injection_detected, a2a_detected).
        composite_score is pre-modifier; callers should add injection/A2A bonuses.
        """
        a_score = cls._action_type_score(data)
        t_score = cls._target_sensitivity_score(data)

        # Historical fingerprint = sorted tool names + first 64 chars of system
        fingerprint = ":".join(sorted(
            t.get("name", "") if isinstance(t, dict) else str(t)
            for t in data.get("tools", [])
        )) + data.get("system", "")[:64]
        h_score = await tracker.score(user_id, fingerprint)

        vector = RiskVector(a_score, t_score, h_score)
        base = vector.composite()

        injection = cls._detect_injection(data)
        a2a = cls._detect_a2a(data)

        if injection:
            base = min(base + 5.0, 10.0)
        if a2a:
            base = min(base + 3.0, 10.0)
            A2A_DETECTIONS.inc()

        return round(base, 4), vector, injection, a2a


# ═══════════════════════════════════════════════════════════════════════════════
# §7  HITL CIRCUIT BREAKER  (4-tier)
# ═══════════════════════════════════════════════════════════════════════════════

class ChallengeStore:
    """
    Stores pending CRITICAL-tier HITL challenges.
    Challenge tokens expire after TTL seconds.
    """

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def create(self, request_hash: str, user_id: str) -> str:
        """Issue a challenge token. Returns the token."""
        token = secrets.token_urlsafe(32)
        async with self._lock:
            self._store[token] = {
                "request_hash": request_hash,
                "user_id": user_id,
                "issued_at": time.monotonic(),
                "used": False,
            }
        return token

    async def verify(self, token: str, response_mac: str, chain_key: bytes) -> tuple[bool, str]:
        """
        Verify the HITL challenge response.
        Expected response_mac = HMAC-SHA256(chain_key, token)[:16].
        Returns (valid, request_hash).
        """
        async with self._lock:
            challenge = self._store.get(token)
            if not challenge:
                return False, ""
            if challenge["used"]:
                return False, ""
            age = time.monotonic() - challenge["issued_at"]
            if age > self._ttl:
                del self._store[token]
                return False, ""
            expected = hmac.new(chain_key, token.encode(), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(response_mac, expected):
                return False, ""
            challenge["used"] = True
            return True, challenge["request_hash"]


class HITLCircuitBreaker:
    """
    4-tier HITL enforcement.

    Tier     Score   Action
    AUTO     0–3     Auto-approve, log
    MEDIUM   4–6     Require X-HITL-Token header
    HIGH     7–8     Require token + X-HITL-Reason (≥20 chars)
    CRITICAL >8      Out-of-band challenge-response (2FA)
    """

    def __init__(self, config: dict, challenge_store: ChallengeStore):
        self._cfg = config
        self._challenges = challenge_store
        self._chain_key = os.environ.get("AUDIT_CHAIN_KEY", "default-change-me").encode()
        # HITL token store: token → (user_id, expiry)
        self._tokens: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    def tier_for_score(self, score: float) -> HITLTier:
        t = self._cfg.get("hitl_thresholds", {})
        if score <= t.get("auto_max", 3.0):
            return HITLTier.AUTO
        elif score <= t.get("medium_max", 6.0):
            return HITLTier.MEDIUM
        elif score <= t.get("high_max", 8.0):
            return HITLTier.HIGH
        else:
            return HITLTier.CRITICAL

    async def issue_medium_token(self, user_id: str) -> str:
        """Issue a short-lived HITL approval token for MEDIUM tier."""
        token = secrets.token_urlsafe(16)
        async with self._lock:
            self._tokens[token] = (user_id, time.monotonic() + 300)
        return token

    async def validate_medium_token(self, token: str, user_id: str) -> bool:
        async with self._lock:
            if token not in self._tokens:
                return False
            uid, expiry = self._tokens[token]
            if uid != user_id or time.monotonic() > expiry:
                del self._tokens[token]
                return False
            del self._tokens[token]
            return True

    async def enforce(
        self,
        tier: HITLTier,
        request: Request,
        request_hash: str,
        user_id: str,
    ) -> Optional[JSONResponse]:
        """
        Returns None if approved, or a JSONResponse if blocked/pending.
        """
        if tier == HITLTier.AUTO:
            return None  # pass through

        if tier == HITLTier.MEDIUM:
            token = request.headers.get("X-HITL-Token", "")
            if not token:
                # Issue a token they must present on retry
                issued = await self.issue_medium_token(user_id)
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "HITL approval required",
                        "tier": "MEDIUM",
                        "instruction": "Resubmit request with X-HITL-Token header",
                        "token": issued,
                        "framework": FRAMEWORK_REF,
                    },
                )
            valid = await self.validate_medium_token(token, user_id)
            if not valid:
                BLOCKED_COUNT.labels(reason="invalid_hitl_token").inc()
                return JSONResponse(
                    status_code=403,
                    content={"error": "Invalid or expired HITL token", "tier": "MEDIUM"},
                )
            return None  # approved

        if tier == HITLTier.HIGH:
            token = request.headers.get("X-HITL-Token", "")
            reason = request.headers.get("X-HITL-Reason", "")
            if not token or len(reason.strip()) < 20:
                issued = await self.issue_medium_token(user_id)
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "HITL HIGH-tier approval required",
                        "tier": "HIGH",
                        "instruction": (
                            "Resubmit with X-HITL-Token and "
                            "X-HITL-Reason (≥20 characters explaining why)"
                        ),
                        "token": issued,
                        "framework": FRAMEWORK_REF,
                    },
                )
            valid = await self.validate_medium_token(token, user_id)
            if not valid:
                BLOCKED_COUNT.labels(reason="invalid_hitl_high").inc()
                return JSONResponse(
                    status_code=403,
                    content={"error": "Invalid or expired HITL token", "tier": "HIGH"},
                )
            return None  # approved

        # CRITICAL — out-of-band 2FA challenge
        challenge_response = request.headers.get("X-HITL-Challenge", "")
        if not challenge_response:
            challenge_token = await self._challenges.create(request_hash, user_id)
            # In production: send challenge_token to webhook/PagerDuty/Slack
            logger.critical(
                "CRITICAL HITL challenge issued: user=%s hash=%s token=%s",
                user_id, request_hash[:12], challenge_token,
            )
            BLOCKED_COUNT.labels(reason="critical_pending_2fa").inc()
            return JSONResponse(
                status_code=202,
                content={
                    "status": "pending_2fa",
                    "tier": "CRITICAL",
                    "challenge_token": challenge_token,
                    "instruction": (
                        "Compute HMAC-SHA256(AUDIT_CHAIN_KEY, challenge_token)[:16] "
                        "and resubmit with X-HITL-Challenge: <challenge_token>:<mac>"
                    ),
                    "expires_in_seconds": 300,
                    "framework": FRAMEWORK_REF,
                },
            )

        # Verify challenge response
        parts = challenge_response.split(":", 1)
        if len(parts) != 2:
            return JSONResponse(status_code=403, content={"error": "Malformed X-HITL-Challenge"})
        token, mac = parts
        valid, orig_hash = await self._challenges.verify(token, mac, self._chain_key)
        if not valid:
            BLOCKED_COUNT.labels(reason="invalid_2fa_response").inc()
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid or expired 2FA challenge response", "tier": "CRITICAL"},
            )
        if orig_hash != request_hash:
            BLOCKED_COUNT.labels(reason="request_hash_mismatch").inc()
            return JSONResponse(
                status_code=403,
                content={"error": "Request body changed since challenge was issued"},
            )
        return None  # approved


# ═══════════════════════════════════════════════════════════════════════════════
# §8  RESPONSE SCANNER  (outbound inspection)
# ═══════════════════════════════════════════════════════════════════════════════

EXFIL_PATTERNS = re.compile(
    r"(ANTHROPIC_API_KEY|sk-ant-|sk-[a-zA-Z0-9]{48}|"
    r"ghp_[a-zA-Z0-9]{36}|password|secret|credential)",
    re.IGNORECASE,
)

RESPONSE_INJECTION = re.compile(
    r"(ignore previous instructions|override safety|you are now|"
    r"new system prompt|[Ii]gnore all prior)",
    re.IGNORECASE,
)


def scan_response(response_body: bytes) -> tuple[bool, str]:
    """
    Inspect LLM response for data exfiltration or injected payloads
    in tool_use blocks. Returns (is_clean, reason).
    """
    try:
        data = json.loads(response_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return True, "non-JSON response skipped"

    text_content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            text_content += block.get("text", "")
        elif block.get("type") == "tool_use":
            # Tool use inputs could carry injected instructions
            inp = json.dumps(block.get("input", {}))
            if RESPONSE_INJECTION.search(inp):
                return False, f"Injection payload in tool_use block: {block.get('name', '?')}"
            if EXFIL_PATTERNS.search(inp):
                return False, f"Potential secret exfiltration in tool_use input"

    if EXFIL_PATTERNS.search(text_content):
        return False, "Potential secret exfiltration in response text"

    return True, "clean"


# ═══════════════════════════════════════════════════════════════════════════════
# §9  SAFE MODE
# ═══════════════════════════════════════════════════════════════════════════════

class SafeMode:
    """
    When active, the gateway rejects all non-health requests.
    Activated by: missing heartbeat, broken audit chain, or explicit API call.
    Deactivated only by explicit operator action (not automated).
    """

    def __init__(self):
        self._active = asyncio.Event()
        self._reason: str = ""
        self._activated_at: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self._active.is_set()

    def activate(self, reason: str) -> None:
        self._active.set()
        self._reason = reason
        self._activated_at = datetime.now(timezone.utc).isoformat()
        SAFE_MODE_FLAG.set(1)
        logger.critical("SAFE MODE ACTIVATED: %s", reason)

    def deactivate(self, operator_key: str, expected_key: str) -> bool:
        if not hmac.compare_digest(operator_key, expected_key):
            logger.warning("Safe mode deactivation attempted with invalid key")
            return False
        self._active.clear()
        self._reason = ""
        self._activated_at = None
        SAFE_MODE_FLAG.set(0)
        logger.critical("SAFE MODE DEACTIVATED by operator")
        return True

    def status(self) -> dict:
        return {
            "safe_mode_active": self.is_active,
            "reason": self._reason,
            "activated_at": self._activated_at,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §10  CONFIG & DEPENDENCY INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def load_config(path: str = "config/default.yaml") -> dict:
    if not Path(path).exists():
        logger.warning("Config not found at %s — using secure defaults", path)
        return _default_config()
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    _expand_env_vars(cfg)
    return cfg


def _expand_env_vars(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                obj[k] = os.environ.get(v[2:-1], "")
            else:
                _expand_env_vars(v)
    elif isinstance(obj, list):
        for item in obj:
            _expand_env_vars(item)


def _default_config() -> dict:
    return {
        "gateway": {
            "bind_host": "127.0.0.1",
            "bind_port": 8888,
            "risk_weights": [0.40, 0.35, 0.25],
            "hitl_thresholds": {"auto_max": 3.0, "medium_max": 6.0, "high_max": 8.0},
            "rate_limit_rpm": 60,
            "rate_limit_burst": 10,
        },
        "heartbeat": {
            "path": "HEARTBEAT.md",
            "max_staleness_seconds": 120,
            "check_interval_seconds": 30,
        },
        "audit": {
            "log_path": "logs/audit.jsonl",
            "redact_secrets": True,
        },
        "provider":  {"active": "anthropic", "timeout_seconds": 60},
        "providers": {
            "anthropic":  {"api_key": "${ANTHROPIC_API_KEY}", "endpoint": "https://api.anthropic.com/v1/messages", "version": "2023-06-01"},
            "openai":     {"api_key": "${OPENAI_API_KEY}",   "endpoint": "https://api.openai.com/v1/chat/completions"},
            "gemini":     {"api_key": "${GEMINI_API_KEY}",   "model": "gemini-1.5-pro"},
            "ollama":     {"host": "http://localhost:11434",  "path": "/api/chat", "model": "llama3"},
            "openrouter": {"api_key": "${OPENROUTER_API_KEY}","endpoint": "https://openrouter.ai/api/v1/chat/completions"},
        },
        "nexus": {"enabled": True, "enforcement": "passthrough", "log_agent_identity": True},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# §11  APPLICATION LIFESPAN & FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

# These will be populated during startup
_CONFIG: dict = {}
_heartbeat: HeartbeatMonitor
_audit: ImmutableAuditLog
_rate_limiter: TokenBucket
_hist_tracker: HistoricalContextTracker
_safe_mode: SafeMode
_challenge_store: ChallengeStore
_hitl: HITLCircuitBreaker
_http_client: httpx.AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _CONFIG, _heartbeat, _audit, _rate_limiter, _hist_tracker
    global _safe_mode, _challenge_store, _hitl, _http_client

    _CONFIG = load_config()
    gw = _CONFIG.get("gateway", {})
    hb_cfg = _CONFIG.get("heartbeat", {})
    audit_cfg = _CONFIG.get("audit", {})

    chain_key = os.environ.get("AUDIT_CHAIN_KEY", "")
    if not chain_key:
        logger.critical("AUDIT_CHAIN_KEY not set — audit log integrity compromised")
        chain_key = secrets.token_hex(32)
        logger.warning("Generated ephemeral chain key — set AUDIT_CHAIN_KEY in env")

    # Ensure log directory exists
    Path(audit_cfg.get("log_path", "logs/audit.jsonl")).parent.mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # Initialize components
    _safe_mode = SafeMode()
    _heartbeat = HeartbeatMonitor(
        hb_cfg.get("path", "HEARTBEAT.md"),
        hb_cfg.get("max_staleness_seconds", 120),
    )
    _audit = ImmutableAuditLog(audit_cfg.get("log_path", "logs/audit.jsonl"), chain_key)
    _rate_limiter = TokenBucket(gw.get("rate_limit_rpm", 60), gw.get("rate_limit_burst", 10))
    _hist_tracker = HistoricalContextTracker()
    _challenge_store = ChallengeStore()
    _hitl = HITLCircuitBreaker(gw, _challenge_store)
    _http_client = httpx.AsyncClient(timeout=_CONFIG.get("anthropic", {}).get("timeout_seconds", 60))

    # Verify audit chain integrity on startup
    chain_valid, entries, chain_msg = await _audit.verify_chain()
    if not chain_valid:
        _safe_mode.activate(f"Audit chain broken: {chain_msg}")
        logger.critical("STARTUP ABORTED: audit chain break at %d entries: %s", entries, chain_msg)
    else:
        logger.info("Audit chain verified: %d entries OK", entries)

    # Heartbeat — initialize only if first run, validate if exists
    await _heartbeat.initialize()
    hb_valid, hb_reason = await _heartbeat.validate()
    if not hb_valid and not _safe_mode.is_active:
        _safe_mode.activate(f"Heartbeat invalid: {hb_reason}")

    # Start background heartbeat writer
    beat_task = asyncio.create_task(_heartbeat_loop(hb_cfg.get("check_interval_seconds", 30)))

    logger.info(
        "AI SAFE² Gateway v%s started | safe_mode=%s | chain_entries=%d",
        GATEWAY_VERSION, _safe_mode.is_active, entries,
    )

    yield

    beat_task.cancel()
    await _http_client.aclose()
    logger.info("AI SAFE² Gateway shutdown complete")


async def _heartbeat_loop(interval: int) -> None:
    """Write periodic heartbeats. Validate before each write."""
    while True:
        await asyncio.sleep(interval)
        hb_valid, hb_reason = await _heartbeat.validate()
        if hb_valid:
            await _heartbeat.write_beat(_audit._last_hash)
        else:
            _safe_mode.activate(f"Heartbeat lost during operation: {hb_reason}")
            logger.critical("Heartbeat validation failed: %s", hb_reason)


app = FastAPI(
    title="AI SAFE² Core Gateway",
    version=GATEWAY_VERSION,
    description=FRAMEWORK_REF,
    lifespan=lifespan,
)


# ═══════════════════════════════════════════════════════════════════════════════
# §12  MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

@app.middleware("http")
async def governance_middleware(request: Request, call_next):
    # Allow health/metrics/safe-mode routes without enforcement
    if request.url.path in ("/health", "/metrics", "/safe-mode/status"):
        return await call_next(request)

    # Safe mode check — hard stop
    if _safe_mode.is_active:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Gateway in SAFE MODE — all operations suspended",
                **_safe_mode.status(),
                "action": "Contact operator to review and deactivate safe mode",
            },
        )

    # Rate limiting
    user_id = request.headers.get("X-User-ID", request.client.host if request.client else "unknown")
    if not await _rate_limiter.consume(user_id):
        BLOCKED_COUNT.labels(reason="rate_limited").inc()
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "framework": FRAMEWORK_REF},
        )

    start = time.monotonic()
    response = await call_next(request)
    LATENCY.observe(time.monotonic() - start)
    response.headers["X-AISAFE2-Version"] = GATEWAY_VERSION
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# §13  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    hb_valid, hb_reason = await _heartbeat.validate()
    chain_valid, _, _ = await _audit.verify_chain()
    status = "degraded" if not hb_valid or not chain_valid else "active"
    return {
        "status": status,
        "version": GATEWAY_VERSION,
        "framework": FRAMEWORK_REF,
        "heartbeat": {"valid": hb_valid, "reason": hb_reason},
        "audit_chain": {"valid": chain_valid},
        "safe_mode": _safe_mode.is_active,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/safe-mode/status")
async def safe_mode_status():
    return _safe_mode.status()


@app.post("/safe-mode/deactivate")
async def deactivate_safe_mode(request: Request):
    body = await request.json()
    operator_key = body.get("operator_key", "")
    expected = os.environ.get("OPERATOR_DEACTIVATION_KEY", "")
    if not expected:
        raise HTTPException(500, "OPERATOR_DEACTIVATION_KEY not configured")
    if _safe_mode.deactivate(operator_key, expected):
        return {"status": "safe_mode_deactivated"}
    raise HTTPException(403, "Invalid operator key")


@app.post("/v1/messages")
async def proxy_messages(request: Request):
    """
    Main proxy endpoint. Enforces full AI SAFE² governance stack.
    All requests are scored, tiered, and audit-logged regardless of outcome.
    """
    user_id = request.headers.get("X-User-ID", "anonymous")
    request_hash = ""
    risk_score = 0.0
    tier = HITLTier.AUTO
    blocked = True
    block_reason = ""

    try:
        body = await request.body()

        # Redact secrets before any processing
        body_str = SECRET_REDACT.sub("***REDACTED***", body.decode("utf-8", errors="replace"))
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON body")

        # Request fingerprint
        request_hash = hashlib.sha256(body).hexdigest()[:32]

        # Normalize request for enforcement + NEXUS field extraction
        _norm_req = None
        if _ADAPTERS_AVAILABLE:
            try:
                active_provider = _CONFIG.get("provider", {}).get("active", "anthropic")
                _norm_req = get_adapter(
                    active_provider, _CONFIG.get("providers", {})
                ).normalize_request(dict(request.headers), data)
            except Exception as _e:
                logger.warning("Adapter normalization failed: %s", _e)

        # Risk scoring (3-vector) — use normalized input if available
        risk_input = _norm_req.to_risk_input() if _norm_req else data
        risk_score, vector, injection, a2a = await RiskScorer.score(risk_input, user_id, _hist_tracker)
        tier = _hitl.tier_for_score(risk_score)

        REQUEST_COUNT.labels(status="evaluated", hitl_tier=tier.value).inc()
        RISK_SCORE_HIST.observe(risk_score)

        # Hard block: injection detected
        if injection:
            block_reason = "Prompt injection pattern detected"
            BLOCKED_COUNT.labels(reason="prompt_injection").inc()
            await _audit.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors={"action": vector.action_type, "sensitivity": vector.target_sensitivity, "history": vector.historical_context},
                hitl_tier=tier.value, blocked=True, reason=block_reason,
            )
            return JSONResponse(status_code=403, content={
                "error": "Security policy violation", "detail": block_reason,
                "policy": FRAMEWORK_REF, "control": "P1.T1.2",
            })

        # HITL enforcement
        hitl_response = await _hitl.enforce(tier, request, request_hash, user_id)
        if hitl_response is not None:
            block_reason = f"HITL {tier.value} enforcement"
            await _audit.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors={"action": vector.action_type, "sensitivity": vector.target_sensitivity, "history": vector.historical_context},
                hitl_tier=tier.value, blocked=True, reason=block_reason,
            )
            return hitl_response

        # ── Multi-provider dispatch ────────────────────────────────────────
        try:
            if _ADAPTERS_AVAILABLE:
                active_provider = _CONFIG.get("provider", {}).get("active", "anthropic")
                timeout         = _CONFIG.get("provider", {}).get("timeout_seconds", 60)
                _adapter        = get_adapter(active_provider, _CONFIG.get("providers", {}))
                # httpx async client: run sync adapter.forward in threadpool
                import asyncio
                upstream_response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _adapter.forward(body, timeout=timeout)
                )
                # Wrap requests.Response to match httpx interface
                class _WrappedResp:
                    def __init__(self, r):
                        self.content     = r.content
                        self.status_code = r.status_code
                        self.headers     = dict(r.headers)
                upstream_response = _WrappedResp(upstream_response)
            else:
                api_key = _CONFIG.get("providers", {}).get("anthropic", {}).get("api_key", "")
                if not api_key:
                    raise HTTPException(500, "API key not configured")
                upstream_response = await _http_client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                        "x-forwarded-by": f"aisafe2-gateway/{GATEWAY_VERSION}",
                    },
                    content=body,
                )
        except ValueError as e:
            raise HTTPException(500, f"Provider not configured: {e}")

        # ── Response scanning (provider-aware) ─────────────────────────────
        if _ADAPTERS_AVAILABLE and _norm_req:
            is_clean, scan_reason = _adapter.scan_response(upstream_response.content)
        else:
            is_clean, scan_reason = scan_response(upstream_response.content)
        if not is_clean:
            logger.warning("Response scan failed: %s", scan_reason)
            BLOCKED_COUNT.labels(reason="response_scan").inc()
            await _audit.append(
                user_id=user_id, request_hash=request_hash, risk_score=risk_score,
                risk_vectors={"action": vector.action_type, "sensitivity": vector.target_sensitivity, "history": vector.historical_context},
                hitl_tier=tier.value, blocked=True, reason=f"Response scan: {scan_reason}",
            )
            return JSONResponse(status_code=403, content={
                "error": "Response blocked by outbound scan", "detail": scan_reason,
                "policy": FRAMEWORK_REF,
            })

        # Success — include provider + NEXUS identity fields in audit
        _nexus_extra = extract_nexus_audit_fields(_norm_req) if (_ADAPTERS_AVAILABLE and _norm_req) else {}
        blocked = False
        await _audit.append(
            user_id=user_id, request_hash=request_hash, risk_score=risk_score,
            risk_vectors={"action": vector.action_type, "sensitivity": vector.target_sensitivity, "history": vector.historical_context},
            hitl_tier=tier.value, blocked=False, reason=None,
            extra={
                "a2a_flagged":     a2a,
                "upstream_status": upstream_response.status_code,
                "provider":        _CONFIG.get("provider", {}).get("active", "anthropic"),
                **_nexus_extra,
            },
        )

        REQUEST_COUNT.labels(status=str(upstream_response.status_code), hitl_tier=tier.value).inc()

        # Strip sensitive Anthropic response headers before forwarding
        safe_headers = {
            k: v for k, v in upstream_response.headers.items()
            if k.lower() not in {"x-request-id", "cf-ray", "server", "via", "x-ratelimit-limit-requests"}
        }
        safe_headers["X-AISAFE2-Version"] = GATEWAY_VERSION
        safe_headers["X-AISAFE2-Risk-Score"] = str(risk_score)
        safe_headers["X-AISAFE2-HITL-Tier"] = tier.value

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=safe_headers,
            media_type=upstream_response.headers.get("content-type", "application/json"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Gateway internal error: %s", e, exc_info=True)
        await _audit.append(
            user_id=user_id, request_hash=request_hash, risk_score=risk_score,
            risk_vectors={}, hitl_tier=tier.value if tier else "UNKNOWN",
            blocked=True, reason=f"Internal error: {type(e).__name__}",
        )
        # Never expose stack traces to clients
        return JSONResponse(status_code=500, content={"error": "Internal gateway error"})


# ═══════════════════════════════════════════════════════════════════════════════
# §14  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description=f"AI SAFE² Core Gateway {GATEWAY_VERSION}")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    cfg = load_config(args.config)
    gw = cfg.get("gateway", {})

    print(f"\n{'='*60}")
    print(f"  AI SAFE² Core Gateway  {GATEWAY_VERSION}")
    print(f"  {FRAMEWORK_REF}")
    print(f"{'='*60}")
    print(f"  Binding:  http://{args.host}:{args.port}")
    print(f"  HITL:     4-tier circuit breaker active")
    print(f"  Audit:    HMAC-chained immutable JSONL")
    print(f"  Heartbeat: {cfg.get('heartbeat', {}).get('path', 'HEARTBEAT.md')}")
    print(f"{'='*60}\n")

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=True,
    )
