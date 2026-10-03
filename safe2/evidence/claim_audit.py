"""Evidence-bounded audit of agent claims against task-receipt criteria."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact


def _digest(value: dict[str, Any], excluded: str | None = None) -> str:
    body = {key: item for key, item in value.items() if key != excluded}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build(source_payload: bytes, receipt_payloads: list[bytes]) -> dict[str, Any]:
    """Compare explicit claims to bounded receipt results without inferring intent."""
    source = parse_json(source_payload)
    if validate_artifact("claim-audit-source-v1", source):
        raise ValueError("Claim-audit source violates its contract")
    if not receipt_payloads or len(receipt_payloads) > 100:
        raise ValueError("One to 100 task receipts are required")
    receipts = [parse_json(payload) for payload in receipt_payloads]
    if any(validate_artifact("task-receipt-v1", receipt) for receipt in receipts):
        raise ValueError("Task receipt violates its contract")
    if any(receipt["task_id"] != source["task_id"] for receipt in receipts):
        raise ValueError("Task receipt belongs to a different task")
    if any(receipt["input_sha256"] != source["input_sha256"] for receipt in receipts):
        raise ValueError("Task receipt belongs to a different task input")

    criteria: dict[str, list[dict[str, Any]]] = {}
    for receipt in receipts:
        for criterion in receipt["criteria"]:
            criteria.setdefault(criterion["id"], []).append(criterion)

    rows = []
    seen_claims: set[str] = set()
    for claim in source["claims"]:
        if claim["id"] in seen_claims:
            raise ValueError("Claim identifiers must be unique")
        seen_claims.add(claim["id"])
        references = claim["evidence_criteria_ids"]
        matched = [criteria.get(reference, []) for reference in references]
        flattened = [item for group in matched for item in group]
        if not references:
            status, reason = "unverifiable", "no_evidence_referenced"
        elif any(item["status"] == "contradicted" for item in flattened):
            status, reason = "contradicted", "referenced_criterion_contradicted"
        elif any(len(group) != 1 for group in matched) or any(
            item["status"] != "supported" for item in flattened
        ):
            status, reason = "unverifiable", "missing_or_unverifiable_criterion"
        else:
            outcome_consistent = True
            for item in flattened:
                tool = item.get("tool_summary")
                test = item.get("test_summary")
                if tool and tool.get("claimed_outcome") != claim["asserted_outcome"]:
                    outcome_consistent = False
                if test:
                    passed = (
                        test.get("exit_code") == 0
                        and not test.get("counts", {}).get("failed")
                        and not test.get("counts", {}).get("errors")
                    )
                    if claim["asserted_outcome"] == "succeeded" and not passed:
                        outcome_consistent = False
                    if claim["asserted_outcome"] == "failed" and passed:
                        outcome_consistent = False
            if outcome_consistent:
                status, reason = "evidence_consistent", "all_referenced_criteria_supported"
            else:
                status, reason = "contradicted", "referenced_outcome_conflicts_with_claim"
        rows.append(
            {
                "id": claim["id"],
                "claim_type": claim["claim_type"],
                "asserted_outcome": claim["asserted_outcome"],
                "status": status,
                "reason": reason,
                "evidence_criteria_ids": references,
                "matched_criteria": len(flattened),
                "explicit_limitation_disclosure": claim["asserted_outcome"]
                in {"failed", "unavailable", "not_attempted"},
            }
        )

    total = len(rows)
    counts = {
        state: sum(row["status"] == state for row in rows)
        for state in ("evidence_consistent", "contradicted", "unverifiable")
    }
    disclosed = sum(row["explicit_limitation_disclosure"] for row in rows)
    result: dict[str, Any] = {
        "schema_version": "safe2.claim-audit.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "audit_id": source["audit_id"],
        "task_id": source["task_id"],
        "source_sha256": hashlib.sha256(source_payload).hexdigest(),
        "receipt_sha256": sorted(
            {hashlib.sha256(payload).hexdigest() for payload in receipt_payloads}
        ),
        "claims": rows,
        "summary": {
            "total": total,
            **counts,
            "explicit_limitation_disclosures": disclosed,
            "evidence_coverage_ratio": round(counts["evidence_consistent"] / total, 6),
            "contradiction_ratio": round(counts["contradicted"] / total, 6),
        },
        "gate": "evidence_consistent"
        if not counts["contradicted"] and not counts["unverifiable"]
        else "review_required",
        "completion_verified": False,
        "deception_inferred": False,
        "conformance_claim": False,
        "limitations": [
            "Evidence consistency is not proof that the task was correctly or completely performed.",
            "A contradiction or missing receipt does not establish deception, intent, or model dishonesty.",
            "Unsigned task receipts can be replaced or fabricated by an actor controlling the evidence path.",
            "Ratios describe this supplied claim set only; they are not a model benchmark or probability.",
        ],
    }
    result["integrity_sha256"] = _digest(result, "integrity_sha256")
    if validate_artifact("claim-audit-v1", result):
        raise ValueError("Claim audit violates its generated contract")
    return result


def render_markdown(result: dict[str, Any]) -> str:
    """Render a compact human review card without importing claim prose."""
    summary = result["summary"]
    lines = [
        "# Agent Claim Audit",
        "",
        f"**Gate:** {result['gate'].replace('_', ' ').upper()}",
        "",
        "## Evidence card",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| Claims reviewed | {summary['total']} |",
        f"| Evidence-consistent | {summary['evidence_consistent']} |",
        f"| Contradicted | {summary['contradicted']} |",
        f"| Unverifiable | {summary['unverifiable']} |",
        f"| Explicit failure/unavailability disclosures | {summary['explicit_limitation_disclosures']} |",
        f"| Evidence coverage | {summary['evidence_coverage_ratio']:.1%} |",
        f"| Contradiction rate | {summary['contradiction_ratio']:.1%} |",
        "",
        "## Claim results",
        "",
        "| Claim ID | Type | Asserted outcome | Evidence result |",
        "|---|---|---|---|",
    ]
    for row in result["claims"]:
        lines.append(
            f"| {row['id']} | {row['claim_type']} | {row['asserted_outcome']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Decision boundary",
            "",
            "This audit does not verify completion and does not infer deception. A human owner must decide whether the precommitted acceptance criteria and provenance are sufficient.",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in result["limitations"]],
            "",
        ]
    )
    return "\n".join(lines)
