"""`safe2 mcp` - consumer-side MCP runtime protection (mcp-safe-wrap, absorbed).

`scan`/`gate`/`score`/`report` cover the static and remote-assessment legs
of the MCP Security Toolkit. This module covers the third leg: wrapping a
live MCP connection (stdio or HTTP) with injection scanning, audit
logging, and rate limiting at runtime.

`safe2 mcp serve` is intentionally a stub. The AI SAFE2 MCP Server
(skills/mcp — a 388-line async server exposing the 161 controls as MCP
resources/tools) is a different product from the MCP Security Toolkit
absorbed here, and folding it in without a full read-through would mean
claiming an integration this pass didn't actually verify. Flagging that
honestly rather than faking it; wiring it in is the natural next PR.
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys

import click


@click.group()
def mcp():
    """MCP-specific operations: runtime wrapping, plus thin launchers for the knowledge server and gateway."""


@mcp.command("wrap-stdio")
@click.argument("command", nargs=-1, required=True)
@click.option("--audit-log", default="~/.safe2/mcp-audit.jsonl")
@click.option("--scan-inputs/--no-scan-inputs", default=True)
@click.option("--scan-outputs/--no-scan-outputs", default=True)
@click.option("--block/--log-only", default=True, help="Block injections (default) or log-only mode")
@click.option("--rate-limit", default=0, type=int, help="Max requests/hour/session (0=disabled)")
def wrap_stdio(command, audit_log, scan_inputs, scan_outputs, block, rate_limit):
    """Wrap a STDIO MCP server with injection scanning and audit logging.

    \b
    Example:
      safe2 mcp wrap-stdio -- python -m mcp_server.app
    """
    from aisafe2_mcp_tools.wrap.wrapper import StdioWrapper

    wrapper = StdioWrapper(
        command=list(command),
        audit_log=audit_log,
        scan_inputs=scan_inputs,
        scan_outputs=scan_outputs,
        block_on_match=block,
        rate_limit=rate_limit,
    )
    try:
        asyncio.run(wrapper.run())
    except KeyboardInterrupt:
        pass


@mcp.command("wrap-proxy")
@click.argument("target_url")
@click.option("--token", "-t", default=None)
@click.option("--local-port", default=8080, type=int)
@click.option("--scan-inputs/--no-scan-inputs", default=True)
@click.option("--scan-outputs/--no-scan-outputs", default=True)
@click.option("--audit-log", default="~/.safe2/mcp-audit.jsonl")
@click.option("--rate-limit", default=100, type=int, help="Max requests/hour/IP")
@click.option("--pin-schema", is_flag=True, default=False, help="MCP-11: alert on tools/list schema drift")
def wrap_proxy(target_url, token, local_port, scan_inputs, scan_outputs, audit_log, rate_limit, pin_schema):
    """Run a local HTTP proxy wrapping a remote MCP server."""
    from aisafe2_mcp_tools.wrap.proxy import run_proxy

    try:
        asyncio.run(
            run_proxy(
                target_url=target_url,
                token=token,
                local_port=local_port,
                scan_inputs=scan_inputs,
                scan_outputs=scan_outputs,
                audit_log_path=audit_log,
                rate_limit=rate_limit,
                pin_schema=pin_schema,
            )
        )
    except KeyboardInterrupt:
        pass


@mcp.command("serve")
def mcp_serve():
    """[stub] Launch the AI SAFE2 MCP knowledge server - not yet wired into safe2. See module docstring."""
    if shutil.which("ai-safe2-mcp"):
        click.echo("Found ai-safe2-mcp on PATH - launching it directly (not yet a native safe2 integration).")
        raise SystemExit(subprocess.call(["ai-safe2-mcp"]))
    click.echo(
        "`safe2 mcp serve` is not wired up yet - this pass absorbed the MCP Security\n"
        "Toolkit (scan/score/wrap) but deliberately left the AI SAFE2 MCP knowledge\n"
        "server (skills/mcp) out rather than fake-integrate it. For now:\n"
        "  pip install -e skills/mcp && ai-safe2-mcp\n",
        err=True,
    )
    sys.exit(3)
