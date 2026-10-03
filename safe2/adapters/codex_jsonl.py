"""Privacy-preserving translation of explicit Codex JSONL exports."""

from __future__ import annotations

import hashlib
import json
import stat
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from safe2.adapters.conformance import AdapterError, _pairs
from safe2.contracts import validate_artifact

MAX_TRACE_BYTES = 20_000_000
MAX_TRACE_LINES = 100_000
MAX_LINE_BYTES = 1_000_000
ADAPTER_ID = "openai.codex-jsonl"
ADAPTER_VERSION = "1.0"


def descriptor(codex_version: str) -> dict[str, Any]:
    """Return the descriptor for one explicitly versioned Codex producer."""
    if not codex_version.strip() or len(codex_version) > 100:
        raise AdapterError("Codex version must contain 1 to 100 characters")
    return {
        "schema_version": "safe2.adapter.v1",
        "adapter_id": ADAPTER_ID,
        "version": ADAPTER_VERSION,
        "provider": {"name": "OpenAI Codex CLI", "version": codex_version.strip()},
        "evidence_types": ["harness", "usage"],
        "decision_scope": "evidence_only",
        "transport": "file",
        "privacy": {
            "content_collection": "metadata",
            "network_required": False,
            "credential_required": False,
        },
    }


def _strict_object(raw: bytes, line_number: int) -> dict[str, Any]:
    if len(raw) > MAX_LINE_BYTES:
        raise AdapterError(f"Codex JSONL line {line_number} exceeds {MAX_LINE_BYTES} bytes")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                AdapterError(f"non-finite JSON number on line {line_number}: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Codex JSONL line {line_number} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise AdapterError(f"Codex JSONL line {line_number} must be a JSON object")
    return value


def translate(path: Path, codex_version: str, *, observed_at: str | None = None) -> dict[str, Any]:
    """Translate an explicit trace into bounded aggregate evidence.

    Prompts, messages, command strings, command output, and item bodies are never
    copied to the output. Unknown shapes remain visible as coverage gaps.
    """
    producer = descriptor(codex_version)["provider"]
    try:
        info = path.lstat()
    except OSError as exc:
        raise AdapterError(f"Codex trace is not readable: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AdapterError("Codex trace must be a regular, non-symlink file")
    if info.st_size > MAX_TRACE_BYTES:
        raise AdapterError(f"Codex trace exceeds {MAX_TRACE_BYTES} bytes")
    try:
        source = path.read_bytes()
    except OSError as exc:
        raise AdapterError(f"Codex trace is not readable: {path}") from exc

    event_counts: Counter[str] = Counter()
    item_counts: Counter[str] = Counter()
    command_status_counts: Counter[str] = Counter()
    unknown_event_counts: Counter[str] = Counter()
    input_tokens = 0
    output_tokens = 0
    usage_events = 0
    lines = source.splitlines()
    if not lines:
        raise AdapterError("Codex trace is empty")
    if len(lines) > MAX_TRACE_LINES:
        raise AdapterError(f"Codex trace exceeds {MAX_TRACE_LINES} lines")

    documented_events = {"item.started", "item.completed", "turn.completed"}
    for number, raw in enumerate(lines, start=1):
        if not raw.strip():
            raise AdapterError(f"Codex JSONL line {number} is blank")
        event = _strict_object(raw, number)
        event_type = event.get("type")
        if not isinstance(event_type, str) or not event_type:
            unknown_event_counts["missing_type"] += 1
            continue
        event_counts[event_type] += 1
        if event_type not in documented_events:
            unknown_event_counts[event_type] += 1

        if event_type in {"item.started", "item.completed"}:
            item = event.get("item")
            if not isinstance(item, dict) or not isinstance(item.get("type"), str):
                unknown_event_counts[f"{event_type}:missing_item_type"] += 1
                continue
            item_type = str(item["type"])
            item_counts[item_type] += 1
            if item_type == "command_execution" and event_type == "item.completed":
                status = item.get("status")
                if isinstance(status, str) and status:
                    command_status_counts[status] += 1
                else:
                    command_status_counts["unreported"] += 1

        if event_type == "turn.completed":
            usage = event.get("usage")
            if not isinstance(usage, dict):
                unknown_event_counts["turn.completed:missing_usage"] += 1
                continue
            incoming = usage.get("input_tokens")
            outgoing = usage.get("output_tokens")
            if not isinstance(incoming, int) or isinstance(incoming, bool) or incoming < 0:
                unknown_event_counts["turn.completed:invalid_input_tokens"] += 1
                continue
            if not isinstance(outgoing, int) or isinstance(outgoing, bool) or outgoing < 0:
                unknown_event_counts["turn.completed:invalid_output_tokens"] += 1
                continue
            input_tokens += incoming
            output_tokens += outgoing
            usage_events += 1

    gaps = [f"unmodeled:{name}={count}" for name, count in sorted(unknown_event_counts.items())]
    status = "partial" if gaps else "complete"
    line_ref = f"lines:1-{len(lines)}"
    claims = [
        {
            "id": "event-count",
            "name": "event_count",
            "value": len(lines),
            "basis": "observed",
            "source_ref": line_ref,
        },
        {
            "id": "command-count",
            "name": "completed_command_execution_count",
            "value": sum(command_status_counts.values()),
            "basis": "observed",
            "source_ref": line_ref,
        },
        {
            "id": "usage-events",
            "name": "usage_event_count",
            "value": usage_events,
            "basis": "observed",
            "source_ref": line_ref,
        },
    ]
    if usage_events:
        claims.extend(
            [
                {
                    "id": "input-tokens",
                    "name": "input_tokens",
                    "value": input_tokens,
                    "basis": "provider_reported",
                    "source_ref": line_ref,
                },
                {
                    "id": "output-tokens",
                    "name": "output_tokens",
                    "value": output_tokens,
                    "basis": "provider_reported",
                    "source_ref": line_ref,
                },
            ]
        )
    digest = hashlib.sha256(source).hexdigest()
    evidence: dict[str, Any] = {
        "schema_version": "safe2.adapter-evidence.v1",
        "evidence_id": f"codex-jsonl-{digest[:16]}",
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "provider": producer,
        "evidence_type": "harness",
        "observed_at": observed_at or datetime.now(UTC).isoformat(),
        "status": status,
        "decision_scope": "evidence_only",
        "conformance_claim": False,
        "coverage": {
            "inspected": ["event_types", "item_types", "command_status", "token_usage"],
            "gaps": gaps,
        },
        "claims": claims,
        "payload": {
            "event_counts": dict(sorted(event_counts.items())),
            "item_type_counts": dict(sorted(item_counts.items())),
            "command_status_counts": dict(sorted(command_status_counts.items())),
            "usage": {
                "events": usage_events,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "content_retained": False,
        },
        "provenance": {"source": path.name, "source_sha256": digest},
    }
    errors = validate_artifact("adapter-evidence-v1", evidence)
    if errors:
        raise AdapterError("generated Codex evidence failed its packaged contract")
    return evidence
