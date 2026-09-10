"""Packaged, frozen identity for the inert Challenge 001 fixture study."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from typing import Any

GRADER_VERSION = "1.0"
TREATMENTS = ("uncontrolled", "conventional", "safe2-reference")
SCENARIO_IDS = (
    "unauthorized-write",
    "legitimate-write",
    "missing-approval",
    "valid-approval",
    "replayed-approval",
    "enforcement-outage",
)


def protocol() -> dict[str, Any]:
    """Return a fresh copy so a caller cannot mutate the shared study protocol."""
    resource = files("safe2.data").joinpath("challenge_001_protocol.json")
    result = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or tuple(
        item.get("id") for item in result.get("scenarios", [])
    ) != SCENARIO_IDS:
        raise ValueError("The packaged Challenge 001 protocol is invalid.")
    return result


def scenario(scenario_id: str) -> dict[str, Any]:
    """Resolve an exact scenario identifier from the frozen local protocol."""
    for item in protocol()["scenarios"]:
        if item["id"] == scenario_id:
            return item
    raise ValueError("Unknown Challenge 001 scenario identifier.")


def experiment(seed: int = 0) -> dict[str, Any]:
    """Pin scenario and grader content; the seed selects inert candidate values."""
    if type(seed) is not int or not 0 <= seed <= 2**31 - 1:
        raise ValueError("Seed must be an integer between 0 and 2147483647.")
    spec = protocol()
    canonical = json.dumps(
        spec["scenarios"], sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    # Normalize text newlines so a Windows checkout and a Linux wheel agree.
    grader = files("safe2.challenge").joinpath("grading.py").read_bytes()
    grader = grader.replace(b"\r\n", b"\n")
    return {
        "challenge_id": spec["id"],
        "protocol_version": spec["version"],
        "scenario_set_sha256": hashlib.sha256(canonical).hexdigest(),
        "grader_version": GRADER_VERSION,
        "grader_sha256": hashlib.sha256(grader).hexdigest(),
        "environment": "inert-shared-state-v1",
        "seed": seed,
        "model_id": "none",
        "enforcement_plane": spec["enforcement_plane"],
        "framework_version": spec["framework_version"],
    }
