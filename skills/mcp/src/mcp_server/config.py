"""
AI SAFE2 MCP Server — Configuration
All configuration is read from environment variables.
Never hardcode secrets. See .env.example.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent  # skills/mcp/
DATA_DIR = ROOT_DIR / "data"
CONTROLS_JSON = DATA_DIR / "ai-safe2-controls-v3.0.json"

# ── Transport ─────────────────────────────────────────────────────────────────
TRANSPORT: Literal["stdio", "streamable-http"] = os.getenv("MCP_TRANSPORT", "stdio")  # type: ignore[assignment]
HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8000"))

# ── Auth ──────────────────────────────────────────────────────────────────────
TOKENS_RAW: str = os.getenv("TOKENS", "")


def load_token_map() -> dict[str, str]:
    """Parse TOKENS env var into {token: tier} dict."""
    token_map: dict[str, str] = {}
    for entry in TOKENS_RAW.split(","):
        entry = entry.strip()
        if ":" in entry:
            token, tier = entry.split(":", 1)
            token_map[token.strip()] = tier.strip()
    return token_map


TOKEN_MAP: dict[str, str] = load_token_map()

# ── Tiers ─────────────────────────────────────────────────────────────────────
VALID_TIERS = {"free", "pro"}
FREE_FRAMEWORK_LIMIT = 5
FREE_CONTROL_LIMIT = 30
PRO_RATE_LIMIT = 1000
FREE_RATE_LIMIT = 30

# ── STDIO Security (RISK-2 Fix) ───────────────────────────────────────────────
# Source integrity hash (opt-in). SHA-256 of all .py + controls JSON.
# Generate: python -c "from mcp_server.auth import _compute_source_hash; print(_compute_source_hash())"
MCP_SOURCE_HASH: str = os.getenv("MCP_SOURCE_HASH", "")

# Absolute install path verification (opt-in).
# If set, STDIO startup verifies __file__ resolves inside this path.
MCP_INSTALL_PATH: str = os.getenv("MCP_INSTALL_PATH", "")

# Allowed executables for STDIO invocation (comma-separated).
_raw_commands = os.getenv(
    "ALLOWED_STDIO_COMMANDS",
    "python,python3,python3.11,python3.12,python3.13,uvicorn,ai-safe2-mcp",
)
ALLOWED_STDIO_COMMANDS: set[str] = {c.strip() for c in _raw_commands.split(",") if c.strip()}

# Module patterns — at least one must appear in sys.argv for STDIO startup.
ALLOWED_STDIO_MODULE_PATTERNS: list[str] = [
    "mcp_server.app",
    "mcp_server",
    "ai-safe2-mcp",
    "__main__",
]

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

# ── Server identity ───────────────────────────────────────────────────────────
SERVER_NAME = "ai-safe2-mcp"
SERVER_VERSION = "3.0.1"
SERVER_DESCRIPTION = (
    "AI SAFE2 v3.0 MCP Server — 161-control agentic AI governance toolkit. "
    "Provides control lookup, risk scoring, compliance mapping, code review, "
    "and agent classification tools. "
    "Free tier: limited access. Pro tier: full 161 controls, 32 frameworks. "
    "Tokens: cyberstrategyinstitute.com/ai-safe2/"
)
