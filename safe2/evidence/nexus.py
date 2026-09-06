"""Collect reproducible static evidence from a NEXUS implementation checkout."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx

CHECKS = {
    "nexus-guardian-policy": ("opa/nexus-authz.rego", ["CP.4", "P3"]),
    "nexus-aism-invariants": ("opa/nexus-aism-invariants.rego", ["P1", "P2", "P3", "P4", "P5"]),
    "nexus-aim-schema": ("schemas/aim-v0.2.schema.json", ["CP.4", "P2"]),
    "nexus-agbom-schema": ("schemas/agbom-v0.3.schema.json", ["P2"]),
    "nexus-guardian-schema": ("schemas/guardian-v0.3.schema.json", ["CP.4", "P3"]),
    "nexus-nor-schema": ("schemas/nor-v0.3.schema.json", ["P2", "CP.6"]),
    "nexus-mcp-adapter": ("adapters/mcp/adapter.py", ["CP.5"]),
    "nexus-score": ("compliance/scoring/nexus-score.py", ["P2", "P4"]),
}


def _safe_field(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(value))[:100]


def _bounded_digest(path: Path, max_bytes: int) -> tuple[str | None, str | None]:
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(min(65_536, max_bytes + 1 - total)):
                total += len(chunk)
                if total > max_bytes:
                    return None, "size_limit"
                digest.update(chunk)
    except OSError as exc:
        return None, type(exc).__name__
    return digest.hexdigest(), None


def collect(root: Path, *, max_file_bytes: int = 20_000_000) -> dict:
    root = root.resolve()
    observations = []
    for check_id, (relative, controls) in CHECKS.items():
        path = root / relative
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
            contained = True
        except ValueError:
            contained = False
        candidate_present = path.exists() or path.is_symlink()
        rejected = candidate_present and (path.is_symlink() or not contained)
        readable = contained and path.is_file() and not path.is_symlink()
        digest, error = _bounded_digest(path, max_file_bytes) if readable else (None, None)
        if rejected:
            error = "symlink_or_outside_root"
        observed = readable and digest is not None
        observations.append(
            {
                "id": check_id,
                "status": "observed" if observed else "failed" if readable or rejected else "missing",
                "path": relative,
                "control_refs": controls,
                "sha256": digest,
                "error_type": error,
                "evidence_grade": "E3" if observed else "E0",
                "limitation": "Presence and digest do not prove runtime enforcement."
                if observed
                else None,
            }
        )
    return {
        "schema_version": "safe2.nexus-evidence.v1",
        "provider": {"name": "AI SAFE2 NEXUS static collector", "mode": "static"},
        "collected_at": datetime.now(UTC).isoformat(),
        "target": str(root.resolve()),
        "observations": observations,
        "summary": {
            "observed": sum(item["status"] == "observed" for item in observations),
            "missing": sum(item["status"] == "missing" for item in observations),
            "failed": sum(item["status"] == "failed" for item in observations),
        },
        "conformance_claim": False,
        "limitations": [
            "Static collection cannot demonstrate fail-closed behavior, identity binding, or receipt validity.",
            "The NEXUS MCP adapter remains reference scaffolding unless runtime evidence proves otherwise.",
        ],
    }


def collect_runtime(base_url: str, timeout: float = 5.0, max_response_bytes: int = 1_000_000) -> dict:
    """Collect read-only runtime evidence from the published NEXUS gateway API."""
    endpoints = {
        "nexus-health": ("/health", ["P3", "P4"]),
        "nexus-agbom": ("/v1/agbom", ["P2"]),
        "nexus-audit": ("/v1/audit", ["P2", "P4", "CP.6"]),
    }
    url = httpx.URL(base_url)
    if url.scheme not in {"http", "https"} or not url.host:
        raise ValueError("NEXUS runtime target must be an HTTP(S) URL with a host")
    if url.username or url.password or url.query:
        raise ValueError("NEXUS runtime target must not contain credentials or query parameters")
    port = f":{url.port}" if url.port else ""
    safe_target = f"{url.scheme}://{url.host}{port}{url.path}".rstrip("/")
    observations = []
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        for check_id, (endpoint, controls) in endpoints.items():
            try:
                with client.stream("GET", endpoint) as response:
                    raw = bytearray()
                    exceeded = False
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > max_response_bytes:
                            exceeded = True
                            break
                    body = None
                    if not exceeded and response.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        try:
                            body = json.loads(raw)
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            body = None
                    status = "observed" if response.is_success and not exceeded else "failed"
                observations.append(
                    {
                        "id": check_id,
                        "endpoint": endpoint,
                        "status": status,
                        "http_status": response.status_code,
                        "control_refs": controls,
                        "evidence_grade": "E0" if exceeded else (
                            "E3" if response.is_success and isinstance(body, dict) else "E2"
                            if response.is_success
                            else "E0"
                        ),
                        "validation": "size-limit-exceeded" if exceeded else "json-object-shape"
                        if response.is_success and isinstance(body, dict)
                        else "availability-only",
                        "observed_fields": sorted(
                            _safe_field(field)
                            for field in list(body)[:100]
                            if isinstance(field, (str, int, float, bool))
                        ) if isinstance(body, dict) else [],
                        "response_size_limit_exceeded": exceeded,
                    }
                )
            except httpx.HTTPError as exc:
                observations.append(
                    {
                        "id": check_id,
                        "endpoint": endpoint,
                        "status": "error",
                        "control_refs": controls,
                        "evidence_grade": "E0",
                        "error_type": type(exc).__name__,
                    }
                )
    return {
        "schema_version": "safe2.nexus-evidence.v1",
        "provider": {"name": "AI SAFE2 NEXUS runtime collector", "mode": "read-only-runtime"},
        "collected_at": datetime.now(UTC).isoformat(),
        "target": safe_target,
        "observations": observations,
        "summary": {
            "observed": sum(item["status"] == "observed" for item in observations),
            "failed": sum(item["status"] != "observed" for item in observations),
        },
        "conformance_claim": False,
        "limitations": [
            "Read-only endpoint availability does not prove fail-closed enforcement.",
            "Active authorization, interruption, recovery, and receipt-integrity tests require an explicitly approved test plan.",
        ],
    }
