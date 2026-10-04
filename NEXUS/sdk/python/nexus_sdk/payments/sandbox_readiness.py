"""Sandbox Rail Readiness: deterministic evidence gate for rail activation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance, GatewayReadiness
from nexus_sdk.payments.objects import canonical_hash, utcnow

__all__ = [
    "RailActivationMode",
    "SandboxEvidenceVerifier",
    "SandboxRailReadinessGate",
    "SandboxReadinessProfile",
    "SandboxReadinessReport",
    "SandboxRunEvidence",
]


class RailActivationMode(str, Enum):
    DISABLED = "disabled"
    OBSERVE_ONLY = "observe_only"
    ENFORCED = "enforced"


@dataclass(frozen=True)
class SandboxRunEvidence:
    """Authenticated, payload-minimized evidence from one sandbox counterparty."""

    run_id: str
    counterparty_id: str
    environment_id: str
    contract_digest: str
    binding_digest: str
    policy_stack_digest: str
    execution_profile_digest: str
    conformance_report_digest: str
    outcomes: tuple[tuple[str, bool], ...]
    started_at: str
    completed_at: str
    observer_id: str
    sandbox_only: bool
    production_credentials_used: bool
    real_value_moved: bool
    payloads_omitted: bool
    proof: str

    @property
    def evidence_digest(self) -> str:
        values = dict(self.__dict__)
        values["outcomes"] = [list(item) for item in self.outcomes]
        values.pop("proof")
        return canonical_hash(values)


class SandboxEvidenceVerifier(Protocol):
    assurance: ComponentAssurance

    def verify(self, evidence: SandboxRunEvidence) -> bool: ...


@dataclass(frozen=True)
class SandboxReadinessProfile:
    profile_id: str
    contract_digest: str
    binding_digest: str
    policy_stack_digest: str
    execution_profile_digest: str
    trusted_observer_id: str
    trusted_counterparties: frozenset[str]
    required_outcomes: frozenset[str] = frozenset({
        "positive_binding",
        "amount_mutation_blocked",
        "destination_mutation_blocked",
        "replay_blocked",
        "downgrade_blocked",
        "revocation_race_blocked",
        "pre_submit_timeout_safe",
        "post_submit_timeout_ambiguous",
        "reconciliation_no_resubmit",
        "settlement_binding_verified",
        "authoritative_failure_releases",
    })
    minimum_counterparties: int = 2
    max_evidence_age_seconds: int = 86_400
    max_run_duration_seconds: int = 3_600

    def __post_init__(self) -> None:
        required = (
            self.profile_id, self.contract_digest, self.binding_digest,
            self.policy_stack_digest, self.execution_profile_digest,
            self.trusted_observer_id,
        )
        if (
            not all(required)
            or not self.required_outcomes
            or self.minimum_counterparties < 2
            or len(self.trusted_counterparties) < self.minimum_counterparties
            or self.max_evidence_age_seconds < 1
            or self.max_run_duration_seconds < 1
        ):
            raise ValueError("complete sandbox profile and independent counterparties are required")

    @property
    def profile_digest(self) -> str:
        return canonical_hash({
            "profile_id": self.profile_id,
            "contract_digest": self.contract_digest,
            "binding_digest": self.binding_digest,
            "policy_stack_digest": self.policy_stack_digest,
            "execution_profile_digest": self.execution_profile_digest,
            "trusted_observer_id": self.trusted_observer_id,
            "trusted_counterparties": sorted(self.trusted_counterparties),
            "required_outcomes": sorted(self.required_outcomes),
            "minimum_counterparties": self.minimum_counterparties,
            "max_evidence_age_seconds": self.max_evidence_age_seconds,
            "max_run_duration_seconds": self.max_run_duration_seconds,
        })


@dataclass(frozen=True)
class SandboxReadinessReport:
    maximum_mode: RailActivationMode
    ready_for_enforcement: bool
    profile_digest: str
    accepted_run_digests: tuple[str, ...]
    counterparties: tuple[str, ...]
    environments: tuple[str, ...]
    findings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "maximum_mode": self.maximum_mode.value,
            "ready_for_enforcement": self.ready_for_enforcement,
            "profile_digest": self.profile_digest,
            "accepted_run_digests": list(self.accepted_run_digests),
            "counterparties": list(self.counterparties),
            "environments": list(self.environments),
            "findings": list(self.findings),
            "privacy": "payment payloads and credentials omitted",
        }


class SandboxRailReadinessGate:
    """Bound rail activation to authenticated negative-path sandbox evidence."""

    human_name = "Sandbox Rail Readiness"
    technical_name = "SandboxRailReadinessGate"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, profile: SandboxReadinessProfile,
                 verifier: SandboxEvidenceVerifier,
                 now=utcnow) -> None:
        self.profile = profile
        self.verifier = verifier
        self.now = now

    def evaluate(self, evidence_items: tuple[SandboxRunEvidence, ...], *,
                 gateway_readiness: GatewayReadiness) -> SandboxReadinessReport:
        current_time = self.now()
        if current_time.tzinfo is None:
            raise ValueError("sandbox readiness clock must include a timezone")
        findings: list[str] = []
        accepted: dict[str, SandboxRunEvidence] = {}
        seen: dict[str, str] = {}
        for evidence in evidence_items:
            if not isinstance(evidence, SandboxRunEvidence):
                findings.append("unknown sandbox evidence type")
                continue
            try:
                digest = evidence.evidence_digest
            except (TypeError, ValueError, AttributeError):
                findings.append(f"{evidence.run_id or 'unknown-run'}: evidence is malformed")
                continue
            prior = seen.get(evidence.run_id)
            if prior is not None:
                if prior != digest:
                    findings.append(f"{evidence.run_id}: conflicting run evidence")
                continue
            seen[evidence.run_id] = digest
            problems = self._problems(evidence, current_time)
            if problems:
                findings.extend(f"{evidence.run_id}: {problem}" for problem in problems)
                continue
            accepted[evidence.run_id] = evidence

        counterparties = tuple(sorted({item.counterparty_id for item in accepted.values()}))
        environments = tuple(sorted({item.environment_id for item in accepted.values()}))
        if accepted and len(counterparties) < self.profile.minimum_counterparties:
            findings.append("independent sandbox counterparty threshold not met")
        if accepted and len(environments) < self.profile.minimum_counterparties:
            findings.append("independent sandbox environment threshold not met")
        if accepted and not gateway_readiness.ready:
            findings.append("gateway execution plane is not deployment-ready")

        ready = bool(accepted) and not findings and (
            len(counterparties) >= self.profile.minimum_counterparties
            and len(environments) >= self.profile.minimum_counterparties
            and gateway_readiness.ready
        )
        if ready:
            mode = RailActivationMode.ENFORCED
        elif accepted:
            mode = RailActivationMode.OBSERVE_ONLY
        else:
            mode = RailActivationMode.DISABLED
            findings.append("no authenticated passing sandbox run exists")
        return SandboxReadinessReport(
            maximum_mode=mode,
            ready_for_enforcement=ready,
            profile_digest=self.profile.profile_digest,
            accepted_run_digests=tuple(sorted(item.evidence_digest for item in accepted.values())),
            counterparties=counterparties,
            environments=environments,
            findings=tuple(findings),
        )

    def _problems(self, evidence: SandboxRunEvidence,
                  current_time: datetime) -> tuple[str, ...]:
        problems: list[str] = []
        required_strings = (
            evidence.run_id, evidence.counterparty_id, evidence.environment_id,
            evidence.contract_digest, evidence.binding_digest,
            evidence.policy_stack_digest, evidence.execution_profile_digest,
            evidence.conformance_report_digest, evidence.observer_id, evidence.proof,
        )
        if not all(isinstance(value, str) and value for value in required_strings):
            problems.append("required evidence identity is missing")
            return tuple(problems)
        try:
            started = datetime.fromisoformat(evidence.started_at)
            completed = datetime.fromisoformat(evidence.completed_at)
        except (TypeError, ValueError):
            problems.append("run timestamps are invalid")
            return tuple(problems)
        if started.tzinfo is None or completed.tzinfo is None:
            problems.append("run timestamps need a timezone")
        else:
            age = (current_time - completed).total_seconds()
            duration = (completed - started).total_seconds()
            if not 0 <= age <= self.profile.max_evidence_age_seconds:
                problems.append("run evidence is stale or from the future")
            if not 0 <= duration <= self.profile.max_run_duration_seconds:
                problems.append("run duration is invalid or exceeds its bound")
        bindings = (
            (evidence.counterparty_id in self.profile.trusted_counterparties,
             "counterparty is not trusted for sandbox validation"),
            (evidence.observer_id == self.profile.trusted_observer_id,
             "sandbox observer identity mismatch"),
            (evidence.contract_digest == self.profile.contract_digest,
             "rail contract digest mismatch"),
            (evidence.binding_digest == self.profile.binding_digest,
             "rail binding digest mismatch"),
            (evidence.policy_stack_digest == self.profile.policy_stack_digest,
             "policy stack digest mismatch"),
            (evidence.execution_profile_digest == self.profile.execution_profile_digest,
             "execution profile digest mismatch"),
            (evidence.sandbox_only is True, "run was not sandbox-only"),
            (evidence.production_credentials_used is False,
             "production credentials were used"),
            (evidence.real_value_moved is False, "real value moved during sandbox validation"),
            (evidence.payloads_omitted is True, "evidence did not minimize payment payloads"),
        )
        problems.extend(reason for accepted, reason in bindings if not accepted)
        if not isinstance(evidence.outcomes, tuple):
            problems.append("sandbox outcomes are malformed")
        else:
            names: list[str] = []
            passed: dict[str, bool] = {}
            for item in evidence.outcomes:
                if (
                    not isinstance(item, tuple)
                    or len(item) != 2
                    or not isinstance(item[0], str)
                    or not item[0]
                    or type(item[1]) is not bool
                ):
                    problems.append("sandbox outcomes are malformed")
                    break
                names.append(item[0])
                passed[item[0]] = item[1]
            if len(names) != len(set(names)):
                problems.append("sandbox outcomes contain duplicate case names")
            missing = self.profile.required_outcomes.difference(passed)
            if missing:
                problems.append("required sandbox outcomes are missing: " + ", ".join(sorted(missing)))
            failed = sorted(name for name in self.profile.required_outcomes if passed.get(name) is False)
            if failed:
                problems.append("required sandbox outcomes failed: " + ", ".join(failed))
        try:
            verified = self.verifier.verify(evidence) is True
        except Exception:
            verified = False
        if not verified:
            problems.append("sandbox evidence proof is invalid or unavailable")
        return tuple(problems)
