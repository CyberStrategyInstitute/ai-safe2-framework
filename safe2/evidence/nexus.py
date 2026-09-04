"""Collect reproducible static evidence from a NEXUS implementation checkout."""

from __future__ import annotations

import hashlib
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


def collect(root: Path) -> dict:
    observations = []
    for check_id, (relative, controls) in CHECKS.items():
        path = root / relative
        exists = path.is_file()
        observations.append(
            {
                "id": check_id,
                "status": "observed" if exists else "missing",
                "path": relative,
                "control_refs": controls,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if exists else None,
                "evidence_grade": "E3" if exists else "E0",
                "limitation": "Presence and digest do not prove runtime enforcement."
                if exists
                else None,
            }
        )
    return {
        "schema_version": "1.0",
        "provider": {"name": "AI SAFE2 NEXUS static collector", "mode": "static"},
        "collected_at": datetime.now(UTC).isoformat(),
        "target": str(root.resolve()),
        "observations": observations,
        "summary": {
            "observed": sum(item["status"] == "observed" for item in observations),
            "missing": sum(item["status"] == "missing" for item in observations),
        },
        "conformance_claim": False,
        "limitations": [
            "Static collection cannot demonstrate fail-closed behavior, identity binding, or receipt validity.",
            "The NEXUS MCP adapter remains reference scaffolding unless runtime evidence proves otherwise.",
        ],
    }


def collect_runtime(base_url: str, timeout: float = 5.0) -> dict:
    """Collect read-only runtime evidence from the published NEXUS gateway API."""
    endpoints = {
        "nexus-health": ("/health", ["P3", "P4"]),
        "nexus-agbom": ("/v1/agbom", ["P2"]),
        "nexus-audit": ("/v1/audit", ["P2", "P4", "CP.6"]),
    }
    observations = []
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        for check_id, (endpoint, controls) in endpoints.items():
            try:
                response = client.get(endpoint)
                status = "observed" if response.is_success else "failed"
                body = (
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else None
                )
                observations.append(
                    {
                        "id": check_id,
                        "endpoint": endpoint,
                        "status": status,
                        "http_status": response.status_code,
                        "control_refs": controls,
                        "evidence_grade": (
                            "E3" if response.is_success and isinstance(body, dict) else "E2"
                            if response.is_success
                            else "E0"
                        ),
                        "validation": "json-object-shape"
                        if response.is_success and isinstance(body, dict)
                        else "availability-only",
                        "observed_fields": sorted(body) if isinstance(body, dict) else [],
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
                        "error": str(exc),
                    }
                )
    return {
        "schema_version": "1.0",
        "provider": {"name": "AI SAFE2 NEXUS runtime collector", "mode": "read-only-runtime"},
        "collected_at": datetime.now(UTC).isoformat(),
        "target": base_url,
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
