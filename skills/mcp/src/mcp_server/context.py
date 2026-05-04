"""
AI SAFE2 MCP Server — Request Context (RISK-0 FIX)

Async-safe tier propagation using Python's contextvars module.

Replaces the broken module-level `_current_request: Request | None = None`
pattern in the original app.py, which caused all HTTP-transport tool calls
to silently fall back to "free" tier regardless of the authenticated token.

Why ContextVar:
  - Python's asyncio copies context into each new coroutine/task
  - Each HTTP request gets its own copy — no cross-request contamination
  - Thread-safe and async-safe by design (no locks required)
  - Works identically for stdio (where tier is always "pro")
"""
from __future__ import annotations

from contextvars import ContextVar, Token

# Default: "free" — fail-secure. Never grant elevated access without explicit auth.
_tier_var: ContextVar[str] = ContextVar("mcp_request_tier", default="free")


def set_tier(tier: str) -> Token:
    """
    Set the tier for the current async context.
    Called by BearerAuthMiddleware immediately after token validation.
    Returns a Token that can reset the value (used in tests).
    """
    return _tier_var.set(tier)


def get_tier() -> str:
    """
    Get the tier for the current async context.
    Returns 'free' if not explicitly set (fail-secure default).
    """
    return _tier_var.get()


def reset_tier(token: Token) -> None:
    """Reset tier to its previous value. Used in test isolation."""
    _tier_var.reset(token)
