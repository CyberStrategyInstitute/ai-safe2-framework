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
HOST = os.getenv("MCP_HOST", "127.0.0.1")   # bind to localhost only; Caddy handles TLS
PORT = int(os.getenv("MCP_PORT", "8000"))

# ── Auth ──────────────────────────────────────────────────────────────────────
# Tokens are managed externally (cyberstrategyinstitute.com/ai-safe2/).
# The MCP server only validates — it never issues tokens.
# Format: TOKENS env var = comma-separated list of "token:tier" pairs
# Example: TOKENS="free_abc123:free,pro_xyz789:pro"
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
# free:  email registration at cyberstrategyinstitute.com/ai-safe2/
# pro:   Toolkit purchase ($97) at cyberstrategyinstitute.com/ai-safe2/
VALID_TIERS = {"free", "pro"}

FREE_FRAMEWORK_LIMIT = 5          # frameworks returned in compliance mapping
FREE_CONTROL_LIMIT = 30           # controls returned in lookup results
PRO_RATE_LIMIT = 1000             # requests per hour
FREE_RATE_LIMIT = 30              # requests per hour

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")   # "json" or "console"

# ── Server identity ───────────────────────────────────────────────────────────
SERVER_NAME = "ai-safe2-mcp"
SERVER_VERSION = "3.0.0"
SERVER_DESCRIPTION = (
    "AI SAFE2 v3.0 MCP Server — 161-control agentic AI governance toolkit. "
    "Provides control lookup, risk scoring, compliance mapping, code review, "
    "and agent classification tools. "
    "Free tier: limited access. Pro tier: full 161 controls, 32 frameworks. "
    "Tokens: cyberstrategyinstitute.com/ai-safe2/"
)
