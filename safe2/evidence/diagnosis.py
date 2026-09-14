"""Evidence-bounded failure localization for an identified agent system."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

LEVEL_ORDER = {"strong": 5, "moderate": 4, "limited": 3, "insufficient": 2, "contradicted": 1}


def _assessment(candidate: dict[str, Any], observations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    support = [observations[item] for item in candidate["supporting_observation_ids"]]
    contradict = [observations[item] for item in candidate["contradicting_observation_ids"]]
    observed_direct = sum(item["basis"] == "observed" and item["directness"] == "direct" for item in support)
    observed_indirect = sum(
        item["basis"] == "observed" and item["directness"] != "direct" for item in support
    )
    declared = sum(item["basis"] == "declared" for item in support)
    missing = sum(item["basis"] == "missing" for item in support)
    observed_contradictions = sum(item["basis"] == "observed" for item in contradict)
    sources = {item["source_id"] for item in support if item["basis"] != "missing" and item["source_id"]}
    if observed_contradictions:
        level = "contradicted"
    elif observed_direct >= 2 and len(sources) >= 2 and not candidate["assumptions"]:
        level = "strong"
    elif observed_direct:
        level = "moderate"
    elif observed_indirect or declared:
        level = "limited"
    else:
        level = "insufficient"
    return {
        "level": level,
        "observed_direct_support": observed_direct,
        "observed_indirect_support": observed_indirect,
        "declared_support": declared,
        "missing_support": missing,
        "observed_contradictions": observed_contradictions,
        "distinct_support_sources": len(sources),
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[int, ...]:
    assessment = candidate["evidence_assessment"]
    return (
        LEVEL_ORDER[assessment["level"]], assessment["observed_direct_support"],
        assessment["distinct_support_sources"], assessment["observed_indirect_support"],
        assessment["declared_support"], -assessment["observed_contradictions"],
        -len(candidate["assumptions"]),
    )


def diagnose(payload: bytes, identity_payload: bytes) -> dict[str, Any]:
    """Localize candidate failures without converting evidence rank into root-cause proof."""
    if not payload or len(payload) > 1_000_000 or not identity_payload or len(identity_payload) > 1_000_000:
        raise ValueError("Diagnosis inputs must be nonempty files of at most 1 MB each")
    source = parse_json(payload)
    identity = parse_json(identity_payload)
    if validate_artifact("failure-source-v1", source):
        raise ValueError("Failure source violates its evidence contract")
    if validate_artifact("system-identity-manifest-v1", identity):
        raise ValueError("System identity violates its manifest contract")
    if source["subject"]["subject_id"] != identity["subject"]["subject_id"]:
        raise ValueError("Failure source and system identity subject do not match")
    if source["subject"]["system_fingerprint_sha256"] != identity["system_fingerprint_sha256"]:
        raise ValueError("Failure source and system identity fingerprint do not match")

    components = {item["component_id"]: item for item in identity["components"]}
    observation_map: dict[str, dict[str, Any]] = {}
    for observation in source["observations"]:
        observation_id = observation["observation_id"]
        if observation_id in observation_map:
            raise ValueError("Observation identifiers must be unique")
        observation_map[observation_id] = observation
        if any(item not in components for item in observation["component_ids"]):
            raise ValueError("Every observation component must exist in the system identity")
        if observation["basis"] == "missing":
            if (observation["source_id"] is not None or observation["source_ref"] is not None
                    or observation["directness"] != "unknown"):
                raise ValueError("Missing observations cannot claim an attributed source")
        elif observation["source_id"] is None or observation["source_ref"] is None:
            raise ValueError("Observed and declared observations require source attribution")

    candidate_ids: set[str] = set()
    assessed = []
    for candidate in source["candidates"]:
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            raise ValueError("Candidate identifiers must be unique")
        candidate_ids.add(candidate_id)
        primary = candidate["primary_component_id"]
        interaction = candidate["interacting_component_id"]
        if primary not in components or (interaction is not None and interaction not in components):
            raise ValueError("Every candidate component must exist in the system identity")
        if interaction == primary:
            raise ValueError("A failure interaction requires two different components")
        support_ids = set(candidate["supporting_observation_ids"])
        contradict_ids = set(candidate["contradicting_observation_ids"])
        if support_ids & contradict_ids:
            raise ValueError("One observation cannot both support and contradict a candidate")
        if not (support_ids | contradict_ids) <= observation_map.keys():
            raise ValueError("Candidate evidence must reference declared observations")
        assessment = _assessment(candidate, observation_map)
        assessed.append({
            "candidate_id": candidate_id,
            "location": {
                "primary_component_id": primary,
                "primary_category": components[primary]["category"],
                "interacting_component_id": interaction,
                "interacting_category": components[interaction]["category"] if interaction else None,
            },
            "failure_mode": candidate["failure_mode"], "description": candidate["description"],
            "supporting_observation_ids": candidate["supporting_observation_ids"],
            "contradicting_observation_ids": candidate["contradicting_observation_ids"],
            "assumptions": candidate["assumptions"], "repair_owner": candidate["repair_owner"],
            "recommended_action": candidate["recommended_action"], "evidence_assessment": assessment,
        })
    assessed.sort(key=lambda item: (_rank_key(item), item["candidate_id"]), reverse=True)
    for index, candidate in enumerate(assessed, 1):
        candidate["rank"] = index

    top = assessed[0]
    usable = top["evidence_assessment"]["level"] in {"strong", "moderate", "limited"}
    tied = len(assessed) > 1 and _rank_key(top) == _rank_key(assessed[1])
    if not usable:
        status, primary_id = "insufficient_evidence", None
    elif tied:
        status, primary_id = "competing_candidates", None
    else:
        status, primary_id = "ranked_candidate", top["candidate_id"]

    observations = source["observations"]
    attributed_sources = {
        item["source_id"] for item in observations if item["basis"] != "missing" and item["source_id"]
    }
    recommendations = []
    if primary_id:
        recommendations.append(top["recommended_action"])
    else:
        recommendations.append("Collect discriminating evidence before assigning a primary repair owner.")
    if any(item["basis"] == "missing" for item in observations):
        recommendations.append("Collect the observations explicitly marked missing.")
    if all(item["basis"] != "observed" for item in observations):
        recommendations.append("Add independently observed execution or state evidence.")
    if tied:
        recommendations.append("Test the leading candidates with an observation that supports one and contradicts the other.")

    result = {
        "schema_version": "safe2.failure-diagnosis.v1", "created_at": datetime.now(UTC).isoformat(),
        "source": {"failure_id": source["failure_id"], "sha256": hashlib.sha256(payload).hexdigest(),
                   "bytes": len(payload), "authentication": "not_checked"},
        "system_identity": {
            "subject_id": identity["subject"]["subject_id"],
            "system_fingerprint_sha256": identity["system_fingerprint_sha256"],
            "manifest_sha256": hashlib.sha256(identity_payload).hexdigest(),
            "configuration_verified": False,
        },
        "task": source["task"], "outcome": source["outcome"], "observations": observations,
        "evidence_summary": {
            "observed": sum(item["basis"] == "observed" for item in observations),
            "declared": sum(item["basis"] == "declared" for item in observations),
            "missing": sum(item["basis"] == "missing" for item in observations),
            "direct": sum(item["directness"] == "direct" for item in observations),
            "indirect": sum(item["directness"] == "indirect" for item in observations),
            "unknown_directness": sum(item["directness"] == "unknown" for item in observations),
            "distinct_attributed_sources": len(attributed_sources),
        },
        "candidates": assessed, "primary_candidate_id": primary_id, "diagnosis_status": status,
        "recommendations": recommendations, "decision_scope": "failure_localization_support_only",
        "root_cause_verified": False, "probability_estimate": False, "conformance_claim": False,
        "limitations": [
            "Candidate ranking is deterministic evidence triage, not a causal or probability estimate.",
            "Observed statements remain attributed and are not automatically independently reproduced.",
            "The system identity fingerprint binds declared composition but does not verify deployed state.",
            "Missing telemetry can change the ranking and must not be interpreted as clean evidence.",
            "A ranked candidate requires human or independently verified acceptance before remediation.",
            "Diagnosis does not establish task completion, safety, control effectiveness, or AI SAFE2 conformance.",
        ],
    }
    if validate_artifact("failure-diagnosis-v1", result):
        raise ValueError("Failure diagnosis produced an invalid artifact")
    return result
