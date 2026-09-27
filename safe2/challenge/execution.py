"""Explicit, bounded Challenge 001 process execution and evidence receipts."""

from __future__ import annotations

import copy
import hashlib
import os
import stat
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from safe2.bounded_process import run_bounded
from safe2.challenge.adapters import import_source
from safe2.challenge.integrity import canonical_bytes, digest, seal, verify_digest
from safe2.challenge.io import parse_json, read_bytes
from safe2.challenge.protocol import experiment, protocol
from safe2.contracts import validate_artifact


def _file_digest(path: str | Path) -> tuple[Path, str]:
    target = Path(path)
    target.lstat()
    resolved = target.resolve(strict=True)
    if not stat.S_ISREG(resolved.lstat().st_mode):
        raise ValueError("Command file must resolve to a regular file.")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(resolved, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Command file must remain a regular file.")
        hasher = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            hasher.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    def identity(value: os.stat_result) -> tuple[int, int, int, int]:
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns
    if identity(before) != identity(after):
        raise ValueError("Command file changed while it was being inspected.")
    return resolved, hasher.hexdigest()


def _command_bindings(command: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
    normalized = list(command)
    bindings: list[dict[str, Any]] = []
    for index, value in enumerate(command):
        candidate = Path(value)
        if index == 0 or candidate.exists():
            resolved, fingerprint = _file_digest(candidate)
            normalized[index] = str(resolved)
            bindings.append({"argument_index": index, "path": str(resolved), "sha256": fingerprint})
    return normalized, bindings


def create_plan(
    command: list[str] | tuple[str, ...], *, provider_name: str, provider_version: str,
    producer_id: str, treatment: str, seed: int = 0, repetitions: int = 1,
    timeout_seconds: float = 30.0, max_output_bytes: int = 262_144,
    system_identity: str | Path | None = None,
) -> dict[str, Any]:
    """Pre-register the exact executable, study identity, limits, and producer declaration."""
    if not isinstance(command, (list, tuple)) or not command:
        raise ValueError("Command must contain an explicit executable path.")
    if any(not isinstance(item, str) or not item for item in command):
        raise ValueError("Command arguments must be non-empty strings.")
    normalized_command, file_bindings = _command_bindings(list(command))
    executable_hash = file_bindings[0]["sha256"]
    identity_hash = hashlib.sha256(read_bytes(system_identity)).hexdigest() if system_identity else None
    plan = {
        "schema_version": "safe2.challenge-execution-plan.v1",
        "challenge_id": "001", "seed": seed, "repetitions": repetitions,
        "treatment": treatment,
        "provider": {"name": provider_name, "version": provider_version, "producer_id": producer_id},
        "command": normalized_command,
        "executable_sha256": executable_hash,
        "command_file_bindings": file_bindings,
        "system_identity_sha256": identity_hash,
        "limits": {"timeout_seconds": timeout_seconds, "max_output_bytes": max_output_bytes},
        "acknowledgements": {
            "explicit_process_execution": True, "not_a_sandbox": True,
            "independence_not_established": True,
        },
    }
    if validate_artifact("challenge-execution-plan-v1", plan):
        raise ValueError("Execution plan violates its packaged contract.")
    # Reuse runner bounds before an executable is ever started.
    if type(seed) is not int or not 0 <= seed <= 2**31 - 1:
        raise ValueError("Seed is outside the supported range.")
    if type(repetitions) is not int or not 1 <= repetitions <= 100:
        raise ValueError("Repetitions must be between 1 and 100.")
    return plan


def _request(spec: dict[str, Any], plan: dict[str, Any], trial: int) -> dict[str, Any]:
    value = f"candidate:{plan['seed']}:{trial}"
    return {
        "schema_version": "safe2.challenge-executor-request.v1",
        "challenge_id": "001", "protocol_version": protocol()["version"],
        "scenario_id": spec["id"], "trial": trial, "treatment": plan["treatment"],
        "action": {
            "principal": spec["principal"], "operation": "write",
            "target": spec["target"], "value": value,
        },
        "conditions": {
            "requires_approval": spec["requires_approval"], "approval": spec["approval"],
            "control_available": spec["control_available"], "authorized": spec["authorized"],
        },
        "initial_state": copy.deepcopy(spec["initial_state"]),
    }


def _missing_episode(request: dict[str, Any], status: str, elapsed_ms: float) -> dict[str, Any]:
    return {
        "id": f"001:{request['treatment']}:{request['scenario_id']}:{request['trial']}",
        "scenario_id": request["scenario_id"], "trial": request["trial"],
        "treatment": request["treatment"], "action": request["action"],
        "decision": {"raw": status.upper(), "mode": "unknown", "constraints": [],
                     "constraints_applied": None},
        "observation": {"status": "missing", "before": None, "after": None},
        "metrics": {"elapsed_ms": elapsed_ms, "cost_usd": None, "human_interventions": None},
    }


def _episode(request: dict[str, Any], response: dict[str, Any], elapsed_ms: float) -> dict[str, Any]:
    allowed = {"schema_version", "decision", "observation", "metrics"}
    if set(response) != allowed or response.get("schema_version") != "safe2.challenge-executor-response.v1":
        raise ValueError("Executor response has unknown, missing, or unsupported top-level fields.")
    episode = _missing_episode(request, "invalid_response", elapsed_ms)
    episode["decision"] = response["decision"]
    episode["observation"] = response["observation"]
    metrics = response["metrics"]
    episode["metrics"] = {
        "elapsed_ms": elapsed_ms,
        "cost_usd": metrics.get("cost_usd"),
        "human_interventions": metrics.get("human_interventions"),
    }
    # The source schema is the authoritative strict shape check.
    specimen = {
        "schema_version": "safe2.challenge-source.v1", "adapter_contract": "generic-v1",
        "provider": {"name": "validation", "version": "1"}, "producer_id": "validation",
        "run_id": "validation", "synthetic": False, "experiment": _live_experiment(0),
        "episodes": [episode],
    }
    if validate_artifact("challenge-source", specimen):
        raise ValueError("Executor response does not satisfy the Challenge source contract.")
    return episode


def _live_experiment(seed: int) -> dict[str, Any]:
    value = experiment(seed)
    value["environment"] = "controlled-process-boundary-v1"
    value["model_id"] = "provider-declared-in-execution-plan"
    return value


def execute_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run a validated plan and return source, normalized run, and receipt.

    Failures become explicit incomplete episodes. They do not disappear, become
    successes, or prevent the remaining pre-registered scenarios from running.
    """
    if validate_artifact("challenge-execution-plan-v1", plan):
        raise ValueError("Execution plan violates its packaged contract.")
    executable, before_hash = _file_digest(plan["command"][0])
    if before_hash != plan["executable_sha256"] or str(executable) != plan["command"][0]:
        raise ValueError("Executor identity differs from the pre-registered plan.")
    for binding in plan["command_file_bindings"]:
        index = binding["argument_index"]
        path, fingerprint = _file_digest(plan["command"][index])
        if str(path) != binding["path"] or fingerprint != binding["sha256"]:
            raise ValueError("A command file differs from the pre-registered plan.")
    safe_env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
        "LANG", "LC_ALL", "PYTHONIOENCODING",
    }}
    safe_env["PYTHONIOENCODING"] = "utf-8"
    episodes: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for trial in range(plan["repetitions"]):
        for spec in protocol()["scenarios"]:
            request = _request(spec, plan, trial)
            payload = canonical_bytes(request)
            started = time.monotonic()
            result = None
            status = "process_error"
            response_hash = None
            try:
                result = run_bounded(
                    plan["command"], timeout=plan["limits"]["timeout_seconds"],
                    max_bytes=plan["limits"]["max_output_bytes"], stdin=payload,
                    env=safe_env,
                )
                elapsed = (time.monotonic() - started) * 1000
                if result.exceeded:
                    status = "output_limit"
                    episode = _missing_episode(request, status, elapsed)
                elif not result.output_complete:
                    status = "stream_incomplete"
                    episode = _missing_episode(request, status, elapsed)
                elif result.returncode != 0:
                    status = "process_error"
                    episode = _missing_episode(request, status, elapsed)
                else:
                    response_hash = hashlib.sha256(result.stdout).hexdigest()
                    try:
                        episode = _episode(request, parse_json(result.stdout), elapsed)
                        status = "complete"
                    except (ValueError, TypeError, KeyError):
                        status = "invalid_response"
                        episode = _missing_episode(request, status, elapsed)
            except subprocess.TimeoutExpired:
                elapsed = (time.monotonic() - started) * 1000
                status = "timeout"
                episode = _missing_episode(request, status, elapsed)
            episodes.append(episode)
            receipts.append({
                "episode_id": episode["id"], "request_sha256": hashlib.sha256(payload).hexdigest(),
                "response_sha256": response_hash,
                "return_code": result.returncode if result is not None else None, "status": status,
            })
    command_file_checks = []
    for binding in plan["command_file_bindings"]:
        _, after = _file_digest(binding["path"])
        command_file_checks.append({
            "argument_index": binding["argument_index"], "path": binding["path"],
            "sha256_before": binding["sha256"], "sha256_after": after,
            "unchanged": binding["sha256"] == after,
        })
    after_hash = command_file_checks[0]["sha256_after"]
    source = {
        "schema_version": "safe2.challenge-source.v1", "adapter_contract": "generic-v1",
        "provider": {"name": plan["provider"]["name"], "version": plan["provider"]["version"]},
        "producer_id": plan["provider"]["producer_id"],
        "run_id": f"controlled-execution-{uuid.uuid4()}", "synthetic": False,
        "experiment": _live_experiment(plan["seed"]), "episodes": episodes,
    }
    if validate_artifact("challenge-source", source):
        raise ValueError("Controlled execution produced an invalid source artifact.")
    source_hash = digest(source)
    run = import_source(source, adapter="generic")
    receipt = seal({
        "schema_version": "safe2.challenge-execution-receipt.v1",
        "plan_sha256": digest(plan), "source_sha256": source_hash,
        "run_integrity_sha256": run["integrity_sha256"],
        "executor_sha256_before": before_hash, "executor_sha256_after": after_hash,
        "executor_unchanged": before_hash == after_hash,
        "command_file_checks": command_file_checks,
        "system_identity_sha256": plan["system_identity_sha256"],
        "episode_receipts": receipts,
        "claims": {
            "parent_process_bounded": True, "process_sandboxed": False,
            "descendant_containment": False, "independent_replication": "not_established",
        },
    })
    if validate_artifact("challenge-execution-receipt-v1", receipt):
        raise ValueError("Execution receipt violates its packaged contract.")
    return source, run, receipt


def verify_execution(
    plan: dict[str, Any], source: dict[str, Any], run: dict[str, Any], receipt: dict[str, Any],
    *, system_identity: str | Path | None = None,
) -> dict[str, Any]:
    """Verify artifact contracts and cross-bindings without re-running the executor."""
    from safe2.challenge.model import verify_run

    errors: list[str] = []
    for name, artifact in (
        ("challenge-execution-plan-v1", plan), ("challenge-source", source),
        ("challenge-run", run), ("challenge-execution-receipt-v1", receipt),
    ):
        if validate_artifact(name, artifact):
            errors.append(f"invalid_{name}")
    if errors:
        return {"valid": False, "errors": errors, "executor_reexecuted": False}
    if receipt["plan_sha256"] != digest(plan):
        errors.append("plan_binding_mismatch")
    if receipt["source_sha256"] != digest(source):
        errors.append("source_binding_mismatch")
    if receipt["run_integrity_sha256"] != run.get("integrity_sha256"):
        errors.append("run_binding_mismatch")
    if not verify_digest(receipt):
        errors.append("receipt_integrity_mismatch")
    expected_checks = []
    for binding in plan["command_file_bindings"]:
        matching = [item for item in receipt["command_file_checks"]
                    if item["argument_index"] == binding["argument_index"]]
        if len(matching) != 1:
            errors.append("command_file_binding_mismatch")
            continue
        check = matching[0]
        expected_checks.append(check)
        if (check["path"] != binding["path"] or check["sha256_before"] != binding["sha256"]
                or check["unchanged"] != (check["sha256_before"] == check["sha256_after"])):
            errors.append("command_file_binding_mismatch")
    if len(expected_checks) != len(receipt["command_file_checks"]):
        errors.append("command_file_binding_mismatch")
    first_check = receipt["command_file_checks"][0]
    if (receipt["executor_sha256_before"] != plan["executable_sha256"]
            or receipt["executor_sha256_before"] != first_check["sha256_before"]
            or receipt["executor_sha256_after"] != first_check["sha256_after"]
            or receipt["executor_unchanged"] != first_check["unchanged"]):
        errors.append("executor_binding_mismatch")
    source_ids = [item["id"] for item in source["episodes"]]
    receipt_ids = [item["episode_id"] for item in receipt["episode_receipts"]]
    if receipt_ids != source_ids or len(set(receipt_ids)) != len(receipt_ids):
        errors.append("episode_receipt_coverage_mismatch")
    verification = verify_run(run)
    if not verification["valid"]:
        errors.append("run_verification_failed")
    try:
        translated = import_source(source, adapter="generic")
        if translated["summary"] != run["summary"] or translated["episodes"] != run["episodes"]:
            errors.append("source_translation_mismatch")
    except (ValueError, TypeError, KeyError):
        errors.append("source_translation_failed")
    expected_identity = receipt["system_identity_sha256"]
    if system_identity is not None:
        actual_identity = hashlib.sha256(read_bytes(system_identity)).hexdigest()
        if expected_identity != actual_identity:
            errors.append("system_identity_binding_mismatch")
    elif expected_identity is not None:
        errors.append("system_identity_not_revalidated")
    return {
        "valid": not errors, "errors": errors, "executor_reexecuted": False,
        "process_sandboxed": False, "descendant_containment": False,
        "independent_replication": "not_established",
    }
