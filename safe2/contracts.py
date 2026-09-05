"""Packaged JSON Schema discovery and redacted structural validation."""

from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMAS = {
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
