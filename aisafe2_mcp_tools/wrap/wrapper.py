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

from aisafe2_mcp_tools.wrap import policy
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
        pin_schema: bool = False,
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
        self.pin_schema = pin_schema
        self._pinned_catalog: str | None = None
        # JSON-RPC id -> (method, tool name): responses carry neither, and the
        # audit trail previously recorded empty method/tool fields.
        self._pending: dict[str, tuple[str, str]] = {}

    def _emit(self, msg: dict) -> None:
        sys.stdout.buffer.write(json.dumps(msg).encode() + b"\n")
        sys.stdout.buffer.flush()

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
                msg = self._scanner.parse_json_line(line)
                if msg is not None and "id" in msg and "method" in msg:
                    tool = ""
                    params = msg.get("params")
                    if isinstance(params, dict):
                        tool = str(params.get("name", ""))
                    self._pending[str(msg["id"])] = (str(msg["method"]), tool)
                if self.scan_inputs:
                    if msg is not None:
                        sanitized, findings = self._scanner.scan(msg, "input")
                        ssrf = self._scanner.check_ssrf(msg)
                        all_f = findings + ssrf
                        if all_f:
                            method, tool = self._pending.get(str(msg.get("id")), (msg.get("method", ""), ""))
                            self._audit.write_injection("input", all_f, method, tool_name=tool)
                            if self.block_on_match:
                                self._audit.write_policy_action("input_blocked", method, tool)
                                if "id" in msg:
                                    # Answer the client instead of leaving it waiting forever.
                                    self._pending.pop(str(msg["id"]), None)
                                    self._emit(policy.jsonrpc_error(
                                        msg["id"], policy.CODE_INPUT_BLOCKED,
                                        "AI SAFE2: request blocked - hostile content in arguments",
                                        {"families": sorted({str(f.get("family", "")) for f in all_f})},
                                    ))
                                continue
                        stdin.write(json.dumps(sanitized).encode() + b"\n")
                    else:
                        stdin.write(line)  # BUG-2 fix: unchanged bytes
                else:
                    stdin.write(line)  # BUG-2 fix: unchanged bytes
                await stdin.drain()
            except (asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
                break
        # Client closed its side: propagate EOF so the server can exit. Without
        # this the server waited on stdin forever and the wrapper never returned,
        # leaving orphaned wrapper/server pairs after every client disconnect.
        try:
            stdin.close()
        except (BrokenPipeError, ConnectionResetError):
            pass

    async def _server_to_client(self, proc: asyncio.subprocess.Process) -> None:
        stdout = proc.stdout
        if stdout is None:
            raise RuntimeError("MCP subprocess stdout pipe is unavailable")
        while True:
            try:
                line = await stdout.readline()
                if not line:
                    break
                msg = self._scanner.parse_json_line(line) if (
                    self.scan_outputs or self.pin_schema) else None
                if msg is None:
                    sys.stdout.buffer.write(line)  # BUG-2 fix: unchanged bytes
                    sys.stdout.buffer.flush()
                    continue
                method, tool = self._pending.pop(str(msg.get("id")), ("", ""))
                out: dict = msg
                if self.scan_outputs:
                    sanitized, findings = self._scanner.scan(msg, "output")
                    if findings:
                        self._audit.write_injection("output", findings, method, tool_name=tool)
                        log.warning("wrap.stdio.injection", count=len(findings))
                    out, action = policy.enforce_output(
                        msg, sanitized, findings, method, self.block_on_match)
                    if action in ("tools_removed", "withheld"):
                        self._audit.write_policy_action(
                            action, method, tool,
                            detail={"removed_tools": policy.removed_tool_names(msg, out)}
                            if action == "tools_removed" else None,
                        )
                if self.pin_schema and method == "tools/list":
                    out = self._check_catalog(msg, out)
                self._emit(out)
            except (asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
                break

    def _check_catalog(self, original: dict, out: dict) -> dict:
        """MCP-11: pin the first catalog; withhold a changed one in block mode."""
        current = policy.catalog_hash(original)
        if current is None:
            return out
        if self._pinned_catalog is None:
            self._pinned_catalog = current
            self._audit.write_schema_pinned(current)
            return out
        if current == self._pinned_catalog:
            return out
        self._audit.write_schema_changed(self._pinned_catalog, current, enforced=self.block_on_match)
        log.warning("wrap.stdio.catalog_changed", baseline=self._pinned_catalog[:16])
        if not self.block_on_match:
            return out
        return policy.jsonrpc_error(
            original.get("id"), policy.CODE_CATALOG_CHANGED,
            "AI SAFE2: tool catalog changed since it was pinned; restart to re-approve",
            {"baseline_hash": self._pinned_catalog, "current_hash": current},
        )

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
