"""Opt-in posting of a project manifest to the hosted Tarvin assessment tool.

One JSON-RPC `tools/call` POST over Streamable HTTP, no session, no `initialize`.
The API key comes only from the environment, is held in memory for the one request,
and is never written to disk, logged, printed, or placed in an exception message.
"""

from __future__ import annotations

import json
import re
import shlex
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from safe2 import __version__

ENDPOINT = "https://mcp.agency-check.app/pro/mcp"
KEY_ENV = "SAFE2_MCP_PRO_KEY"
KEY_PREFIX = "as2k_"
TOOL_NAME = "assess_" + "project"
MAX_BODY_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 1_048_576
CONNECT_RETRY_DELAY_SECONDS = 0.5
UNSIGNED_NOTICE = (
    "Manifest is UNSIGNED: the server trusts generator.name and cannot verify this CLI produced it "
    "(manifest signing is an open decision)."
)
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class PostError(ValueError):
    """Raised before any network activity when a post cannot be made safely."""


@dataclass(frozen=True)
class PostOutcome:
    """Result of one post attempt. `error` holds server text that has been sanitized."""

    status: str
    http_status: int | None = None
    structured: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    attempts: int = 1

    @property
    def succeeded(self) -> bool:
        return self.status in {"ok", "not_applied"}


def clean_text(value: object, limit: int = 200) -> str:
    """Neutralize untrusted server text before it reaches a terminal or a log."""
    return _CONTROL.sub("?", str(value))[:limit]


def require_key(environ: dict[str, str]) -> str | None:
    """Return the key from the environment, None when unset; reject a malformed one unseen."""
    key = environ.get(KEY_ENV, "").strip()
    if not key:
        return None
    if not key.startswith(KEY_PREFIX) or any(character.isspace() for character in key):
        raise PostError(f"{KEY_ENV} is set but is not an {KEY_PREFIX}... Tarvin key")
    return key


def build_body(manifest: dict[str, Any]) -> bytes:
    """The exact JSON-RPC request: `{ "manifest": <manifest> }` as the tool arguments."""
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": TOOL_NAME, "arguments": {"manifest": manifest}},
    }
    body = json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if len(body) > MAX_BODY_BYTES:
        raise PostError(f"manifest request is {len(body)} bytes; the server accepts at most {MAX_BODY_BYTES}")
    return body


def manual_call_hint(manifest_path: Path, endpoint: str | None = None) -> list[str]:
    """What to print when no key is set: where the manifest is and the exact one-line call."""
    endpoint = endpoint or ENDPOINT
    call = (
        f"jq -n --slurpfile m {shlex.quote(str(manifest_path))} "
        f"'{{jsonrpc:\"2.0\",id:1,method:\"tools/call\",params:{{name:\"{TOOL_NAME}\","
        "arguments:{manifest:$m[0]}}}' | "
        f"curl -sS -X POST {shlex.quote(endpoint)} "
        f'-H "Authorization: Bearer ${KEY_ENV}" '
        "-H 'Content-Type: application/json' "
        "-H 'Accept: application/json, text/event-stream' --data-binary @-"
    )
    return [
        f"{KEY_ENV} is not set; nothing was sent.",
        f"Manifest: {manifest_path}",
        f"To send it, set {KEY_ENV} in your environment (it is never accepted as an argument) and run:",
        call,
    ]


def _check_endpoint(endpoint: str) -> None:
    parts = urlsplit(endpoint)
    if parts.scheme == "https":
        return
    if parts.scheme == "http" and (parts.hostname or "") in _LOOPBACK_HOSTS:
        return
    raise PostError("the endpoint must use https (plain http is allowed only for loopback)")


class _ResponseTooLarge(Exception):
    pass


def _send(
    body: bytes, key: str, endpoint: str, transport: httpx.BaseTransport | None
) -> tuple[int, str, bytes]:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": f"safe2/{__version__} assess-manifest",
    }
    timeout = httpx.Timeout(30.0, connect=10.0)
    with (
        httpx.Client(timeout=timeout, follow_redirects=False, transport=transport) as client,
        client.stream("POST", endpoint, content=body, headers=headers) as response,
    ):
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                raise _ResponseTooLarge
            chunks.append(chunk)
        return response.status_code, response.headers.get("content-type", ""), b"".join(chunks)


def _decode(content_type: str, payload: bytes) -> dict[str, Any] | None:
    text = payload.decode("utf-8", "replace")
    try:
        if "text/event-stream" in content_type:
            for line in text.splitlines():
                if line.startswith("data:"):
                    message = json.loads(line[5:].strip())
                    if isinstance(message, dict) and ("result" in message or "error" in message):
                        return message
            return None
        message = json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        return None
    return message if isinstance(message, dict) else None


def _tool_error(result: dict[str, Any]) -> dict[str, Any]:
    """Pull `{error:{code,message,...}}` out of an isError result's text, sanitized."""
    error: dict[str, Any] = {"code": "tool_error", "message": ""}
    content = result.get("content")
    first = content[0] if isinstance(content, list) and content and isinstance(content[0], dict) else {}
    try:
        parsed = json.loads(str(first.get("text", "")))
    except (json.JSONDecodeError, RecursionError):
        return error
    raw = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(raw, dict):
        return error
    error["code"] = clean_text(raw.get("code", "tool_error"), 64)
    error["message"] = clean_text(raw.get("message", ""))
    if isinstance(raw.get("upgrade_url"), str):
        error["upgrade_url"] = clean_text(raw["upgrade_url"], 300)
    if isinstance(raw.get("issues"), list):
        error["issues"] = [
            {"path": clean_text(issue.get("path", "/"), 120), "message": clean_text(issue.get("message", ""), 160)}
            for issue in raw["issues"][:20]
            if isinstance(issue, dict)
        ]
    return error


