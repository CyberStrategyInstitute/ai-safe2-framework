"""Offline verification of the installed SAFE2 runtime and contract catalog."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from datetime import UTC, datetime
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from safe2 import __version__
from safe2.contracts import SCHEMAS, validate_artifact

REQUIRED_DISTRIBUTIONS = (
    "click",
    "pydantic",
    "httpx",
    "jsonschema",
    "structlog",
    "rich",
    "anyio",
    "defusedxml",
)


def _metadata_versions() -> dict[str, str]:
    versions = {}
    for name in REQUIRED_DISTRIBUTIONS:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return versions


def _entrypoints() -> set[str] | None:
    try:
        return {
            item.name
            for item in importlib.metadata.entry_points(group="console_scripts")
            if item.value == "safe2.cli:main"
        }
    except Exception:  # metadata providers are outside SAFE2's control
        return None


def inspect_installation(
    *,
    runtime: tuple[int, int, int] | None = None,
    installed: dict[str, str] | None = None,
    distribution_version: str | None | object = ...,
    console_entrypoints: set[str] | None | object = ...,
) -> dict[str, Any]:
    """Inspect local metadata and packaged schemas without network or project reads."""
    runtime = runtime or (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    installed = _metadata_versions() if installed is None else installed
    if distribution_version is ...:
        try:
            resolved_distribution: str | None = importlib.metadata.version("ai-safe2")
        except importlib.metadata.PackageNotFoundError:
            resolved_distribution = None
    else:
        resolved_distribution = distribution_version  # type: ignore[assignment]
    entries = _entrypoints() if console_entrypoints is ... else console_entrypoints

    if runtime[:2] < (3, 11):
        python_support = "unsupported"
    elif runtime[:2] <= (3, 14):
        python_support = "supported"
    else:
        python_support = "not_yet_qualified"

    invalid = []
    catalog = hashlib.sha256()
    loaded = 0
    for name, filename in sorted(SCHEMAS.items()):
        try:
            raw = files("safe2.data").joinpath(filename).read_bytes()
            document = json.loads(raw)
            Draft202012Validator.check_schema(document)
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            invalid.append(name)
            continue
        loaded += 1
        catalog.update(name.encode("utf-8"))
        catalog.update(b"\0")
        catalog.update(filename.encode("utf-8"))
        catalog.update(b"\0")
        catalog.update(raw)

    missing = sorted(set(REQUIRED_DISTRIBUTIONS) - set(installed))
    entrypoint_status = (
        "metadata_unavailable"
        if entries is None
        else "present"
        if "safe2" in entries
        else "missing"
    )
    version_match = resolved_distribution == __version__ if resolved_distribution is not None else None
    hard_fail = (
        python_support == "unsupported"
        or bool(missing)
        or bool(invalid)
        or version_match is False
    )
    unresolved = (
        python_support == "not_yet_qualified"
        or resolved_distribution is None
        or entrypoint_status != "present"
    )
    verdict = "fail" if hard_fail else "hold" if unresolved else "pass"
    result: dict[str, Any] = {
        "schema_version": "safe2.installation-check.v1",
        "checked_at": datetime.now(UTC).isoformat(),
        "cli_version": __version__,
        "python": {"version": ".".join(str(part) for part in runtime), "support": python_support},
        "distribution": {
            "name": "ai-safe2",
            "version": resolved_distribution,
            "status": "installed" if resolved_distribution is not None else "metadata_unavailable",
            "version_match": version_match,
        },
        "dependencies": {"required": dict(sorted(installed.items())), "missing": missing},
        "contracts": {
            "declared": len(SCHEMAS),
            "loaded": loaded,
            "invalid": invalid,
            "catalog_sha256": catalog.hexdigest() if loaded else None,
        },
        "console_entrypoint": entrypoint_status,
        "verdict": verdict,
        "exit_code": {"pass": 0, "fail": 1, "hold": 2}[verdict],
        "network_used": False,
        "content_inspected": False,
        "limitations": [
            "This check verifies local package metadata and schema readability, not package signatures or publisher identity.",
            "Dependency presence is not a vulnerability, license, or minimum-version audit.",
            "A passing installation check does not test a project, harness, control implementation, or framework conformance.",
        ],
    }
    if validate_artifact("installation-check-v1", result):
        raise ValueError("Installation check produced an invalid artifact")
    return result
