"""Policy Parity Guard: fail-closed agreement with a deployed policy evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance
from nexus_sdk.payments.firewall import PaymentVerdict
from nexus_sdk.payments.objects import (
    ConsequenceClass,
    PaymentDecision,
    PaymentReasonCode,
    RuntimeMeasurement,
    TransactionIntent,
    canonical_hash,
    utcnow,
)
from nexus_sdk.payments.policy_authority import (
    DeterministicPolicyAuthority,
    PolicyAuthorityDecision,
)

__all__ = [
    "AuthenticatedPolicyEvaluator",
    "DeployedPolicyEvaluation",
    "ParityEnforcedPolicyAuthority",
    "ParityPolicyAuthorityDecision",
    "PolicyEvaluationAuthenticator",
    "PolicyInputProvider",
    "PolicyParityProfile",
    "PolicyParityReport",
]


@dataclass(frozen=True)
class DeployedPolicyEvaluation:
    """Authenticated result returned by the independently deployed evaluator."""

    decision: str
    reason_codes: tuple[str, ...]
    policy_id: str
    consequence: str
    evaluator_id: str
    policy_bundle_digest: str
    input_digest: str
    evaluated_at: str
    proof: str

    @property
    def evaluation_digest(self) -> str:
        values = dict(self.__dict__)
        values["reason_codes"] = list(self.reason_codes)
        values.pop("proof")
        return canonical_hash(values)


class AuthenticatedPolicyEvaluator(Protocol):
    """Out-of-process evaluator reached over an authenticated deployment channel."""

    assurance: ComponentAssurance

    def evaluate(self, input_document: dict[str, Any]) -> DeployedPolicyEvaluation: ...


class PolicyEvaluationAuthenticator(Protocol):
    """Verify response authenticity independently of the agent and transport."""

    assurance: ComponentAssurance

    def verify(self, evaluation: DeployedPolicyEvaluation) -> bool: ...


class PolicyInputProvider(Protocol):
    """Build the exact deployed-policy input from authoritative state."""

    def build(self, intent: TransactionIntent, *,
              runtime: RuntimeMeasurement | None,
              expected_runtime_baseline: str | None,
              hear_satisfied_by: str | None,
              now: datetime) -> dict[str, Any]: ...


@dataclass(frozen=True)
class PolicyParityProfile:
    evaluator_id: str
    policy_id: str
    policy_bundle_digest: str
    max_evaluation_age_seconds: int = 30

    def __post_init__(self) -> None:
        if (
            not self.evaluator_id
            or not self.policy_id
            or not self.policy_bundle_digest
            or self.max_evaluation_age_seconds < 1
        ):
            raise ValueError("complete policy parity profile and positive freshness are required")

    @property
    def profile_digest(self) -> str:
        return canonical_hash(self.__dict__)


@dataclass(frozen=True)
class PolicyParityReport:
    matched: bool
    reference_decision: str
    deployed_decision: str | None
    input_digest: str
    profile_digest: str
    reason: str
    deployed_evaluation_digest: str | None = None


@dataclass(frozen=True)
class ParityPolicyAuthorityDecision(PolicyAuthorityDecision):
    """Policy outcome carrying its immutable, transaction-scoped parity proof."""

    parity_report: PolicyParityReport | None = None


class ParityEnforcedPolicyAuthority:
    """Issue policy authority only when local and deployed deterministic rules agree."""

    human_name = "Policy Parity Guard"
    technical_name = "ParityEnforcedPolicyAuthority"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, authority: DeterministicPolicyAuthority,
                 input_provider: PolicyInputProvider,
                 evaluator: AuthenticatedPolicyEvaluator,
                 authenticator: PolicyEvaluationAuthenticator,
                 profile: PolicyParityProfile,
                 now=utcnow) -> None:
        if authority.definition.policy_id != profile.policy_id:
            raise ValueError("reference and deployed policy identifiers must match")
        if authority.definition.configuration_digest != profile.policy_bundle_digest:
            raise ValueError("policy definition must pin the deployed bundle digest")
        self.authority = authority
        self.input_provider = input_provider
        self.evaluator = evaluator
        self.authenticator = authenticator
        self.profile = profile
        self.now = now

    def evaluate(self, intent: TransactionIntent, *,
                 runtime: RuntimeMeasurement | None,
                 expected_runtime_baseline: str | None = None,
                 hear_satisfied_by: str | None = None,
                 now: datetime | None = None) -> ParityPolicyAuthorityDecision:
        evaluated_at = now or self.now()
        reference = self.authority.evaluate(
            intent,
            runtime=runtime,
            expected_runtime_baseline=expected_runtime_baseline,
            hear_satisfied_by=hear_satisfied_by,
            now=evaluated_at,
        )
        try:
            document = self.input_provider.build(
                intent,
                runtime=runtime,
                expected_runtime_baseline=expected_runtime_baseline,
                hear_satisfied_by=hear_satisfied_by,
                now=evaluated_at,
            )
        except Exception as exc:
            return self._refuse(
                reference, intent, "",
                PaymentReasonCode.POLICY_AUTHORITY_UNAVAILABLE,
                f"authoritative policy input unavailable: {type(exc).__name__}",
            )
        if not isinstance(document, dict):
            return self._refuse(
                reference, intent, "",
                PaymentReasonCode.POLICY_EVIDENCE_INVALID,
                "policy input provider returned a non-document value",
            )
        input_digest = canonical_hash(document)
        try:
            deployed = self.evaluator.evaluate(document)
        except Exception as exc:
            return self._refuse(
                reference, intent, input_digest,
                PaymentReasonCode.POLICY_AUTHORITY_UNAVAILABLE,
                f"deployed policy evaluator unavailable: {type(exc).__name__}",
            )
        if not isinstance(deployed, DeployedPolicyEvaluation):
            return self._refuse(
                reference, intent, input_digest,
                PaymentReasonCode.POLICY_EVIDENCE_INVALID,
                "deployed evaluator returned an unknown response type",
            )
        try:
            invalid = self._evidence_problem(deployed, input_digest, evaluated_at)
        except Exception as exc:
            invalid = f"deployed evaluation verification failed: {type(exc).__name__}"
        if invalid:
            return self._refuse(
                reference, intent, input_digest,
                PaymentReasonCode.POLICY_EVIDENCE_INVALID, invalid, deployed,
            )
        mismatch = self._parity_problem(reference.verdict, deployed)
        if mismatch:
            return self._refuse(
                reference, intent, input_digest,
                PaymentReasonCode.POLICY_DIVERGENCE, mismatch, deployed,
            )
        report = PolicyParityReport(
            matched=True,
            reference_decision=reference.verdict.decision.value,
            deployed_decision=deployed.decision,
            input_digest=input_digest,
            profile_digest=self.profile.profile_digest,
            reason="reference and deployed policy results match exactly",
            deployed_evaluation_digest=deployed.evaluation_digest,
        )
        return ParityPolicyAuthorityDecision(
            verdict=reference.verdict,
            policy_digest=reference.policy_digest,
            canonical=reference.canonical,
            receipt=reference.receipt,
            parity_report=report,
        )

    def _evidence_problem(self, deployed: DeployedPolicyEvaluation,
                          input_digest: str, evaluated_at: datetime) -> str | None:
        try:
            deployed_at = datetime.fromisoformat(deployed.evaluated_at)
        except (TypeError, ValueError):
            return "deployed evaluation timestamp is invalid"
        if deployed_at.tzinfo is None or evaluated_at.tzinfo is None:
            return "policy evaluation timestamps must include a timezone"
        age = (evaluated_at - deployed_at).total_seconds()
        if not all(isinstance(value, str) and value for value in (
            deployed.decision, deployed.policy_id, deployed.consequence,
            deployed.evaluator_id, deployed.policy_bundle_digest,
            deployed.input_digest, deployed.proof,
        )):
            return "deployed evaluation contains missing or invalid fields"
        if not isinstance(deployed.reason_codes, tuple) or not all(
            isinstance(code, str) and code for code in deployed.reason_codes
        ):
            return "deployed reason codes are malformed"
        checks = (
            (deployed.evaluator_id == self.profile.evaluator_id, "untrusted evaluator identity"),
            (deployed.policy_id == self.profile.policy_id, "policy identifier mismatch"),
            (
                deployed.policy_bundle_digest == self.profile.policy_bundle_digest,
                "policy bundle digest mismatch",
            ),
            (deployed.input_digest == input_digest, "policy input digest mismatch"),
            (
                0 <= age <= self.profile.max_evaluation_age_seconds,
                "deployed evaluation is stale or from the future",
            ),
            (
                len(deployed.reason_codes) == len(set(deployed.reason_codes)),
                "deployed reason codes contain duplicates",
            ),
        )
        problem = next((reason for accepted, reason in checks if not accepted), None)
        if problem:
            return problem
        if self.authenticator.verify(deployed) is not True:
            return "deployed evaluation proof is invalid"
        return None

    @staticmethod
    def _parity_problem(reference: PaymentVerdict,
                        deployed: DeployedPolicyEvaluation) -> str | None:
        expected = (
            reference.decision.value,
            tuple(sorted(reference.codes)),
            reference.policy_id,
            reference.consequence.value,
        )
        observed = (
            deployed.decision,
            tuple(sorted(deployed.reason_codes)),
            deployed.policy_id,
            deployed.consequence,
        )
        if expected != observed:
            return "decision, reason codes, policy identity, or consequence diverged"
        if deployed.decision not in {value.value for value in PaymentDecision}:
            return "deployed decision is unknown"
        if deployed.consequence not in {value.value for value in ConsequenceClass}:
            return "deployed consequence is unknown"
        return None

    def _refuse(self, reference: PolicyAuthorityDecision,
                intent: TransactionIntent, input_digest: str,
                code: PaymentReasonCode, reason: str,
                deployed: DeployedPolicyEvaluation | None = None
                ) -> ParityPolicyAuthorityDecision:
        report = PolicyParityReport(
            matched=False,
            reference_decision=reference.verdict.decision.value,
            deployed_decision=deployed.decision if deployed else None,
            input_digest=input_digest,
            profile_digest=self.profile.profile_digest,
            reason=reason,
            deployed_evaluation_digest=deployed.evaluation_digest if deployed else None,
        )
        verdict = PaymentVerdict(
            decision=PaymentDecision.DENY,
            transaction_intent_id=intent.transaction_intent_id,
            reason_codes=[code],
            reasoning=reason,
            policy_id=self.profile.policy_id,
            evaluated_at=reference.verdict.evaluated_at,
        )
        return ParityPolicyAuthorityDecision(
            verdict=verdict,
            policy_digest=reference.policy_digest,
            parity_report=report,
        )
