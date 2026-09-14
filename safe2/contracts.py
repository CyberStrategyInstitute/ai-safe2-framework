"""Packaged JSON Schema discovery and redacted structural validation."""

from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMAS = {
    "system-identity-source-v1": "system-identity-source-v1.schema.json",
    "system-identity-manifest-v1": "system-identity-manifest-v1.schema.json",
    "harness-source-v1": "harness-source-v1.schema.json",
    "harness-evidence-v1": "harness-evidence-v1.schema.json",
    "pytest-capture-v1": "pytest-capture-v1.schema.json",
    "usage-summary-v1": "usage-summary-v1.schema.json",
    "report-attestation-v1": "report-attestation-v1.schema.json",
    "tool-result-v1": "tool-result-v1.schema.json",
    "test-result-v1": "test-result-v1.schema.json",
    "task-receipt-input-v1": "task-receipt-input-v1.schema.json",
    "task-receipt-v1": "task-receipt-v1.schema.json",
    "challenge-bundle": "challenge-bundle-v1.schema.json",
    "challenge-run": "challenge-run-v1.schema.json",
    "challenge-source": "challenge-source-v1.schema.json",
    "challenge-comparison": "challenge-comparison-v1.schema.json",
    "aism-assessment-v1": "aism-assessment-v1.schema.json",
    "discovery-v1": "discovery-v1.schema.json",
    "discovery-drift-v1": "discovery-drift-v1.schema.json",
    "environment-posture-v1": "environment-posture-v1.schema.json",
    "environment-policy-v1": "environment-policy-v1.schema.json",
    "environment-policy-decision-v1": "environment-policy-decision-v1.schema.json",
    "friction-event-v1": "friction-event-v1.schema.json",
    "friction-summary-v1": "friction-summary-v1.schema.json",
    "run-manifest-v1": "run-manifest-v1.schema.json",
    "nexus-evidence-v1": "nexus-evidence-v1.schema.json",
    "skillspector-evidence-v1": "skillspector-evidence-v1.schema.json",
}


def schema_text(name: str) -> str:
    resource = files("safe2.data").joinpath(SCHEMAS[name])
    return resource.read_text(encoding="utf-8")


def _schemas() -> dict[str, dict[str, object]]:
    return {name: json.loads(schema_text(name)) for name in SCHEMAS}


def _registry(schemas: dict[str, dict[str, object]]) -> Registry:
    registry = Registry()
    for document in schemas.values():
        schema_id = str(document["$id"])
        registry = registry.with_resource(schema_id, Resource.from_contents(document))
    return registry


def _safe_instance_path(parts: list[object]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += "." + str(part)[:80]
    return rendered


def validate_artifact(name: str, artifact: object) -> list[dict[str, str]]:
    """Return redacted structural violations for one packaged contract."""
    schemas = _schemas()
    validator = Draft202012Validator(schemas[name], registry=_registry(schemas))
    violations = sorted(
        validator.iter_errors(artifact),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    return [
        {
            "instance_path": _safe_instance_path(list(error.absolute_path)),
            "validator": str(error.validator),
            "schema_path": "/".join(str(part) for part in error.absolute_schema_path),
        }
        for error in violations
    ]
