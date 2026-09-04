"""
AI SAFE2 MCP Security Toolkit — mcp-safe-wrap: STDIO Wrapper
Intercepts the OS pipe between your MCP client and any local MCP server.

Sub-modules:
  scanner.py   — MessageScanner (injection + SSRF detection)
  ratelimit.py — SyncTokenBucket
  audit.py     — AuditLog (JSONL append-only)
  proxy.py     — run_proxy() (HTTP proxy mode)

Wire format guarantee: scan_inputs/scan_outputs=False passes original bytes unchanged.
BUG-1 fix: asyncio.get_running_loop() throughout.
BUG-2 fix: only re-serializes JSON when scan actually runs.
"""
from __future__ import annotations

import asyncio
import json
import sys

import structlog

from aisafe2_mcp_tools.wrap.audit import AuditLog
from aisafe2_mcp_tools.wrap.ratelimit import SyncTokenBucket, make_sync_bucket
from aisafe2_mcp_tools.wrap.scanner import MessageScanner

log = structlog.get_logger()


class StdioWrapper:
    """Wraps any STDIO MCP server with injection scanning and audit logging."""

    def __init__(
        self,
        command: list[str],
        audit_log: str | None = None,
        scan_inputs: bool = True,
        scan_outputs: bool = True,
        block_on_match: bool = True,
        rate_limit: int = 0,
    ) -> None:
        if not command:
            raise ValueError("command must be non-empty")
        self.command = command
        self.scan_inputs = scan_inputs
        self.scan_outputs = scan_outputs
        self.block_on_match = block_on_match
        self._scanner = MessageScanner()
        self._audit = AuditLog(audit_log)
        self._bucket: SyncTokenBucket | None = make_sync_bucket(rate_limit)

    async def run(self) -> None:
        proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if proc.stdin is None or proc.stdout is None or proc.stderr is None:
            proc.kill()
            await proc.wait()
            raise RuntimeError("MCP subprocess did not expose all requested pipes")
        try:
            await asyncio.gather(
                self._client_to_server(proc),
                self._server_to_client(proc),
                self._relay_stderr(proc),
                return_exceptions=True,
            )
        finally:
            try:
                proc.terminate()
            except ProcessLookupError:
                pass

    async def _client_to_server(self, proc: asyncio.subprocess.Process) -> None:
        stdin = proc.stdin
        if stdin is None:
            raise RuntimeError("MCP subprocess stdin pipe is unavailable")
        loop = asyncio.get_running_loop()  # BUG-1 fix
        reader = asyncio.StreamReader(limit=2 ** 20)
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                if self._bucket and not self._bucket.consume():
                    log.warning("wrap.stdio.rate_limited")
                    continue
                if self.scan_inputs:
                    msg = self._scanner.parse_json_line(line)
                    if msg is not None:
                        sanitized, findings = self._scanner.scan(msg, "input")
                        ssrf = self._scanner.check_ssrf(msg)
                        all_f = findings + ssrf
                        if all_f:
                            self._audit.write_injection("input", all_f, msg.get("method", ""))
                            if self.block_on_match:
                                continue
                        stdin.write(json.dumps(sanitized).encode() + b"\n")
                    else:
                        stdin.write(line)  # BUG-2 fix: unchanged bytes
                else:
                    stdin.write(line)  # BUG-2 fix: unchanged bytes
                await stdin.drain()
            except (asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
                break

    async def _server_to_client(self, proc: asyncio.subprocess.Process) -> None:
        stdout = proc.stdout
        if stdout is None:
            raise RuntimeError("MCP subprocess stdout pipe is unavailable")
        while True:
            try:
                line = await stdout.readline()
                if not line:
                    break
                if self.scan_outputs:
                    msg = self._scanner.parse_json_line(line)
                    if msg is not None:
                        sanitized, findings = self._scanner.scan(msg, "output")
                        if findings:
                            self._audit.write_injection("output", findings,
                                                        msg.get("method", ""),
                                                        tool_name=self._scanner.extract_tool_name(msg))
                            log.warning("wrap.stdio.injection", count=len(findings))
                        sys.stdout.buffer.write(json.dumps(sanitized).encode() + b"\n")
                    else:
                        sys.stdout.buffer.write(line)
                else:
                    sys.stdout.buffer.write(line)  # BUG-2 fix: unchanged bytes
                sys.stdout.buffer.flush()
            except (asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
                break

    async def _relay_stderr(self, proc: asyncio.subprocess.Process) -> None:
        stderr = proc.stderr
        if stderr is None:
            raise RuntimeError("MCP subprocess stderr pipe is unavailable")
        while True:
            try:
                line = await stderr.readline()
                if not line:
                    break
                sys.stderr.buffer.write(line)
                sys.stderr.buffer.flush()
            except (asyncio.CancelledError, BrokenPipeError):
                break
