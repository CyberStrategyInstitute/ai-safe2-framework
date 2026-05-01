"""mcp-safe-wrap CLI entry point."""
from __future__ import annotations
import asyncio
import sys
import click


@click.group()
def cli():
    """
    mcp-safe-wrap — AI SAFE2 v3.0 Consumer-Side MCP Protection

    \b
    STDIO mode:  mcp-safe-wrap stdio -- python -m mcp_server.app
    HTTP proxy:  mcp-safe-wrap proxy https://external-mcp.example/mcp
    """


@cli.command()
@click.argument("command", nargs=-1, required=True)
@click.option("--audit-log", default="~/.mcp-safe-wrap/audit.jsonl")
@click.option("--scan-inputs/--no-scan-inputs", default=True)
@click.option("--scan-outputs/--no-scan-outputs", default=True)
@click.option("--block/--log-only", default=True,
              help="Block injections (default) or log-only mode")
@click.option("--rate-limit", default=0, type=int,
              help="Max requests per hour per session (0=disabled)")
def stdio(command, audit_log, scan_inputs, scan_outputs, block, rate_limit):
    """
    Wrap a STDIO MCP server with injection scanning and audit logging.

    \b
    Examples:
      mcp-safe-wrap stdio -- python -m mcp_server.app
      mcp-safe-wrap stdio --log-only -- node dist/server.js

    \b
    Claude Code config (.claude/settings.json):
      {
        "mcpServers": {
          "safe-server": {
            "command": "mcp-safe-wrap",
            "args": ["stdio", "--", "python", "-m", "mcp_server.app"],
            "env": {"PYTHONPATH": "/path/to/src"}
          }
        }
      }
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


@cli.command()
@click.argument("target_url")
@click.option("--token", "-t", default=None)
@click.option("--local-port", default=8080, type=int)
@click.option("--scan-inputs/--no-scan-inputs", default=True)
@click.option("--scan-outputs/--no-scan-outputs", default=True)
@click.option("--audit-log", default="~/.mcp-safe-wrap/audit.jsonl")
@click.option("--rate-limit", default=100, type=int,
              help="Max requests per hour per IP (default: 100)")
def proxy(target_url, token, local_port, scan_inputs, scan_outputs, audit_log, rate_limit):
    """
    Run a local HTTP proxy wrapping a remote MCP server.

    \b
    Examples:
      mcp-safe-wrap proxy https://external-mcp.example/mcp --token pro_xyz
      mcp-safe-wrap proxy https://external-mcp.example/mcp --local-port 8081

    \b
    Claude Code config:
      {"type": "http", "url": "http://localhost:8080/proxy"}
    """
    from aisafe2_mcp_tools.wrap.proxy import run_proxy
    try:
        asyncio.run(run_proxy(
            target_url=target_url,
            token=token,
            local_port=local_port,
            scan_inputs=scan_inputs,
            scan_outputs=scan_outputs,
            audit_log_path=audit_log,
            rate_limit=rate_limit,
        ))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