def _interpret(http_status: int, content_type: str, payload: bytes) -> PostOutcome:
    if http_status in {401, 403}:
        return PostOutcome("auth_failed", http_status)
    message = _decode(content_type, payload)
    if not 200 <= http_status < 300:
        detail = None
        if message and isinstance(message.get("error"), dict):
            detail = {"code": "http_error", "message": clean_text(message["error"].get("message", ""))}
        return PostOutcome("http_error", http_status, error=detail)
    if message is None:
        return PostOutcome("bad_response", http_status)
    if isinstance(message.get("error"), dict):
        rpc = message["error"]
        return PostOutcome(
            "tool_error",
            http_status,
            error={"code": "rpc_error", "message": clean_text(rpc.get("message", ""))},
        )
    result = message.get("result")
    if not isinstance(result, dict):
        return PostOutcome("bad_response", http_status)
    if result.get("isError") is True:
        error = _tool_error(result)
        status = error["code"] if error["code"] in {"pro_required", "invalid_manifest"} else "tool_error"
        return PostOutcome(status, http_status, error=error)
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        return PostOutcome("bad_response", http_status)
    return PostOutcome("not_applied" if structured.get("applied") is False else "ok", http_status, structured=structured)


def post_manifest(
    manifest: dict[str, Any],
    *,
    key: str,
    endpoint: str | None = None,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> PostOutcome:
    """Send one request. Retries once on a connect error only; never on any HTTP status."""
    target = endpoint or ENDPOINT
    _check_endpoint(target)
    body = build_body(manifest)
    attempts = 0
    while True:
        attempts += 1
        try:
            http_status, content_type, payload = _send(body, key, target, transport)
        except httpx.ConnectError:
            if attempts >= 2:
                return PostOutcome("network_error", attempts=attempts, error={"code": "ConnectError", "message": ""})
            sleep(CONNECT_RETRY_DELAY_SECONDS)
            continue
        except _ResponseTooLarge:
            return PostOutcome("bad_response", attempts=attempts, error={"code": "response_too_large", "message": ""})
        except httpx.HTTPError as exc:
            return PostOutcome("network_error", attempts=attempts, error={"code": type(exc).__name__, "message": ""})
        outcome = _interpret(http_status, content_type, payload)
        return PostOutcome(
            outcome.status, outcome.http_status, outcome.structured, outcome.error, attempts
        )


def describe_outcome(outcome: PostOutcome) -> list[str]:
    """Human summary lines. Server-supplied text is sanitized; the key is never available here."""
    lines: list[str] = []
    if outcome.succeeded and outcome.structured is not None:
        data = outcome.structured
        lines.append(f"Project: {clean_text(data.get('name', ''))} ({clean_text(data.get('project_id', ''))})")
        lines.append(f"ACT tier: {clean_text(data.get('act_tier', 'unknown'), 32)}")
        if outcome.status == "not_applied":
            lines.append(
                "NOT APPLIED: the server kept an existing CLI manifest for this project "
                f"({clean_text(data.get('reason', 'unspecified'))}). Nothing was changed."
            )
        else:
            lines.append("Applied: yes")
        raw_gaps = data.get("gaps")
        gaps = [gap for gap in raw_gaps if isinstance(gap, dict)] if isinstance(raw_gaps, list) else []
        lines.append(f"Missing controls: {len(gaps)}")
        for gap in gaps[:20]:
            lines.append(
                f"  - {clean_text(gap.get('control_id', ''), 40)} "
                f"{clean_text(gap.get('name', ''), 100)} [{clean_text(gap.get('severity', ''), 20)}]"
            )
        lines.append(f"Snapshot: {clean_text(data.get('snapshot_id', 'none'), 64)}")
        if data.get("signed") is False:
            lines.append("Server reports signed: false (no signature is applied to the record).")
        return lines
    error = outcome.error or {}
    if outcome.status == "pro_required":
        lines.append("Tarvin access is required for the hosted assessment; nothing was recorded.")
        if error.get("upgrade_url"):
            lines.append(f"Upgrade: {error['upgrade_url']}")
    elif outcome.status == "invalid_manifest":
        lines.append("The server rejected the manifest as invalid; nothing was recorded.")
        lines.extend(f"  - {issue['path']}: {issue['message']}" for issue in error.get("issues", []))
    elif outcome.status == "auth_failed":
        lines.append(f"The server rejected the API key (HTTP {outcome.http_status}); nothing was recorded.")
    elif outcome.status == "network_error":
        lines.append(
            f"Could not reach the server ({error.get('code', 'error')}) after {outcome.attempts} attempt(s)."
        )
    else:
        lines.append(f"The post did not succeed: {outcome.status}")
        if outcome.http_status:
            lines.append(f"  HTTP status: {outcome.http_status}")
        if error.get("code") or error.get("message"):
            lines.append(f"  Server error: {error.get('code', '')} {error.get('message', '')}".rstrip())
    return lines
