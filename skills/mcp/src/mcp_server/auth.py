"""
AI SAFE2 MCP Server — Auth Middleware
Bearer token validation for HTTPS transport.
STDIO startup security verification (source integrity + command/path allowlist).

Security fixes applied (v3.0.1):
  RISK-0: Sets tier in ContextVar for async-safe propagation to tool functions.
  RISK-2: verify_stdio_security() checks source hash + command allowlist + install path.
  RISK-3: Applies per-tier token bucket rate limiting inside dispatch().

Token tiers:
  free  — registered at cyberstrategyinstitute.com/ai-safe2/
  pro   — Toolkit purchaser at cyberstrategyinstitute.com/ai-safe2/

For stdio transport, auth is bypassed AFTER security checks pass.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.config import (
    ALLOWED_STDIO_COMMANDS,
    ALLOWED_STDIO_MODULE_PATTERNS,
    MCP_INSTALL_PATH,
    MCP_SOURCE_HASH,
    TOKEN_MAP,
    TRANSPORT,
)
from mcp_server.context import get_tier, set_tier
from mcp_server.ratelimit import get_limiter

log = structlog.get_logger()

_PUBLIC_PATHS = {"/health", "/", "/favicon.ico"}


# ── STDIO Security Verification (RISK-2 Fix) ──────────────────────────────────

def _verify_command_allowlist() -> tuple[bool, str]:
    """
    Verify this process was invoked via an allowed command + module pattern.

    Two-layer check:
      1. Executable name must be in ALLOWED_STDIO_COMMANDS.
      2. sys.argv must contain at least one ALLOWED_STDIO_MODULE_PATTERNS entry,
         OR the process was launched via the installed entry point (ai-safe2-mcp).

    What this defends against:
      A tampered project-level .claude/settings.json that swaps `mcp_server.app`
      for another module while still using a recognized Python binary. The argv
      check catches this case — the rogue module's name won't match our patterns.

    Known limitation:
      This cannot block a malicious settings.json that points to a completely
      different binary (e.g., command: /tmp/evil). That threat requires:
        - IDE-level MCP config signing (Claude Code roadmap item)
        - OS-level process isolation (e.g., Warden kernel containment)
      Those are complementary controls, not replaced by this check.

    If MCP_INSTALL_PATH is set, also verifies this file resolves inside that path.
    """
    if not sys.argv:
        return True, ""  # Cannot inspect args — allow (opt-in defense)

    executable = Path(sys.executable).name
    args_flat = " ".join(sys.argv)

    # Check 1: executable allowlist
    if executable not in ALLOWED_STDIO_COMMANDS:
        return False, (
            f"Executable '{executable}' not in ALLOWED_STDIO_COMMANDS. "
            f"Allowed: {sorted(ALLOWED_STDIO_COMMANDS)}"
        )

    # Check 2: module pattern or entry-point name
    module_ok = any(pat in args_flat for pat in ALLOWED_STDIO_MODULE_PATTERNS)
    entry_point_ok = "ai-safe2-mcp" in str(sys.argv[0])

    if not (module_ok or entry_point_ok):
        return False, (
            f"sys.argv '{args_flat}' does not match any allowed module pattern. "
            f"Expected one of: {ALLOWED_STDIO_MODULE_PATTERNS}. "
            "Configure ALLOWED_STDIO_MODULE_PATTERNS if using a custom entrypoint."
        )

    # Check 3: install path (opt-in)
    if MCP_INSTALL_PATH:
        server_path = str(Path(__file__).resolve())
        allowed_root = str(Path(MCP_INSTALL_PATH).resolve())
        if not server_path.startswith(allowed_root):
            return False, (
                f"Server running from '{server_path}' which is outside "
                f"MCP_INSTALL_PATH='{allowed_root}'. "
                "Possible path-substitution attack or misconfigured install."
            )

    return True, ""


def _compute_source_hash() -> str:
    """
    SHA-256 of all .py files in the mcp_server package + controls JSON.

    Files are sorted and hashed with their names for determinism.
    The controls JSON is included because it is the primary data supply-chain
    attack surface (RISK-1: injection via poisoned control descriptions).

    Generate at release time:
      python -c "from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())"

    Store the output in MCP_SOURCE_HASH env var to enable verification.
    """
    src_dir = Path(__file__).parent
    # Resolve data dir relative to package (works regardless of CWD)
    data_dir = src_dir.parent.parent / "data"

    combined = hashlib.sha256()

    for f in sorted(src_dir.rglob("*.py")):
        combined.update(f.name.encode("utf-8"))
        combined.update(f.read_bytes())

    controls_json = data_dir / "ai-safe2-controls-v3.0.json"
    if controls_json.exists():
        combined.update(b"ai-safe2-controls-v3.0.json")
        combined.update(controls_json.read_bytes())

    return combined.hexdigest()


def _verify_source_integrity() -> tuple[bool, str]:
    """
    Compare computed source hash against MCP_SOURCE_HASH.
    Returns (True, "") if verification passes or is not configured.
    Returns (False, reason) on mismatch.
    """
    if not MCP_SOURCE_HASH:
        return True, ""  # Opt-in — not configured

    actual = _compute_source_hash()
    if actual != MCP_SOURCE_HASH:
        return False, (
            f"Source integrity FAILED. "
            f"Expected: {MCP_SOURCE_HASH[:16]}... "
            f"Actual: {actual[:16]}... "
            "Source files or controls data may have been tampered. Blocking startup."
        )

    log.info("auth.stdio_integrity_ok", hash_prefix=actual[:16])
    return True, ""


def verify_stdio_security() -> None:
    """
    Run all STDIO security checks before starting the server.
    Calls sys.exit(1) on any failure (fail-closed).

    Called once from main() before mcp.run(transport='stdio').
    """
    ok, reason = _verify_command_allowlist()
    if not ok:
        log.error("auth.stdio_command_violation", reason=reason, action="blocking_startup")
        sys.exit(1)

    ok, reason = _verify_source_integrity()
    if not ok:
        log.error("auth.stdio_integrity_failure", reason=reason, action="blocking_startup")
        sys.exit(1)

    log.info("auth.stdio_security_checks_passed")


# ── Bearer Auth + Rate Limit Middleware (RISK-0, RISK-3 Fix) ─────────────────

class BearerAuthMiddleware(BaseHTTPMiddleware):
    """
    HTTP bearer token validation + per-tier rate limiting.

    RISK-0 FIX: Sets tier in ContextVar (mcp_server.context) immediately after
    token validation so tool functions can read it via get_tier(). Replaces the
    broken _current_request = None module-level global.

    RISK-3 FIX: Applies token bucket rate limiting (mcp_server.ratelimit) after
    tier is resolved. Key format: "{tier}:{client_ip}" — prevents free-tier keys
    from consuming pro-tier token budget.
    """

    async def dispatch(self, request: Request, call_next):
        # ── STDIO: security checks ran at startup; grant Pro and proceed ─────
        if TRANSPORT == "stdio":
            set_tier("pro")
            return await call_next(request)

        # ── Public paths: no auth, no rate limit ─────────────────────────────
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # ── Bearer token validation ───────────────────────────────────────────
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

        # ── Propagate tier via ContextVar (RISK-0 FIX) ───────────────────────
        request.state.tier = tier
        set_tier(tier)
        log.debug("auth.ok", tier=tier, path=request.url.path)

        # ── Rate limiting (RISK-3 FIX) ────────────────────────────────────────
        client_ip = (request.client.host if request.client else "unknown")
        rate_key = f"{tier}:{client_ip}"
        rl_result = get_limiter().check(rate_key)

        if not rl_result.allowed:
            log.warning(
                "ratelimit.exceeded",
                tier=tier,
                ip=client_ip,
                retry_after=rl_result.retry_after_seconds,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": (
                        f"You have exceeded the {tier} tier limit of "
                        f"{rl_result.limit} requests/hour. "
                        f"Retry after {rl_result.retry_after_seconds} seconds."
                    ),
                    "retry_after_seconds": rl_result.retry_after_seconds,
                },
                headers=rl_result.headers,
            )

        response = await call_next(request)

        # Attach rate limit state headers to every successful response
        for k, v in rl_result.headers.items():
            response.headers[k] = v

        return response


def get_tier_from_request(request: Request | None) -> str:
    """
    Return the tier for the current request.
    Reads from ContextVar (RISK-0 FIX). Kept for backward compatibility.
    """
    if TRANSPORT == "stdio":
        return "pro"
    return get_tier()
