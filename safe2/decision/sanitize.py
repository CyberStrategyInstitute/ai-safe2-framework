"""Minimize structured state before it crosses a provider boundary."""

from __future__ import annotations

import re
from typing import Any

SECRET_KEYS = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|private[_-]?key)", re.IGNORECASE
)
SENSITIVE_KEYS = re.compile(
    r"(?:customer|production[_-]?log|exploit|hostname|source[_-]?code|architecture)", re.IGNORECASE
)
SECRET_VALUE = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)"
)


def redact_local(value: Any) -> tuple[Any, list[str]]:
    """Redact obvious secrets while preserving the local structured decision state."""
    findings: list[str] = []

    def visit(item: Any, path: str) -> Any:
        if isinstance(item, dict):
            out = {}
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if SECRET_KEYS.search(str(key)):
                    out[key] = "[REDACTED]"
                    findings.append(child_path)
                else:
                    out[key] = visit(child, child_path)
            return out
        if isinstance(item, list):
            return [visit(child, f"{path}[{index}]") for index, child in enumerate(item)]
        if isinstance(item, str) and SECRET_VALUE.search(item):
            findings.append(path)
            return "[REDACTED]"
        return item

    return visit(value, "$"), sorted(set(findings))


def external_capsule(state: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Return only the explicitly supplied sanitized capsule for an external provider."""
    capsule = state.get("decision_capsule")
    if not isinstance(capsule, dict):
        return None, ["structured_state.decision_capsule is required for external adjudication"]
    prohibited: list[str] = []

    def inspect(item: Any, path: str) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if SECRET_KEYS.search(str(key)) or SENSITIVE_KEYS.search(str(key)):
                    prohibited.append(child_path)
                inspect(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                inspect(child, f"{path}[{index}]")

    inspect(capsule, "decision_capsule")
    redacted, secrets = redact_local(capsule)
    gaps = [f"prohibited external capsule field: {key}" for key in sorted(set(prohibited))]
    gaps.extend(f"secret-like value at {path}" for path in secrets)
    if gaps:
        return None, gaps
    return redacted, []
