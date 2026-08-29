"""
AI SAFE2 MCP Server: configuration.
All configuration is read from environment variables.
Never hardcode secrets. See .env.example.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

# v3.1 does not add six new top-level framework controls. The 161-control core
# taxonomy is retained and the CP.5.MCP profile is layered on top explicitly.
# This avoids duplicating the full core dataset while making MCP-1 through
# MCP-19 queryable as profile controls.
CONTROLS_JSON = DATA_DIR / "ai-safe2-controls-v3.0.json"
MCP_PROFILE_JSON = DATA_DIR / "mcp-profile-v3.1.json"
FRAMEWORK_VERSION = "3.1.0"
MCP_SPEC_VERSION = "2026-07-28"

TRANSPORT: Literal["stdio", "streamable-http"] = os.getenv("MCP_TRANSPORT", "stdio")  # type: ignore[assignment]
HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8000"))

TOKENS_RAW: str = os.getenv("TOKENS", "")
MCP_AUTH_AUDIENCE: str = os.getenv("MCP_AUTH_AUDIENCE", "")


def load_token_map() -> dict[str, str]:
    """Parse legacy TOKENS into {token: tier}. Compatibility only for MCP-19."""
    token_map: dict[str, str] = {}
    for entry in TOKENS_RAW.split(","):
        entry = entry.strip()
        if ":" in entry:
            token, tier = entry.split(":", 1)
            token_map[token.strip()] = tier.strip()
    return token_map


TOKEN_MAP: dict[str, str] = load_token_map()

VALID_TIERS = {"free", "pro"}
FREE_FRAMEWORK_LIMIT = 5
FREE_CONTROL_LIMIT = 30
PRO_RATE_LIMIT = 1000
FREE_RATE_LIMIT = 30

MCP_SOURCE_HASH: str = os.getenv("MCP_SOURCE_HASH", "")
MCP_INSTALL_PATH: str = os.getenv("MCP_INSTALL_PATH", "")
_raw_commands = os.getenv(
    "ALLOWED_STDIO_COMMANDS",
    "python,python3,python3.11,python3.12,python3.13,uvicorn,ai-safe2-mcp",
)
ALLOWED_STDIO_COMMANDS: set[str] = {c.strip() for c in _raw_commands.split(",") if c.strip()}
ALLOWED_STDIO_MODULE_PATTERNS: list[str] = [
    "mcp_server.app",
    "mcp_server",
    "ai-safe2-mcp",
    "__main__",
]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

SERVER_NAME = "ai-safe2-mcp"
SERVER_VERSION = FRAMEWORK_VERSION
SERVER_DESCRIPTION = (
    "AI SAFE2 v3.1 MCP Server: 161-control agentic AI governance toolkit with "
    "a CP.5.MCP profile aligned to MCP 2026-07-28. Provides control lookup, risk "
    "scoring, compliance mapping, code review, and agent classification tools. "
    "Legacy opaque bearer tokens remain supported for entitlement compatibility but "
    "do not by themselves establish MCP-19 audience-validation conformance."
)
