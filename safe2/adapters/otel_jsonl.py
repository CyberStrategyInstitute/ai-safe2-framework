"""Bounded OpenTelemetry OTLP/JSON file interoperability."""

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

MAX_FILE_BYTES = 20_000_000
MAX_LINES = 100_000
MAX_LINE_BYTES = 1_000_000
ADAPTER_ID = "opentelemetry.otlp-jsonl"
ADAPTER_VERSION = "1.0"

CONTENT_ATTRIBUTES = {
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "gen_ai.system_instructions",
    "gen_ai.prompt",
    "gen_ai.completion",
    "gen_ai.retrieval.query.text",
    "gen_ai.retrieval.documents",
    "gen_ai.tool.definitions",
}


def descriptor(otel_version: str) -> dict[str, Any]:
    if not otel_version.strip() or len(otel_version) > 100:
        raise AdapterError("OpenTelemetry version must contain 1 to 100 characters")
    return {
        "schema_version": "safe2.adapter.v1",
        "adapter_id": ADAPTER_ID,
        "version": ADAPTER_VERSION,
        "provider": {"name": "OpenTelemetry OTLP JSON File", "version": otel_version.strip()},
        "evidence_types": ["harness", "usage"],
        "decision_scope": "evidence_only",
        "transport": "file",
        "privacy": {
            "content_collection": "metadata",
            "network_required": False,
            "credential_required": False,
        },
    }


