"""
AI SAFE2 MCP Server — Auth Middleware
Bearer token validation for HTTPS transport.
Tokens are issued externally; this module only validates.

Token tiers:
  free  — registered at cyberstrategyinstitute.com/ai-safe2/ (email required)
  pro   — Toolkit purchaser at cyberstrategyinstitute.com/ai-safe2/

For stdio transport (local use), auth is bypassed — stdio is inherently
scoped to the local process, with no network exposure.
"""
from __future__ import annotations

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.config import TOKEN_MAP, TRANSPORT

log = structlog.get_logger()

# Paths that skip auth entirely
_PUBLIC_PATHS = {"/health", "/", "/favicon.ico"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """
    Validates Authorization: Bearer <token> header for all MCP endpoints.
    Skips auth for health check and root paths.
    Attaches tier to request.state for downstream access control.
    """

    async def dispatch(self, request: Request, call_next):
        if TRANSPORT == "stdio":
            # stdio is local-only — no network, no auth needed
            request.state.tier = "pro"
            return await call_next(request)

        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            log.warning("auth.missing_token", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Missing Authorization header",
                    "detail": (
                        "Include: Authorization: Bearer <your-token>. "
                        "Get a token at cyberstrategyinstitute.com/ai-safe2/"
                    ),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        tier = TOKEN_MAP.get(token)

        if tier is None:
            log.warning("auth.invalid_token", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid or expired token",
                    "detail": (
                        "Register for a free token or purchase the Toolkit at "
                        "cyberstrategyinstitute.com/ai-safe2/"
                    ),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.tier = tier
        log.debug("auth.ok", tier=tier, path=request.url.path)
        return await call_next(request)


def get_tier_from_request(request: Request | None) -> str:
    """
    Return the tier for the current request.
    Falls back to 'free' if tier is not set (should not happen in practice).
    For stdio transport, always returns 'pro'.
    """
    if TRANSPORT == "stdio":
        return "pro"
    if request is None:
        return "free"
    return getattr(request.state, "tier", "free")
