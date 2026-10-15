#!/usr/bin/env python3
"""Turn explicit CI phase observations into a revision-bound execution receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path


SCHEMA_VERSION = "ai-safe2.ci-execution-receipt.v1"
SOURCE_VERSION = "ai-safe2.ci-execution-observation.v1"
PHASES = (
    "environment_preflight",
    "build",
    "test",
    "postprocess",
    "evidence_publication",
)
FAILURE_CLASSES = {
    "environment_preflight",
    "build",
    "test_transport",
    "test_harness",
    "application_assertion",
    "postprocess",
    "evidence_publication",
    "unknown",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def fail(phase: str, failure_class: str, reason: str, outcome: str = "failed") -> tuple[str, dict]:
    return outcome, {"class": failure_class, "phase": phase, "reason": reason}


def require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def normalize_phase(phase: dict) -> dict:
    name = phase.get("name")
    if name not in PHASES:
        raise ValueError(f"unsupported phase: {name}")
    status = phase.get("status")
    if status not in {"passed", "failed", "unavailable", "not_run"}:
        raise ValueError(f"unsupported status for {name}")
    exit_code = phase.get("exit_code")
    if exit_code is not None and type(exit_code) is not int:
        raise ValueError(f"exit_code for {name} must be an integer or null")
    failure_class = phase.get("failure_class")
    failure_reason = phase.get("failure_reason")
    if status in {"failed", "unavailable"}:
        if failure_class not in FAILURE_CLASSES:
            raise ValueError(f"{name} must include a supported failure_class")
        require_string(failure_reason, f"failure_reason for {name}")
    elif failure_class is not None or failure_reason is not None:
        raise ValueError(f"{name} may only report failure details when failed or unavailable")
    normalized = {
        "name": name,
        "status": status,
        "exit_code": exit_code,
        "failure_class": failure_class,
        "failure_reason": failure_reason,
    }
    for field in ("started_at", "completed_at"):
        if field in phase:
            value = phase[field]
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field} for {name} must be a string or null")
            normalized[field] = value
    return normalized


def validate_test_results(value: object) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("test_results must be an object or null")
    if value.get("status") not in {"passed", "failed", "partial", "not_run"}:
        raise ValueError("test_results contains an unsupported status")
    names = ("minimum_required", "discovered", "executed", "passed", "failed", "skipped")
    counts = {name: value.get(name) for name in names}
    if any(type(item) is not int or item < 0 for item in counts.values()):
        raise ValueError("test counts must be non-negative integers")
    if counts["minimum_required"] < 1:
        raise ValueError("minimum_required must be at least one")
    if counts["executed"] != counts["passed"] + counts["failed"] + counts["skipped"]:
        raise ValueError("executed must equal passed, failed, and skipped counts")
    if counts["discovered"] < counts["executed"]:
        raise ValueError("discovered must be greater than or equal to executed")
    return {"status": value["status"], **counts}


def normalize_runner(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("runner must be an object")
    operating_system = value.get("operating_system")
    architecture = value.get("architecture")
    for name, item in (("operating_system", operating_system), ("architecture", architecture)):
        if item is not None and not isinstance(item, str):
            raise ValueError(f"runner.{name} must be a string or null")
    environment_facts = value.get("environment_facts", {})
    if not isinstance(environment_facts, dict):
        raise ValueError("runner.environment_facts must be an object")
    if any(not isinstance(item, (str, int, float, bool)) and item is not None for item in environment_facts.values()):
        raise ValueError("runner.environment_facts values must be scalar or null")
    return {
        "provider": require_string(value.get("provider"), "runner.provider"),
        "image": require_string(value.get("image"), "runner.image"),
        "operating_system": operating_system,
        "architecture": architecture,
        "environment_facts": deepcopy(environment_facts),
    }


def normalize_artifacts(value: object) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError("artifacts must be an array of objects")
    return deepcopy(value)


def normalize_limitations(value: object) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("limitations must be an array of strings")
    return list(value)


def evaluate(source: dict) -> dict:
    if source.get("schema_version") != SOURCE_VERSION:
        raise ValueError(f"schema_version must be {SOURCE_VERSION}")

    required_phases = source.get("required_phases")
    if not isinstance(required_phases, list) or not required_phases:
        raise ValueError("required_phases must be a non-empty list")
    if len(required_phases) != len(set(required_phases)):
        raise ValueError("required_phases must be unique")
    if any(name not in PHASES for name in required_phases):
        raise ValueError("required_phases contains an unsupported phase")

    receipt_id = require_string(source.get("receipt_id"), "receipt_id")
    subject = source.get("subject")
    if not isinstance(subject, dict):
        raise ValueError("subject must be an object")
    normalized_subject = {
        "identifier": require_string(subject.get("identifier"), "subject.identifier"),
        "revision": require_string(subject.get("revision"), "subject.revision"),
        "capability": require_string(subject.get("capability"), "subject.capability"),
    }
    normalized_runner = normalize_runner(source.get("runner"))
    phases = source.get("phases")
    if not isinstance(phases, list):
        raise ValueError("phases must be a list")
    by_name: dict[str, dict] = {}
    normalized_phases = []
    for raw_phase in phases:
        if not isinstance(raw_phase, dict):
            raise ValueError("each phase must be an object")
        phase = normalize_phase(raw_phase)
        name = phase["name"]
        if name in by_name:
            raise ValueError(f"duplicate phase: {name}")
        by_name[name] = phase
        normalized_phases.append(phase)

    outcome = "produced"
    failure = {"class": None, "phase": None, "reason": None}
    for name in required_phases:
        phase = by_name.get(name)
        if phase is None:
            outcome, failure = fail(name, "test_harness", f"Required phase was not reported: {name}")
            break
        status = phase["status"]
        if status == "unavailable":
            outcome, failure = fail(
                name,
                phase["failure_class"],
                phase["failure_reason"],
                outcome="unavailable",
            )
            break
        if status == "failed":
            outcome, failure = fail(name, phase["failure_class"], phase["failure_reason"])
            break
        if status == "not_run":
            outcome, failure = fail(name, "test_harness", f"Required phase did not run: {name}")
            break

    test_results = validate_test_results(source.get("test_results"))
    if outcome == "produced" and "test" in required_phases:
        if not isinstance(test_results, dict):
            outcome, failure = fail("test", "test_harness", "Required test results were not reported")
        else:
            if test_results["executed"] < test_results["minimum_required"]:
                outcome, failure = fail("test", "test_harness", "Fewer tests executed than the configured minimum")
            elif test_results.get("status") != "passed" or test_results["failed"] != 0:
                outcome, failure = fail("test", "test_harness", "Test summary contradicts a passed test phase")

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "subject": normalized_subject,
        "runner": normalized_runner,
        "required_phases": list(required_phases),
        "phases": normalized_phases,
        "test_results": deepcopy(test_results),
        "outcome": outcome,
        "failure": failure,
        "artifacts": normalize_artifacts(source.get("artifacts", [])),
        "limitations": normalize_limitations(source.get("limitations", [])),
    }
    receipt["integrity"] = {"content_digest": canonical_digest(receipt)}
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-produced", action="store_true")
    args = parser.parse_args()
    try:
        receipt = evaluate(load(args.input))
    except (KeyError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"{receipt['outcome']}: {args.output}")
    if args.require_produced and receipt["outcome"] != "produced":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