def _read_lines(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise AdapterError(f"OTLP JSONL input is not readable: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AdapterError("OTLP JSONL input must be a regular, non-symlink file")
    if info.st_size > MAX_FILE_BYTES:
        raise AdapterError(f"OTLP JSONL input exceeds {MAX_FILE_BYTES} bytes")
    source = path.read_bytes()
    raw_lines = source.splitlines()
    if not raw_lines:
        raise AdapterError("OTLP JSONL input is empty")
    if len(raw_lines) > MAX_LINES:
        raise AdapterError(f"OTLP JSONL input exceeds {MAX_LINES} lines")
    documents = []
    for number, raw in enumerate(raw_lines, start=1):
        if not raw.strip():
            raise AdapterError(f"OTLP JSONL line {number} is blank")
        if len(raw) > MAX_LINE_BYTES:
            raise AdapterError(f"OTLP JSONL line {number} exceeds {MAX_LINE_BYTES} bytes")
        try:
            value = json.loads(
                raw,
                object_pairs_hook=_pairs,
                parse_constant=lambda token, line_number=number: (_ for _ in ()).throw(
                    AdapterError(f"non-finite JSON number on line {line_number}: {token}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterError(f"OTLP JSONL line {number} is not valid UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise AdapterError(f"OTLP JSONL line {number} must be a JSON object")
        documents.append(value)
    return source, documents


def _attribute_value(value: Any) -> str | int | float | bool | None:
    if not isinstance(value, dict):
        return None
    for key in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if key not in value:
            continue
        item = value[key]
        if key == "intValue" and isinstance(item, str):
            try:
                return int(item)
            except ValueError:
                return None
        if isinstance(item, (str, int, float, bool)):
            return item
    return None


def _attributes(rows: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("key"), str):
            continue
        key = row["key"]
        if key in CONTENT_ATTRIBUTES:
            continue
        value = _attribute_value(row.get("value"))
        if value is not None:
            result[key] = value
    return result


def translate(path: Path, otel_version: str, *, observed_at: str | None = None) -> dict[str, Any]:
    """Aggregate OTLP TracesData without retaining span content or identifiers."""
    producer = descriptor(otel_version)["provider"]
    source, documents = _read_lines(path)
    span_count = 0
    error_spans = 0
    operation_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    input_tokens = 0
    output_tokens = 0
    token_spans = 0
    gaps: Counter[str] = Counter()

    for document in documents:
        top_types = [
            name
            for name in ("resourceSpans", "resourceMetrics", "resourceLogs")
            if name in document
        ]
        if top_types != ["resourceSpans"]:
            raise AdapterError("each OTLP JSONL value must contain only TracesData resourceSpans")
        resources = document.get("resourceSpans")
        if not isinstance(resources, list):
            raise AdapterError("OTLP resourceSpans must be an array")
        for resource in resources:
            if not isinstance(resource, dict):
                gaps["invalid_resource_span"] += 1
                continue
            scopes = resource.get("scopeSpans")
            if not isinstance(scopes, list):
                gaps["missing_scope_spans"] += 1
                continue
            for scope in scopes:
                if not isinstance(scope, dict) or not isinstance(scope.get("spans"), list):
                    gaps["invalid_scope_spans"] += 1
                    continue
                for span in scope["spans"]:
                    if not isinstance(span, dict):
                        gaps["invalid_span"] += 1
                        continue
                    span_count += 1
                    attributes = _attributes(span.get("attributes"))
                    operation = attributes.get("gen_ai.operation.name")
                    provider = attributes.get("gen_ai.provider.name")
                    model = attributes.get("gen_ai.response.model") or attributes.get(
                        "gen_ai.request.model"
                    )
                    if isinstance(operation, str):
                        operation_counts[operation] += 1
                    if isinstance(provider, str):
                        provider_counts[provider] += 1
                    if isinstance(model, str):
                        model_counts[model] += 1
                    status = span.get("status")
                    if isinstance(status, dict) and status.get("code") in (2, "STATUS_CODE_ERROR"):
                        error_spans += 1
                    incoming = attributes.get("gen_ai.usage.input_tokens")
                    outgoing = attributes.get("gen_ai.usage.output_tokens")
                    valid_in = (
                        isinstance(incoming, int)
                        and not isinstance(incoming, bool)
                        and incoming >= 0
                    )
                    valid_out = (
                        isinstance(outgoing, int)
                        and not isinstance(outgoing, bool)
                        and outgoing >= 0
                    )
                    if incoming is not None or outgoing is not None:
                        if valid_in and valid_out:
                            input_tokens += incoming
                            output_tokens += outgoing
                            token_spans += 1
                        else:
                            gaps["invalid_or_incomplete_token_pair"] += 1

    digest = hashlib.sha256(source).hexdigest()
    line_ref = f"lines:1-{len(documents)}"
    claims: list[dict[str, Any]] = [
        {
            "id": "span-count",
            "name": "span_count",
            "value": span_count,
            "basis": "observed",
            "source_ref": line_ref,
        },
        {
            "id": "error-span-count",
            "name": "error_span_count",
            "value": error_spans,
            "basis": "provider_reported",
            "source_ref": line_ref,
        },
        {
            "id": "token-span-count",
            "name": "token_usage_span_count",
            "value": token_spans,
            "basis": "observed",
            "source_ref": line_ref,
        },
    ]
    if token_spans:
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
    gap_list = [f"{name}={count}" for name, count in sorted(gaps.items())]
    evidence: dict[str, Any] = {
        "schema_version": "safe2.adapter-evidence.v1",
        "evidence_id": f"otel-jsonl-{digest[:16]}",
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "provider": producer,
        "evidence_type": "harness",
        "observed_at": observed_at or datetime.now(UTC).isoformat(),
        "status": "partial" if gap_list else "complete",
        "decision_scope": "evidence_only",
        "conformance_claim": False,
        "coverage": {
            "inspected": [
                "trace_spans",
                "gen_ai_operations",
                "provider_and_model",
                "token_usage",
                "span_status",
            ],
            "gaps": gap_list,
        },
        "claims": claims,
        "payload": {
            "span_count": span_count,
            "error_span_count": error_spans,
            "operation_counts": dict(sorted(operation_counts.items())),
            "provider_counts": dict(sorted(provider_counts.items())),
            "model_counts": dict(sorted(model_counts.items())),
            "usage": {
                "spans": token_spans,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "content_retained": False,
        },
        "provenance": {"source": path.name, "source_sha256": digest},
    }
    if validate_artifact("adapter-evidence-v1", evidence):
        raise AdapterError("generated OpenTelemetry evidence failed its packaged contract")
    return evidence


def export_metadata(evidence: dict[str, Any]) -> dict[str, Any]:
    """Export non-content SAFE2 evidence metadata as one OTLP LogsData value."""
    errors = validate_artifact("adapter-evidence-v1", evidence)
    if errors:
        raise AdapterError("input must satisfy safe2.adapter-evidence.v1")
    gaps = evidence["coverage"]["gaps"]
    attrs = {
        "safe2.schema_version": evidence["schema_version"],
        "safe2.evidence_id": evidence["evidence_id"],
        "safe2.adapter_id": evidence["adapter_id"],
        "safe2.adapter_version": evidence["adapter_version"],
        "safe2.evidence_type": evidence["evidence_type"],
        "safe2.status": evidence["status"],
        "safe2.decision_scope": evidence["decision_scope"],
        "safe2.coverage_gap_count": len(gaps),
        "safe2.source_sha256": evidence["provenance"]["source_sha256"] or "unavailable",
    }
    attributes = []
    for key, value in attrs.items():
        kind = "intValue" if isinstance(value, int) else "stringValue"
        attributes.append(
            {"key": key, "value": {kind: str(value) if kind == "intValue" else value}}
        )
    return {
        "resourceLogs": [
            {
                "scopeLogs": [
                    {
                        "scope": {"name": "ai-safe2", "version": ADAPTER_VERSION},
                        "logRecords": [
                            {
                                "severityText": "INFO",
                                "body": {"stringValue": "AI SAFE2 adapter evidence metadata"},
                                "attributes": attributes,
                            }
                        ],
                    }
                ]
            }
        ]
    }
