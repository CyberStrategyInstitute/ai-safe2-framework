"""Compare compatible, verified evidence without implying independent replication."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .grading import grade_episode
from .integrity import seal
from .model import verify_run

_OUTCOMES = ("unauthorized_change", "legitimate_completed", "false_block")


def _key(episode: dict[str, Any]) -> tuple[str, int, str]:
    return episode["scenario_id"], episode["trial"], episode["treatment"]


def _identity(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "integrity_sha256": run["integrity_sha256"],
        "provider": copy.deepcopy(run["provider"]),
        "provenance": copy.deepcopy(run["provenance"]),
    }


def _agreement(
    left: dict[tuple[str, int, str], dict[str, Any]],
    right: dict[tuple[str, int, str], dict[str, Any]],
) -> dict[str, Any]:
    agreements = disagreements = incomplete = conflicts = 0
    for key in sorted(left):
        # Provider grades and summaries are never used as the answer key.
        left_grade = grade_episode(left[key])
        right_grade = grade_episode(right[key])
        if "conflict" in {left_grade["status"], right_grade["status"]}:
            conflicts += 1
        left_outcomes = tuple(left_grade[field] for field in _OUTCOMES)
        right_outcomes = tuple(right_grade[field] for field in _OUTCOMES)
        if (
            left_grade["status"] == "incomplete"
            or right_grade["status"] == "incomplete"
            or all(value is None for value in left_outcomes)
            or all(value is None for value in right_outcomes)
        ):
            incomplete += 1
        elif left_outcomes == right_outcomes:
            agreements += 1
        else:
            disagreements += 1
    evaluated = agreements + disagreements
    return {
        "evaluated_pairs": evaluated,
        "agreements": agreements,
        "disagreements": disagreements,
        "incomplete_pairs": incomplete,
        "conflict_pairs": conflicts,
        "rate": agreements / evaluated if evaluated else None,
    }


def compare_runs(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Require pinned experiment/action/coverage parity before comparing outcomes.

    Comparable means declared experimental conditions match. External state and
    operator independence are not authenticated by this offline comparison.
    """
    for name, run in (("left", left), ("right", right)):
        if not verify_run(run)["valid"]:
            raise ValueError(f"The {name} challenge run failed verification.")

    left_cases = {_key(episode): episode for episode in left["episodes"]}
    right_cases = {_key(episode): episode for episode in right["episodes"]}
    mismatches = [
        "experiment." + field
        for field in sorted(set(left["experiment"]) | set(right["experiment"]))
        if left["experiment"].get(field) != right["experiment"].get(field)
    ]
    if set(left_cases) != set(right_cases):
        mismatches.append("episode_coverage")
    elif any(left_cases[key]["action"] != right_cases[key]["action"] for key in left_cases):
        mismatches.append("episode_actions")

    limitations = [
        (
            "Comparable means declared experiment, action, and case/trial/treatment coverage match; "
            "it does not authenticate external conditions or implementation equivalence."
        ),
        (
            "Outcome agreement is an episode-level descriptive rate over complete, independently "
            "regraded state outcomes, not a probability of success, superiority, or causal prevention."
        ),
        (
            "Integrity checks detect changed artifacts; this comparison does not authenticate "
            "provider signatures, source observers, approvals, or ledger claims."
        ),
        (
            "Independent replication is not established by translation, matching results, "
            "or different provider names; independent operators and study evidence are still required."
        ),
        "Conflict pairs remain visible even when their observed state outcomes agree.",
    ]
    if left["integrity_sha256"] == right["integrity_sha256"]:
        limitations.append("Both inputs are the same sealed artifact, not two executions.")
    left_provenance = left["provenance"]
    right_provenance = right["provenance"]
    if left_provenance["producer_id"] == right_provenance["producer_id"]:
        limitations.append("The inputs declare the same producer; producer independence is absent.")
    if (
        left_provenance["source_sha256"] is not None
        and left_provenance["source_sha256"] == right_provenance["source_sha256"]
    ):
        limitations.append("Both inputs bind the same source hash; this is source reuse, not replication.")
    if any(
        run["provenance"]["kind"] in {"native_fixture", "synthetic_import"}
        for run in (left, right)
    ):
        limitations.append("At least one input is a synthetic fixture; no live-agent efficacy is established.")
    if mismatches:
        limitations.append("Conditions differ; outcomes are not pooled and no agreement rate is reported.")

    return seal({
        "schema_version": "safe2.challenge-comparison.v1",
        "comparison_id": str(uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "left": _identity(left),
        "right": _identity(right),
        "comparable": not mismatches,
        "mismatches": mismatches,
        "outcome_agreement": _agreement(left_cases, right_cases) if not mismatches else None,
        "independent_replication": "not_established",
        "limitations": limitations,
    })
