"""
AI SAFE2 MCP Security Toolkit — mcp-safe-wrap: HTTP Proxy
Runs a local Starlette ASGI proxy that wraps a remote MCP HTTP server.

The proxy sits between your AI client (Claude Code, Codex, Cursor) and
any external MCP HTTP server. It provides:
  - Injection scanning on all tool call parameters (input)
  - Injection scanning on all tool call responses (output)
  - SSRF URL blocklist enforcement
  - Per-IP async token bucket rate limiting
  - Immutable JSONL audit log of every tool invocation

Connect Claude Code to http://127.0.0.1:{local_port}/proxy instead of
the real server URL.

Supports: MCP streamable-http (JSON-RPC over POST)
Limitation: SSE streaming not supported (roadmap item for v1.1)
"""
from __future__ import annotations

import sys
from collections import defaultdict

import structlog

from aisafe2_mcp_tools.wrap.audit import AuditLog
from aisafe2_mcp_tools.wrap.ratelimit import AsyncTokenBucket, make_async_bucket
from aisafe2_mcp_tools.wrap.scanner import MessageScanner

log = structlog.get_logger()


async def run_proxy(
    target_url: str,
    token: str | None,
    local_port: int,
    scan_inputs: bool,
    scan_outputs: bool,
    audit_log_path: str | None,
    rate_limit: int,
) -> None:
    """
    Start the HTTP proxy server.

    Args:
        target_url:      Full URL of the remote MCP server (e.g. https://example.com/mcp)
        token:           Bearer token for the remote server (optional)
        local_port:      Local port to bind to (default 8080)
        scan_inputs:     Scan outbound request parameters for injection
        scan_outputs:    Scan inbound tool responses for injection
        audit_log_path:  Path to JSONL audit log file (None to disable)
        rate_limit:      Max requests per hour per IP (0 to disable)
    """
    try:
        import httpx
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        import uvicorn
    except ImportError:
        print(
            "HTTP proxy mode requires: pip install 'aisafe2-mcp-tools[proxy]'\n"
            "or: pip install starlette uvicorn httpx",
            file=sys.stderr,
        )
        sys.exit(1)

    audit = AuditLog(audit_log_path)
    scanner = MessageScanner()
    ip_buckets: dict[str, AsyncTokenBucket] = defaultdict(
        lambda: make_async_bucket(rate_limit)
    )

    upstream_headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        upstream_headers["Authorization"] = f"Bearer {token}"

    async def handle_proxy(request: Request) -> JSONResponse:
        client_ip = request.client.host if request.client else "unknown"

        # Rate limiting
        if rate_limit > 0 and not await ip_buckets[client_ip].consume():
            log.warning("proxy.rate_limited", ip=client_ip)
            return JSONResponse(
                {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Rate limit exceeded"}},
                status_code=429,
                headers={"Retry-After": "60"},
            )

        # Parse request body
        try:
            body: dict = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )

        method = body.get("method", "")

        # Scan outbound (input) with injection + SSRF checks
        if scan_inputs:
            sanitized_body, input_findings = scanner.scan(body, "input")
            ssrf_findings = scanner.check_ssrf(body)
            all_input = list(input_findings) + ssrf_findings
            if all_input:
                log.warning("proxy.input_injection", ip=client_ip, count=len(all_input))
                audit.write_injection("input", all_input, method, client_ip)
                for sf in ssrf_findings:
                    audit.write_ssrf_blocked(sf.get("field_path", ""), client_ip)
            body = sanitized_body if isinstance(sanitized_body, dict) else body

        # Forward to upstream
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            try:
                resp = await client.post(target_url, headers=upstream_headers, json=body)
                response_data: dict = resp.json()
            except httpx.ConnectError as exc:
                return JSONResponse(
                    {"jsonrpc": "2.0", "error": {"code": -32001, "message": f"Upstream error: {exc}"}},
                    status_code=502,
                )
            except Exception as exc:
                return JSONResponse(
                    {"jsonrpc": "2.0", "error": {"code": -32002, "message": str(type(exc).__name__)}},
                    status_code=502,
                )

        # Scan inbound (output) — tool responses going to LLM client
        if scan_outputs:
            sanitized_resp, output_findings = scanner.scan(response_data, "output")
            if output_findings:
                log.warning("proxy.output_injection", ip=client_ip, count=len(output_findings))
                audit.write_injection(
                    "output", output_findings, method, client_ip,
                    scanner.extract_tool_name(body),
                )
            response_data = sanitized_resp if isinstance(sanitized_resp, dict) else response_data

        # Audit tool invocations (MCP-5)
        if "tool" in method.lower() or method == "tools/call":
            audit.write_tool_invocation(method, scanner.extract_tool_name(body), client_ip)

        return JSONResponse(response_data)

    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "proxy": "mcp-safe-wrap", "target": target_url})

    app = Starlette(routes=[
        Route("/health", health, methods=["GET"]),
        Route("/proxy", handle_proxy, methods=["POST"]),
        Route("/proxy/{path:path}", handle_proxy, methods=["POST", "GET"]),
    ])

    audit.write_proxy_start(target_url, local_port)
    print(
        f"\nmcp-safe-wrap HTTP Proxy — AI SAFE2 v3.0 CP.5.MCP\n"
        f"  Target:       {target_url}\n"
        f"  Local:        http://127.0.0.1:{local_port}/proxy\n"
        f"  Scan inputs:  {scan_inputs}\n"
        f"  Scan outputs: {scan_outputs}\n"
        f"  Rate limit:   {f'{rate_limit}/hr per IP' if rate_limit > 0 else 'disabled'}\n"
        f"  Audit log:    {audit_log_path or 'disabled'}\n\n"
        f"  Connect Claude Code to: http://127.0.0.1:{local_port}/proxy\n",
        file=sys.stderr,
    )

    config = uvicorn.Config(app, host="127.0.0.1", port=local_port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()
