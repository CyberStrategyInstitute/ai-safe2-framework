"""Local artifact receipts, not semantic completion or honesty certification."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from safe2.challenge.io import parse_json, read_bytes, safe_path
from safe2.contracts import validate_artifact
from safe2.evidence.report_auth import verify_report
from safe2.evidence.test_result import evaluate_test_report
from safe2.evidence.tool_result import evaluate_tool_report

MAX_ARTIFACT_BYTES = 1_000_000


def _relative_path(value: str) -> Path:
    # Portable contract: slash-separated paths, no platform-dependent aliases.
    win = PureWindowsPath(value)
    posix = PurePosixPath(value)
    if (
        win.drive or posix.is_absolute() or "\\" in value or ":" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError("Artifact paths must be normalized relative paths without traversal")
    return Path(*posix.parts)


def validate_task_input(document: dict[str, Any]) -> None:
    """Validate declarations without reading artifacts or authenticating their claims."""
    json.dumps(document, allow_nan=False)
    if validate_artifact("task-receipt-input-v1", document):
        raise ValueError("Task receipt input violates task-receipt-input-v1")
    if document["parent_task_id"] == document["task_id"]:
        raise ValueError("A task cannot be its own parent")
    ids = [criterion["id"] for criterion in document["criteria"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Criterion identifiers must be unique")
    usage_ids = [item["event_id"] for item in document["usage"]]
    if len(usage_ids) != len(set(usage_ids)):
        raise ValueError("Usage event identifiers must be unique; duplicate accounting rejected")
    for item in document["usage"]:
        if item["basis"] == "unknown":
            if item["value"] is not None:
                raise ValueError("Unknown usage must be null, not zero or an estimate")
        elif item["value"] is None or item["source_ref"] is None:
            raise ValueError("Reported and estimated usage require a value and source reference")
        if (item["metric"] != "api_cost_usd" and item["value"] is not None
                and int(item["value"]) != item["value"]):
            raise ValueError("Token and elapsed-millisecond counts must be integers")


def evaluate_task(
    document: dict[str, Any], artifact_root: Path, *,
    trusted_public_key: Path | None = None, require_authentication: bool = False,
) -> dict[str, Any]:
    """Check bytes and imported reports; this does not independently execute work."""
    validate_task_input(document)
    if require_authentication and trusted_public_key is None:
        raise ValueError("Required authentication needs an operator-supplied trusted public key")
    paths = [_relative_path(item["path"]) for item in document["criteria"]]
    attestations = [(_relative_path(item["attestation_path"]) if "attestation_path" in item else None)
                    for item in document["criteria"]]
    root = safe_path(artifact_root)
    if not root.is_dir():
        raise ValueError("Artifact root must be an existing trusted local directory")
    results = []
    for criterion, relative, attestation_path in zip(document["criteria"], paths, attestations, strict=True):
        observed = None
        test_summary = None
        tool_summary = None
        authentication = "not_applicable" if criterion["kind"] == "artifact_sha256" else "not_present"
        try:
            payload = read_bytes(root / relative, limit=MAX_ARTIFACT_BYTES)
            observed = hashlib.sha256(payload).hexdigest()
            status = "supported" if observed == criterion["expected_sha256"] else "contradicted"
            reason = "digest_matches" if status == "supported" else "digest_mismatch"
            if criterion["kind"] == "test_report":
                if status == "supported":
                    status, reason, test_summary = evaluate_test_report(
                        payload, task_id=document["task_id"],
                        revision=criterion["expected_revision"],
                        environment=criterion["expected_environment"],
                    )
                else:
                    status, reason = "unverifiable", "test_report_digest_mismatch"
            elif criterion["kind"] == "tool_report":
                if status == "supported":
                    status, reason, tool_summary = evaluate_tool_report(
                        payload, task_id=document["task_id"],
                        revision=criterion["expected_revision"],
                        environment=criterion["expected_environment"],
                        call_id=criterion["expected_call_id"], tool=criterion["expected_tool"],
                        claimed_outcome=criterion["claimed_outcome"],
                    )
                else:
                    status, reason = "unverifiable", "tool_report_digest_mismatch"
            if criterion["kind"] != "artifact_sha256":
                if attestation_path is not None:
                    if trusted_public_key is None:
                        authentication = "unverified_no_trusted_key"
                    else:
                        try:
                            attestation = parse_json(read_bytes(root / attestation_path, limit=16384))
                            authentication = verify_report(payload, attestation, trusted_public_key)
                        except (OSError, TypeError, ValueError, RecursionError):
                            authentication = "authentication_unavailable"
                checked_invalid = (trusted_public_key is not None and attestation_path is not None
                                   and authentication != "authenticated_trusted_key")
                if checked_invalid or (require_authentication and authentication != "authenticated_trusted_key"):
                    status, reason = "unverifiable", "report_authentication_not_established"
        except FileNotFoundError:
            status, reason = "unverifiable", "artifact_missing"
        except (OSError, ValueError):
            status, reason = "unverifiable", "artifact_unreadable_unsafe_or_over_limit"
        result: dict[str, Any] = {
            "id": criterion["id"], "kind": criterion["kind"],
            "status": status, "reason": reason, "observed_sha256": observed,
            "authentication": authentication,
        }
        if test_summary is not None:
            result["test_summary"] = test_summary
        if tool_summary is not None:
            result["tool_summary"] = tool_summary
        results.append(result)
    counts = {state: sum(item["status"] == state for item in results)
              for state in ("supported", "contradicted", "unverifiable")}
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "schema_version": "safe2.task-receipt.v1",
        "task_id": document["task_id"], "parent_task_id": document["parent_task_id"],
        "harness": document["harness"], "observed_at": datetime.now(UTC).isoformat(),
        "input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "verification_scope": (
            "local_artifact_and_imported_report_consistency"
            if any(item["kind"] != "artifact_sha256" for item in document["criteria"])
            else "local_artifact_byte_identity_only"
        ),
        "criteria": results, "counts": counts,
        "authentication_policy": "required_for_reports" if require_authentication else "optional",
        "usage": document["usage"], "usage_verification": "unverified_source_declarations",
        "completion_verified": False, "conformance_claim": False,
        "limitations": [
            "Matching bytes do not prove correct behavior, successful tests, or task completion.",
            "Test summaries describe imported reports, not independently witnessed test execution.",
            "Tool summaries describe imported outcomes; matching a blocker claim is not task success.",
            "Criteria are supplied declarations, not proof they were agreed before execution.",
            "Only authenticated_trusted_key establishes report origin; it does not prove execution or truth.",
            "Usage is not independently billed or aggregated across tasks or subscriptions.",
            "Use a trusted immutable root; this is not a sandbox against concurrent filesystem mutation.",
        ],
    }


def render_receipt(receipt: dict[str, Any]) -> str:
    """Render only validated identifiers and fixed descriptions, never raw outputs."""
    counts = receipt["counts"]
    lines = [
        "# AI SAFE² task receipt", "", f"Task: `{receipt['task_id']}`",
        f"Harness: `{receipt['harness']}`", "",
        f"Scope: `{receipt['verification_scope']}`. Task completion is not verified.", "",
        f"Report authentication policy: `{receipt['authentication_policy']}`.", "",
        (f"Supported: {counts['supported']} | Contradicted: {counts['contradicted']} | "
         f"Unverifiable: {counts['unverifiable']}"), "",
        "| Criterion | Result | Reason | Authentication |", "|---|---|---|---|",
    ]
    for item in receipt["criteria"]:
        lines.append(f"| {item['id']} | {item['status']} | {item['reason']} | {item['authentication']} |")
    for item in receipt["criteria"]:
        if "test_summary" in item:
            summary = item["test_summary"]
            detail = summary["counts"]
            lines.extend(["", (f"Reported tests ({item['id']}): {detail['passed']} passed, "
                               f"{detail['failed']} failed, {detail['errors']} errors, "
                               f"{detail['skipped']} skipped; exit {summary['exit_code']}. "
                               "Imported report; execution not authenticated."), ""])
        if "tool_summary" in item:
            summary = item["tool_summary"]
            lines.extend(["", (f"Tool outcome ({item['id']}): claimed {summary['claimed_outcome']}; "
                               f"reported {summary['reported_outcome']}. "
                               "Imported report; execution not authenticated."), ""])
    lines.extend(["", "## Next action", ""])
    if counts["contradicted"]:
        lines.append("Review conflicting artifact, test, or tool evidence; correct unsupported claims.")
    elif counts["unverifiable"]:
        lines.append("Resolve missing, stale, malformed, or incomplete evidence, then repeat verification.")
    else:
        lines.append("Applicable consistency checks passed. Authenticated execution and acceptance remain separate checks.")
    lines.extend(["", "## Usage (unverified declarations)", ""])
    if not receipt["usage"]:
        lines.append("Unavailable; not assumed to be zero.")
    for item in receipt["usage"]:
        value = "unavailable" if item["value"] is None else str(item["value"])
        lines.append(f"- {item['metric']}: {value} ({item['basis']}).")
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in receipt["limitations"])
    return "\n".join(lines) + "\n"
