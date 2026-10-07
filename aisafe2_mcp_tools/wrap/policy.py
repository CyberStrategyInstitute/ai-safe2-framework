"""
AI SAFE2 MCP Security Toolkit — shared enforcement policy for wrap-stdio and wrap-proxy.

Before this module, "block" mode redacted the matched phrase and forwarded the
rest of a hostile message: a poisoned tool description lost the words "Ignore
previous instructions" but still told the model to read ~/.ssh/id_rsa and hide
it. A rug-pulled catalog was logged as changed and then delivered anyway.

Policy (block mode, critical/high findings only):
  - request (client -> server): not forwarded; the client receives a JSON-RPC
    error for that id instead of hanging on a silently dropped request;
  - tools/list response: offending tools are removed from the catalog, clean
    tools are delivered (MCP-2 return-path sanitization, MCP-11 provenance);
  - any other response: replaced by a JSON-RPC error for the same id;
  - pinned catalog changed: the changed catalog is withheld (fail closed) until
    an operator re-approves it by restarting with a new baseline.
Medium findings are redacted and forwarded, as before. Log-only mode forwards
redacted content and records everything.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

BLOCKING_SEVERITIES = frozenset({"critical", "high"})
_TOOL_INDEX = re.compile(r"\.tools\[(\d+)\]")

# JSON-RPC server-defined error codes used by the wrapper.
CODE_INPUT_BLOCKED = -32010
CODE_OUTPUT_WITHHELD = -32011
CODE_CATALOG_CHANGED = -32012


def blocking(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in findings if str(f.get("severity", "")).lower() in BLOCKING_SEVERITIES]


def jsonrpc_error(msg_id: Any, code: int, message: str, data: dict | None = None) -> dict:
    err: dict[str, Any] = {"code": code, "message": message}
    if data:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": err}


def catalog_hash(msg: dict[str, Any]) -> str | None:
    """Hash of the tool catalog only — never the JSON-RPC envelope.

    The previous pin hashed the whole response including its `id`, so every
    tools/list call registered as a schema change and the alert became noise.
    """
    result = msg.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
        return None
    tools = sorted(result["tools"], key=lambda t: json.dumps(t, sort_keys=True))
    return hashlib.sha256(json.dumps(tools, sort_keys=True).encode()).hexdigest()


def enforce_output(
    msg: dict[str, Any],
    sanitized: dict[str, Any],
    findings: list[dict[str, Any]],
    method: str,
    block: bool,
) -> tuple[dict[str, Any], str]:
    """Return (message_to_deliver, action). action is one of
    'forwarded', 'redacted', 'tools_removed', 'withheld'."""
    hard = blocking(findings)
    if not findings:
        return msg, "forwarded"
    if not block or not hard:
        return sanitized, "redacted"

    result = msg.get("result")
    if method == "tools/list" and isinstance(result, dict) and isinstance(result.get("tools"), list):
        bad = {int(m.group(1)) for f in hard for m in [_TOOL_INDEX.search(f.get("field_path", ""))] if m}
        if bad:
            out = copy.deepcopy(msg)
            out["result"]["tools"] = [t for i, t in enumerate(result["tools"]) if i not in bad]
            return out, "tools_removed"

    return jsonrpc_error(
        msg.get("id"), CODE_OUTPUT_WITHHELD,
        "AI SAFE2: response withheld - hostile content detected in tool output",
        {"families": sorted({str(f.get("family", "")) for f in hard})},
    ), "withheld"


def removed_tool_names(original: dict[str, Any], delivered: dict[str, Any]) -> list[str]:
    try:
        before = [t.get("name", "") for t in original["result"]["tools"]]
        after = {t.get("name", "") for t in delivered["result"]["tools"]}
    except (KeyError, TypeError, AttributeError):
        return []
    return [n for n in before if n not in after]
