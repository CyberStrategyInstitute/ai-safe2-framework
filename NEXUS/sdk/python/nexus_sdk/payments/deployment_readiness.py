"""Deployment Proof & Readiness: signed, fail-closed production admission."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance, GatewayReadiness
from nexus_sdk.payments.objects import canonical_hash, utcnow
from nexus_sdk.payments.sandbox_readiness import (
    RailActivationMode,
    SandboxReadinessReport,
)

__all__ = [
    "DEFAULT_DEPLOYMENT_CONTROLS",
    "DeploymentApprovalEvidence",
    "DeploymentApprovalVerifier",
    "DeploymentControlEvidence",
    "DeploymentEvidenceVerifier",
    "DeploymentReadinessAuthority",
    "DeploymentReadinessDecision",
    "DeploymentReadinessIssuer",
    "DeploymentReadinessProfile",
]


DEFAULT_DEPLOYMENT_CONTROLS = frozenset({
    "execution_plane_ready",
    "policy_parity_live",
    "key_guardian_isolated",
    "runtime_verifier_independent",
    "state_backup_restore",
    "evidence_chain_restore",
    "evidence_completeness",
    "revocation_kill_drill",
    "ambiguous_recovery_drill",
    "sandbox_enforced_ready",
    "network_bypass_prevention",
    "monitoring_alert_delivery",
    "incident_escalation",
    "evidence_export",
    "evidence_deletion",
    "evidence_legal_hold",
    "data_residency_declared",
    "accountable_ownership_declared",
})


@dataclass(frozen=True)
class DeploymentApprovalEvidence:
    """Authenticated human change approval for one exact readiness profile."""

    approval_id: str
    deployment_id: str
    environment_id: str
    profile_digest: str
    approver_id: str
    approved_mode: str
    approved_at: str
    expires_at: str
    proof: str

    @property
    def approval_digest(self) -> str:
        values = dict(self.__dict__)
        values.pop("proof")
        return canonical_hash(values)


@dataclass(frozen=True)
class DeploymentControlEvidence:
    """Authenticated, payload-minimized proof for one deployment control."""

    evidence_id: str
    control_id: str
    deployment_id: str
    environment_id: str
    software_digest: str
    configuration_digest: str
    policy_profile_digest: str
    sandbox_profile_digest: str
    artifact_digest: str
    assessor_id: str
    observed_at: str
    passed: bool
    proof: str

    @property
    def evidence_digest(self) -> str:
        values = dict(self.__dict__)
        values.pop("proof")
        return canonical_hash(values)


class DeploymentEvidenceVerifier(Protocol):
    """Verify evidence outside the agent and deployment under assessment."""

    assurance: ComponentAssurance

    def verify(self, evidence: DeploymentControlEvidence) -> bool: ...


class DeploymentApprovalVerifier(Protocol):
    """Authenticate human approval independently of the requesting agent."""

    assurance: ComponentAssurance

    def verify(self, approval: DeploymentApprovalEvidence) -> bool: ...


class DeploymentReadinessIssuer(Protocol):
    """Seal the final decision through an independently protected authority."""

    authority_id: str
    assurance: ComponentAssurance

    def seal(self, decision: DeploymentReadinessDecision) -> str: ...


@dataclass(frozen=True)
class DeploymentReadinessProfile:
    profile_id: str
    deployment_id: str
    environment_id: str
    software_digest: str
    configuration_digest: str
    policy_profile_digest: str
    sandbox_profile_digest: str
    accountable_owner_id: str
    security_owner_id: str
    data_owner_id: str
    data_jurisdiction: str
    authority_id: str
    trusted_assessors: frozenset[str]
    authorized_approvers: frozenset[str]
    required_controls: frozenset[str] = DEFAULT_DEPLOYMENT_CONTROLS
    minimum_distinct_assessors: int = 2
    max_evidence_age_seconds: int = 86_400
    decision_validity_seconds: int = 3_600

    def __post_init__(self) -> None:
        required = (
            self.profile_id, self.deployment_id, self.environment_id,
            self.software_digest, self.configuration_digest,
            self.policy_profile_digest, self.sandbox_profile_digest,
            self.accountable_owner_id, self.security_owner_id,
            self.data_owner_id, self.data_jurisdiction, self.authority_id,
        )
        if (
            not all(isinstance(value, str) and value for value in required)
            or self.accountable_owner_id == self.security_owner_id
            or not self.required_controls
            or not all(
                isinstance(value, str) and value
                for values in (
                    self.required_controls,
                    self.trusted_assessors,
                    self.authorized_approvers,
                )
                for value in values
            )
            or self.minimum_distinct_assessors < 2
            or len(self.trusted_assessors) < self.minimum_distinct_assessors
            or not self.authorized_approvers
            or self.trusted_assessors.intersection(self.authorized_approvers)
            or self.max_evidence_age_seconds < 1
            or self.decision_validity_seconds < 1
        ):
            raise ValueError(
                "complete deployment identity, separated owners, assessors, and approvers are required"
            )

    @property
    def profile_digest(self) -> str:
        return canonical_hash({
            "profile_id": self.profile_id,
            "deployment_id": self.deployment_id,
            "environment_id": self.environment_id,
            "software_digest": self.software_digest,
            "configuration_digest": self.configuration_digest,
            "policy_profile_digest": self.policy_profile_digest,
            "sandbox_profile_digest": self.sandbox_profile_digest,
            "accountable_owner_id": self.accountable_owner_id,
            "security_owner_id": self.security_owner_id,
            "data_owner_id": self.data_owner_id,
            "data_jurisdiction": self.data_jurisdiction,
            "authority_id": self.authority_id,
            "trusted_assessors": sorted(self.trusted_assessors),
            "authorized_approvers": sorted(self.authorized_approvers),
            "required_controls": sorted(self.required_controls),
            "minimum_distinct_assessors": self.minimum_distinct_assessors,
            "max_evidence_age_seconds": self.max_evidence_age_seconds,
            "decision_validity_seconds": self.decision_validity_seconds,
        })


@dataclass(frozen=True)
class DeploymentReadinessDecision:
    ready: bool
    maximum_mode: RailActivationMode
    profile_digest: str
    deployment_id: str
    environment_id: str
    approved_by: str
    approval_digest: str
    authority_id: str
    evidence_digests: tuple[str, ...]
    assessor_ids: tuple[str, ...]
    findings: tuple[str, ...]
    issued_at: str
    expires_at: str
    proof: str = ""

    @property
    def decision_digest(self) -> str:
        values = dict(self.__dict__)
        values["maximum_mode"] = self.maximum_mode.value
        values["evidence_digests"] = list(self.evidence_digests)
        values["assessor_ids"] = list(self.assessor_ids)
        values["findings"] = list(self.findings)
        values.pop("proof")
        return canonical_hash(values)

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "maximum_mode": self.maximum_mode.value,
            "profile_digest": self.profile_digest,
            "deployment_id": self.deployment_id,
            "environment_id": self.environment_id,
            "approved_by": self.approved_by,
            "approval_digest": self.approval_digest,
            "authority_id": self.authority_id,
            "evidence_digests": list(self.evidence_digests),
            "assessor_ids": list(self.assessor_ids),
            "findings": list(self.findings),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "decision_digest": self.decision_digest,
            "proof": self.proof,
            "privacy": "payment payloads, credentials, and account details omitted",
        }


class DeploymentReadinessAuthority:
    """Issue a signed production-admission decision from exact deployment proof."""

    human_name = "Deployment Proof & Readiness"
    technical_name = "DeploymentReadinessAuthority"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, profile: DeploymentReadinessProfile,
                 verifier: DeploymentEvidenceVerifier,
                 approval_verifier: DeploymentApprovalVerifier,
                 issuer: DeploymentReadinessIssuer,
                 now=utcnow) -> None:
        self.profile = profile
        self.verifier = verifier
        self.approval_verifier = approval_verifier
        self.issuer = issuer
        self.now = now

    def assess(self, evidence_items: tuple[DeploymentControlEvidence, ...], *,
               gateway_readiness: GatewayReadiness,
               sandbox_report: SandboxReadinessReport,
               approval: DeploymentApprovalEvidence) -> DeploymentReadinessDecision:
        current_time = self.now()
        if current_time.tzinfo is None:
            raise ValueError("deployment readiness clock must include a timezone")
        findings: list[str] = []
        accepted: dict[str, DeploymentControlEvidence] = {}
        seen_evidence: dict[str, str] = {}
        seen_controls: dict[str, str] = {}

        if getattr(self.verifier, "assurance", None) is not ComponentAssurance.DEPLOYMENT:
            findings.append("evidence verifier is not deployment-assured")
        if (
            getattr(self.approval_verifier, "assurance", None)
            is not ComponentAssurance.DEPLOYMENT
        ):
            findings.append("approval verifier is not deployment-assured")
        if getattr(self.issuer, "assurance", None) is not ComponentAssurance.DEPLOYMENT:
            findings.append("decision issuer is not deployment-assured")
        if getattr(self.issuer, "authority_id", None) != self.profile.authority_id:
            findings.append("decision authority identity mismatch")
        approval_problems = self._approval_problems(approval, current_time)
        findings.extend(f"deployment approval: {item}" for item in approval_problems)
        approved_by = approval.approver_id if isinstance(approval, DeploymentApprovalEvidence) else ""
        gateway_valid = isinstance(gateway_readiness, GatewayReadiness)
        sandbox_valid = isinstance(sandbox_report, SandboxReadinessReport)
        if not gateway_valid:
            findings.append("gateway readiness result has an unknown type")
        elif (
            not gateway_readiness.ready
            or gateway_readiness.missing
            or gateway_readiness.reference_only
        ):
            findings.append("gateway execution plane is not deployment-ready")
        if not sandbox_valid:
            findings.append("sandbox readiness result has an unknown type")
        elif (
            not sandbox_report.ready_for_enforcement
            or sandbox_report.maximum_mode is not RailActivationMode.ENFORCED
            or sandbox_report.findings
        ):
            findings.append("sandbox rail evidence does not permit enforced mode")
        if sandbox_valid and sandbox_report.profile_digest != self.profile.sandbox_profile_digest:
            findings.append("sandbox readiness profile digest mismatch")

        expected_artifacts = {
            "execution_plane_ready": (
                self._gateway_digest(gateway_readiness) if gateway_valid else "invalid"
            ),
            "sandbox_enforced_ready": (
                canonical_hash(sandbox_report.to_dict()) if sandbox_valid else "invalid"
            ),
            "policy_parity_live": self.profile.policy_profile_digest,
        }
        for evidence in evidence_items:
            if not isinstance(evidence, DeploymentControlEvidence):
                findings.append("unknown deployment evidence type")
                continue
            try:
                digest = evidence.evidence_digest
            except (TypeError, ValueError, AttributeError):
                findings.append(f"{evidence.evidence_id or 'unknown-evidence'}: evidence is malformed")
                continue
            prior_evidence = seen_evidence.get(evidence.evidence_id)
            if prior_evidence is not None:
                if prior_evidence != digest:
                    findings.append(f"{evidence.evidence_id}: conflicting evidence identity")
                continue
            seen_evidence[evidence.evidence_id] = digest
            prior_control = seen_controls.get(evidence.control_id)
            if prior_control is not None:
                findings.append(f"{evidence.control_id}: duplicate control evidence")
                continue
            seen_controls[evidence.control_id] = digest
            problems = self._problems(evidence, current_time)
            expected_artifact = expected_artifacts.get(evidence.control_id)
            if expected_artifact is not None and evidence.artifact_digest != expected_artifact:
                problems += ("bound artifact digest mismatch",)
            if problems:
                findings.extend(f"{evidence.control_id or 'unknown-control'}: {item}" for item in problems)
                continue
            accepted[evidence.control_id] = evidence

        missing = self.profile.required_controls.difference(accepted)
        unexpected = set(accepted).difference(self.profile.required_controls)
        if missing:
            findings.append("required deployment controls are missing: " + ", ".join(sorted(missing)))
        if unexpected:
            findings.append("unexpected deployment controls supplied: " + ", ".join(sorted(unexpected)))
        assessors = tuple(sorted({item.assessor_id for item in accepted.values()}))
        if len(assessors) < self.profile.minimum_distinct_assessors:
            findings.append("independent assessor threshold not met")

        ready = not findings and set(accepted) == set(self.profile.required_controls)
        decision = DeploymentReadinessDecision(
            ready=ready,
            maximum_mode=RailActivationMode.ENFORCED if ready else RailActivationMode.DISABLED,
            profile_digest=self.profile.profile_digest,
            deployment_id=self.profile.deployment_id,
            environment_id=self.profile.environment_id,
            approved_by=approved_by,
            approval_digest=(
                approval.approval_digest
                if isinstance(approval, DeploymentApprovalEvidence)
                else ""
            ),
            authority_id=self.profile.authority_id,
            evidence_digests=tuple(sorted(item.evidence_digest for item in accepted.values())),
            assessor_ids=assessors,
            findings=tuple(findings),
            issued_at=current_time.isoformat(),
            expires_at=datetime.fromtimestamp(
                current_time.timestamp() + self.profile.decision_validity_seconds,
                tz=current_time.tzinfo,
            ).isoformat(),
        )
        try:
            proof = self.issuer.seal(decision)
        except Exception as exc:
            raise RuntimeError("deployment readiness decision could not be sealed") from exc
        if not isinstance(proof, str) or not proof:
            raise RuntimeError("deployment readiness issuer returned an empty proof")
        return replace(decision, proof=proof)

    def _approval_problems(self, approval: DeploymentApprovalEvidence,
                           current_time: datetime) -> tuple[str, ...]:
        if not isinstance(approval, DeploymentApprovalEvidence):
            return ("unknown approval evidence type",)
        required = (
            approval.approval_id, approval.deployment_id, approval.environment_id,
            approval.profile_digest, approval.approver_id, approval.approved_mode,
            approval.approved_at, approval.expires_at, approval.proof,
        )
        if not all(isinstance(value, str) and value for value in required):
            return ("required approval identity is missing",)
        problems: list[str] = []
        try:
            approved_at = datetime.fromisoformat(approval.approved_at)
            expires_at = datetime.fromisoformat(approval.expires_at)
        except (TypeError, ValueError):
            return ("approval timestamps are invalid",)
        if approved_at.tzinfo is None or expires_at.tzinfo is None:
            problems.append("approval timestamps need a timezone")
        elif not approved_at <= current_time < expires_at:
            problems.append("approval is not currently valid")
        checks = (
            (approval.deployment_id == self.profile.deployment_id,
             "deployment identity mismatch"),
            (approval.environment_id == self.profile.environment_id,
             "environment identity mismatch"),
            (approval.profile_digest == self.profile.profile_digest,
             "readiness profile digest mismatch"),
            (approval.approver_id in self.profile.authorized_approvers,
             "approver is not authorized"),
            (approval.approved_mode == RailActivationMode.ENFORCED.value,
             "approval does not authorize enforced mode"),
        )
        problems.extend(reason for accepted, reason in checks if not accepted)
        try:
            verified = self.approval_verifier.verify(approval) is True
        except Exception:
            verified = False
        if not verified:
            problems.append("approval proof is invalid or unavailable")
        return tuple(problems)

    def _problems(self, evidence: DeploymentControlEvidence,
                  current_time: datetime) -> tuple[str, ...]:
        problems: list[str] = []
        required = (
            evidence.evidence_id, evidence.control_id, evidence.deployment_id,
            evidence.environment_id, evidence.software_digest,
            evidence.configuration_digest, evidence.policy_profile_digest,
            evidence.sandbox_profile_digest, evidence.artifact_digest,
            evidence.assessor_id, evidence.observed_at, evidence.proof,
        )
        if not all(isinstance(value, str) and value for value in required):
            return ("required evidence identity is missing",)
        try:
            observed_at = datetime.fromisoformat(evidence.observed_at)
        except (TypeError, ValueError):
            return ("observation timestamp is invalid",)
        if observed_at.tzinfo is None:
            problems.append("observation timestamp needs a timezone")
        else:
            age = (current_time - observed_at).total_seconds()
            if not 0 <= age <= self.profile.max_evidence_age_seconds:
                problems.append("evidence is stale or from the future")
        checks = (
            (evidence.control_id in self.profile.required_controls, "control is not required"),
            (evidence.deployment_id == self.profile.deployment_id, "deployment identity mismatch"),
            (evidence.environment_id == self.profile.environment_id, "environment identity mismatch"),
            (evidence.software_digest == self.profile.software_digest, "software digest mismatch"),
            (
                evidence.configuration_digest == self.profile.configuration_digest,
                "configuration digest mismatch",
            ),
            (
                evidence.policy_profile_digest == self.profile.policy_profile_digest,
                "policy profile digest mismatch",
            ),
            (
                evidence.sandbox_profile_digest == self.profile.sandbox_profile_digest,
                "sandbox profile digest mismatch",
            ),
            (evidence.assessor_id in self.profile.trusted_assessors, "assessor is not trusted"),
            (type(evidence.passed) is bool and evidence.passed, "control did not explicitly pass"),
        )
        problems.extend(reason for accepted, reason in checks if not accepted)
        try:
            verified = self.verifier.verify(evidence) is True
        except Exception:
            verified = False
        if not verified:
            problems.append("evidence proof is invalid or unavailable")
        return tuple(problems)

    @staticmethod
    def _gateway_digest(readiness: GatewayReadiness) -> str:
        return canonical_hash({
            "ready": readiness.ready,
            "missing": list(readiness.missing),
            "reference_only": list(readiness.reference_only),
        })
