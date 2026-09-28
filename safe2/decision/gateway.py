"""Policy-owned routing around optional semantic decision providers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import httpx

from safe2.contracts import validate_artifact
from safe2.decision.providers import DecisionProvider
from safe2.decision.sanitize import external_capsule, redact_local

RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _confidence(result: dict[str, Any]) -> float:
    values = []
    for answer in result.get("answers", {}).values():
        if isinstance(answer, dict):
            if isinstance(answer.get("confidence"), (int, float)):
                values.append(float(answer["confidence"]))
            elif isinstance(answer.get("noul"), (int, float)):
                values.append(max(float(answer["noul"]), 1 - float(answer["noul"])))
    return min(values) if values else 0.0


class DecisionGateway:
    def __init__(
        self,
        policy: dict[str, Any],
        primary: DecisionProvider | None = None,
        secondary: DecisionProvider | None = None,
    ):
        self.policy, self.primary, self.secondary = policy, primary, secondary

    def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        violations = validate_artifact("decision-request-v1", request)
        if violations:
            raise ValueError(
                f"decision request violates contract at {violations[0]['instance_path']}"
            )
        redacted, redactions = redact_local(request["structured_state"])
        risk = request["deterministic"]["risk_tier"]
        statuses = request["deterministic"]["evidence_status"]
        missing = sorted(
            name
            for name in request["deterministic"]["required_evidence"]
            if statuses.get(name) not in {"passed", "not_applicable"}
        )
        human = risk in self.policy["human_review_tiers"]
        provider_evidence: list[dict[str, Any]] = []
        route = "deterministic_only"
        primary_result = None
        if self.primary:
            try:
                primary_result = self.primary.decide(redacted, request["questions"])
                provider_evidence.append(
                    {
                        "provider": self.primary.name,
                        "model": self.primary.model,
                        "status": "observed",
                        "confidence": _confidence(primary_result),
                        "response_sha256": _digest(primary_result),
                    }
                )
                route = "primary_shadow"
            except (httpx.HTTPError, OSError, TypeError, ValueError) as exc:
                provider_evidence.append(
                    {
                        "provider": self.primary.name,
                        "model": self.primary.model,
                        "status": "unavailable",
                        "error_type": type(exc).__name__,
                    }
                )
                route = "provider_unavailable"
        confidence = _confidence(primary_result or {})
        needs_adjudication = (
            bool(primary_result) and confidence < self.policy["primary"]["minimum_confidence"]
        )
        external_ok = (
            request["external_adjudication_allowed"]
            and request["data_classification"] in self.policy["external_permitted_data_classes"]
            and request["decision_class"] in self.policy["external_allowed_decision_classes"]
        )
        capsule, capsule_gaps = external_capsule(request["structured_state"])
        if needs_adjudication and self.secondary and external_ok and capsule is not None:
            try:
                second = self.secondary.decide(capsule, request["questions"])
                provider_evidence.append(
                    {
                        "provider": self.secondary.name,
                        "model": self.secondary.model,
                        "status": "observed",
                        "confidence": _confidence(second),
                        "response_sha256": _digest(second),
                        "state_sha256": _digest(capsule),
                    }
                )
                route = "secondary_shadow_adjudication"
                human = True
            except (httpx.HTTPError, OSError, TypeError, ValueError) as exc:
                provider_evidence.append(
                    {
                        "provider": self.secondary.name,
                        "model": self.secondary.model,
                        "status": "unavailable",
                        "error_type": type(exc).__name__,
                    }
                )
                route = "secondary_unavailable"
                human = True
        elif needs_adjudication:
            route = "human_or_more_evidence"
            human = True
        review_plan = {
            "risk_tier": risk,
            "required_evidence": request["deterministic"]["required_evidence"],
            "missing_or_incomplete_evidence": missing,
            "human_approval_required": human,
            "external_adjudication_eligible": external_ok and capsule is not None,
            "provider_mode": self.policy["mode"],
            "model_may_reduce_risk": False,
        }
        result = {
            "schema_version": "safe2.decision-result.v1",
            "created_at": datetime.now(UTC).isoformat(),
            "decision_id": request["decision_id"],
            "request_sha256": _digest(request),
            "policy": {
                "policy_id": self.policy["policy_id"],
                "version": self.policy["version"],
                "mode": self.policy["mode"],
                "sha256": _digest(self.policy),
            },
            "route": {
                "outcome": route,
                "primary_confidence": confidence if primary_result else None,
                "redactions": redactions,
                "external_capsule_gaps": capsule_gaps,
            },
            "provider_evidence": provider_evidence,
            "review_plan": review_plan,
            "authority": {
                "merge_authorized": False,
                "release_authorized": False,
                "deployment_authorized": False,
                "exception_authorized": False,
                "policy_change_authorized": False,
            },
            "decision_scope": "advisory_review_routing_only",
            "limitations": [
                "Provider output is advisory evidence, not authority.",
                "Deterministic policy and required checks cannot be reduced by a model.",
                "Confidence must be calibrated on a representative labeled corpus.",
                "Human owners retain merge, release, deployment, exception, and policy authority.",
            ],
        }
        if validate_artifact("decision-result-v1", result):
            raise ValueError("decision gateway produced an invalid result")
        return result
