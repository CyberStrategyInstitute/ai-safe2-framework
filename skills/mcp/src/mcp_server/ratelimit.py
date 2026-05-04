"""
AI SAFE2 MCP Server — Token Bucket Rate Limiter (RISK-3 FIX)

Provides in-process, per-tier, per-IP rate limiting for the HTTP transport.
Applied inside BearerAuthMiddleware after tier resolution, so limits are
tier-aware (free: 30/hr, pro: 1000/hr) and cannot be influenced by
client-controlled headers.

Design: Token Bucket Algorithm
  - Each (tier:ip) key gets a bucket with capacity = hourly limit.
  - Bucket refills continuously at rate = limit / 3600 tokens/second.
  - Each request consumes 1 token. Denied if bucket < 1 token.
  - Burst: a cold bucket starts full (allows burst up to the hourly limit).

Thread Safety:
  - Single threading.Lock per limiter instance.
  - Safe for asyncio (lock acquired and released within a single sync call).

Single-Instance Deployment:
  This module uses in-process memory. Data does not survive restarts.
  Suitable for: single Railway dyno, single Docker container, self-hosted single process.

Multi-Instance Upgrade Path:
  Replace _TokenBucketLimiter._buckets with a Redis backend.
  See README section: "Multi-Instance Rate Limiting".

  Minimal Redis upgrade:
    pip install redis
    import redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def check(self, key: str) -> RateLimitResult:
        limit = self._get_limit_for_key(key)
        pipe = r.pipeline()
        now = int(time.time())
        window_key = f"rl:{key}:{now // 3600}"  # hourly window key
        pipe.incr(window_key)
        pipe.expire(window_key, 7200)
        count, _ = pipe.execute()
        allowed = count <= limit
        remaining = max(0, limit - count)
        retry_after = 3600 - (now % 3600) if not allowed else 0
        return RateLimitResult(allowed, limit, remaining, retry_after,
                               self._build_headers(allowed, limit, remaining, retry_after))
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import NamedTuple

import structlog

from mcp_server.config import FREE_RATE_LIMIT, PRO_RATE_LIMIT

log = structlog.get_logger()

# Window in seconds — rate limits are expressed per-hour
_WINDOW_SECONDS = 3600
# Stale bucket GC: remove buckets inactive for 2 windows
_STALE_THRESHOLD = _WINDOW_SECONDS * 2
# GC runs at most once per 5 minutes
_CLEANUP_INTERVAL = 300


class RateLimitResult(NamedTuple):
    """Immutable result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    headers: dict[str, str]


@dataclass
class _Bucket:
    tokens: float
    last_refill: float = field(default_factory=time.monotonic)


class _TokenBucketLimiter:
    """
    Thread-safe in-process token bucket rate limiter.

    Key format: "{tier}:{ip}" — e.g., "pro:203.0.113.42"
    Tier is extracted from the key prefix to determine the limit.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, _Bucket] = {}
        self._last_cleanup = time.monotonic()

    @staticmethod
    def _limit_for_key(key: str) -> int:
        return PRO_RATE_LIMIT if key.startswith("pro:") else FREE_RATE_LIMIT

    def check(self, key: str) -> RateLimitResult:
        """
        Check whether a request identified by `key` is within the rate limit.
        Returns a RateLimitResult with headers ready to attach to the response.
        """
        limit = self._limit_for_key(key)
        rate = limit / _WINDOW_SECONDS  # tokens per second
        now = time.monotonic()

        with self._lock:
            self._maybe_gc(now)

            if key not in self._buckets:
                # First request from this key: start with (limit - 1) tokens
                self._buckets[key] = _Bucket(tokens=float(limit - 1), last_refill=now)
                return self._result(allowed=True, limit=limit, remaining=limit - 1)

            bucket = self._buckets[key]
            elapsed = now - bucket.last_refill
            # Refill tokens since last request, cap at bucket capacity
            bucket.tokens = min(float(limit), bucket.tokens + elapsed * rate)
            bucket.last_refill = now

            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return self._result(allowed=True, limit=limit, remaining=int(bucket.tokens))
            else:
                # Compute seconds until 1 token is available
                retry_after = max(1, int((1.0 - bucket.tokens) / rate))
                return self._result(
                    allowed=False, limit=limit, remaining=0, retry_after=retry_after
                )

    @staticmethod
    def _result(
        allowed: bool,
        limit: int,
        remaining: int,
        retry_after: int = 0,
    ) -> RateLimitResult:
        headers: dict[str, str] = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Window": str(_WINDOW_SECONDS),
        }
        if not allowed:
            headers["Retry-After"] = str(retry_after)
        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            retry_after_seconds=retry_after,
            headers=headers,
        )

    def _maybe_gc(self, now: float) -> None:
        """Garbage-collect stale buckets. Must be called under self._lock."""
        if now - self._last_cleanup < _CLEANUP_INTERVAL:
            return
        stale = [k for k, b in self._buckets.items() if now - b.last_refill > _STALE_THRESHOLD]
        for k in stale:
            del self._buckets[k]
        if stale:
            log.debug("ratelimit.gc", removed=len(stale))
        self._last_cleanup = now

    # ── Testing helpers ────────────────────────────────────────────────────────

    def reset(self, key: str | None = None) -> None:
        """Reset one key or all keys. For test isolation only."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)

    def bucket_state(self, key: str) -> tuple[float, float] | None:
        """Return (tokens, last_refill) for a key. For test inspection only."""
        with self._lock:
            b = self._buckets.get(key)
            return (b.tokens, b.last_refill) if b else None


# ── Module-level singleton ─────────────────────────────────────────────────────
_limiter = _TokenBucketLimiter()


def get_limiter() -> _TokenBucketLimiter:
    """Return the module-level singleton limiter."""
    return _limiter
