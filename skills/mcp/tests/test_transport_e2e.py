"""
End-to-end transport tests: a real MCP client against a real server process.

The unit suite imported tool functions directly and never started the server,
which let three release-blocking defects ship:
  - mcp 2.x removed FastMCP, so a fresh install could not import the server;
  - streamable HTTP returned 500 on every authenticated request (lifespan lost);
  - local stdio sessions silently ran on the free tier.
These tests start the server the way users do and talk to it over MCP.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
PRO = "protok12345678901234567"
FREE = "freetok123456789012345"

mcp = pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402


def _text(result) -> str:
    return "".join(getattr(c, "text", "") for c in result.content)


def _env(**extra) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MCP_", "TOKENS"))}
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    env.update(extra)
    return env


async def _stdio_call(env: dict, tool: str, args: dict) -> tuple[list[str], str]:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "mcp_server.app"], env=env, cwd=str(SRC)
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            return tools, _text(await s.call_tool(tool, args))


def test_server_module_imports_with_installed_mcp():
    """Regression for M1: the pinned mcp version must provide the v1 API used."""
    from mcp.server.fastmcp import FastMCP  # noqa: F401

    major = int(mcp.__version__.split(".")[0]) if hasattr(mcp, "__version__") else 1
    assert major < 2


def test_stdio_handshake_lists_tools_and_grants_configured_tier():
    """Regression for M1 + M3: stdio starts, serves tools, and runs Pro by default."""
    tools, body = asyncio.run(
        _stdio_call(_env(MCP_TRANSPORT="stdio"), "code_review",
                    {"code": "eval(x)", "language": "python"})
    )
    assert {"lookup_control", "risk_score", "code_review", "agent_classify"} <= set(tools)
    assert "Upgrade required" not in body
    assert json.loads(body)["meta"]["tier"] == "pro"


def test_stdio_tier_can_be_set_to_free():
    _, body = asyncio.run(
        _stdio_call(_env(MCP_TRANSPORT="stdio", MCP_STDIO_TIER="free"), "code_review",
                    {"code": "eval(x)", "language": "python"})
    )
    assert "Upgrade required" in body


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def http_server():
    port = _free_port()
    env = _env(MCP_TRANSPORT="streamable-http", MCP_HOST="127.0.0.1", MCP_PORT=str(port),
               TOKENS=f"{FREE}:free,{PRO}:pro", AUTH_FAIL_RATE_LIMIT="5",
               NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    proc = subprocess.Popen([sys.executable, "-m", "mcp_server.app"], env=env, cwd=str(SRC),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(f"{base}/health", timeout=0.5, trust_env=False).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("HTTP server did not start: " + proc.stderr.read().decode()[-500:])
    yield base
    proc.terminate()
    proc.wait(timeout=10)


async def _http_call(base: str, token: str, auth_scheme: str = "Bearer") -> tuple[int, str]:
    async with streamablehttp_client(
        f"{base}/mcp", headers={"Authorization": f"{auth_scheme} {token}"}
    ) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            n = len((await s.list_tools()).tools)
            return n, _text(await s.call_tool("lookup_control", {"control_id": "MCP-19"}))


def test_http_authenticated_session_works(http_server):
    """Regression for M2: authenticated requests previously returned HTTP 500."""
    n, body = asyncio.run(_http_call(http_server, PRO))
    assert n >= 5
    assert "MCP-19" in body


def test_http_bearer_scheme_is_case_insensitive(http_server):
    """Regression for M4 (RFC 7235): 'bearer' must be accepted like 'Bearer'."""
    n, _ = asyncio.run(_http_call(http_server, PRO, auth_scheme="bearer"))
    assert n >= 5


def test_http_failed_auth_lockout_is_not_an_oracle(http_server):
    """Regression for M4: failed attempts are budgeted per IP, and a locked-out
    client is refused even with a valid token (a correct guess must not differ)."""
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "t", "version": "1"}}}
    headers = {"Accept": "application/json, text/event-stream"}
    codes = [
        httpx.post(f"{http_server}/mcp", json=init, timeout=5, trust_env=False,
                   headers={**headers, "Authorization": f"Bearer wrong{i}"}).status_code
        for i in range(8)
    ]
    assert codes[0] == 401
    assert 429 in codes
    valid = httpx.post(f"{http_server}/mcp", json=init, timeout=5, trust_env=False,
                       headers={**headers, "Authorization": f"Bearer {PRO}"})
    assert valid.status_code == 429
