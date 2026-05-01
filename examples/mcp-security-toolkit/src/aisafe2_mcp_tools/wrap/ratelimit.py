"""
AI SAFE2 MCP Security Toolkit — mcp-safe-wrap: Rate Limiter
Consumer-side token bucket rate limiter for the STDIO wrapper and HTTP proxy.

Separated from the score package's ratelimit.py because:
  - wrap uses both sync (STDIO) and async (HTTP proxy) consumption
  - wrap needs per-IP keying for the proxy
  - wrap has different limits than the MCP server itself

The async version uses asyncio.Lock for coroutine safety.
The sync version uses no lock (single-threaded STDIO context).
"""
from __future__ import annotations

import asyncio
import time


class SyncTokenBucket:
    """
    Synchronous token bucket for STDIO wrapper (single-threaded context).
    No asyncio dependency required.
    """
    __slots__ = ("_rate", "_tokens", "_last", "_capacity")

    def __init__(self, rate_per_hour: int) -> None:
        self._capacity = float(rate_per_hour)
        self._rate = float(rate_per_hour) / 3600.0
        self._tokens = float(rate_per_hour)  # Start full (burst allowed)
        self._last = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        self._tokens = min(
            self._capacity,
            self._tokens + (now - self._last) * self._rate,
        )
        self._last = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    @property
    def remaining(self) -> float:
        return self._tokens


class AsyncTokenBucket:
    """
    Async token bucket for HTTP proxy (concurrent coroutine context).
    asyncio.Lock ensures no token double-spending under concurrent requests.
    """
    __slots__ = ("_rate", "_tokens", "_last", "_capacity", "_lock")

    def __init__(self, rate_per_hour: int) -> None:
        self._capacity = float(rate_per_hour)
        self._rate = float(rate_per_hour) / 3600.0
        self._tokens = float(rate_per_hour)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(
                self._capacity,
                self._tokens + (now - self._last) * self._rate,
            )
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    @property
    def capacity(self) -> int:
        return int(self._capacity)


def make_sync_bucket(rate_per_hour: int) -> SyncTokenBucket | None:
    """Return a SyncTokenBucket or None if rate limiting is disabled (0)."""
    return SyncTokenBucket(rate_per_hour) if rate_per_hour > 0 else None


def make_async_bucket(rate_per_hour: int) -> AsyncTokenBucket:
    """
    Return an AsyncTokenBucket. If rate_per_hour is 0, returns a bucket
    with effectively unlimited capacity (10_000_000/hr).
    """
    return AsyncTokenBucket(rate_per_hour if rate_per_hour > 0 else 10_000_000)
