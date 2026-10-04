"""Sovereign Payment Coordinator: fail-closed orchestration across trust boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from nexus_sdk.payments.broker import BrokerRefusal, SignedAuthorization
from nexus_sdk.payments.execution_plane import ComponentAssurance, ExecutionRecord, ExecutionState
from nexus_sdk.payments.key_guardian import (
    CredentialReleaseEnvelope,
    HumanIntentAuthorizationReceipt,
    KeyGuardianClient,
    RuntimeAuthorizationReceipt,
)
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    RuntimeMeasurement,
    TransactionIntent,
    canonical_hash,
    utcnow,
)
from nexus_sdk.payments.policy_authority import (
    DeterministicPolicyAuthority,
    PolicyAuthorityDecision,
)
from nexus_sdk.payments.runtime_verifier import IndependentRuntimeVerifier
from nexus_sdk.payments.settlement_truth import (
    AuthoritativeSettlementObserver,
    RailSettlementEvidence,
    SettlementObservation,
    SettlementTruth,
)

__all__ = [
    "CoordinatedPayment", "CoordinatorConflictError", "PaymentRailSubmitter",
    "PreparedPayment", "RailSubmissionReceipt", "RailSubmissionUncertainError",
    "SovereignPaymentCoordinator",
]


class CoordinatorConflictError(RuntimeError):
    """Durable state changed or supplied evidence cannot reproduce it exactly."""


class RailSubmissionUncertainError(RuntimeError):
    """The rail may have accepted the request; reconciliation is mandatory."""


@dataclass(frozen=True)
class RailSubmissionReceipt:
    execution_id: str
    authorization_id: str
    signing_digest: str
    idempotency_key: str
    submission_id: str
    submitted_at: str
    accepted: bool
    reason: str = ""


class PaymentRailSubmitter(Protocol):
    """Idempotent rail boundary; retries return the original submission result."""

    assurance: ComponentAssurance

    def submit_or_retrieve(self, canonical: CanonicalTransaction,
                           authorization: SignedAuthorization, *,
                           execution_id: str,
                           idempotency_key: str) -> RailSubmissionReceipt: ...


class CoordinatorStateStore(Protocol):
    assurance: ComponentAssurance

    def create(self, record: ExecutionRecord) -> None: ...
    def get(self, execution_id: str) -> ExecutionRecord | None: ...
    def compare_and_swap(self, *, expected: ExecutionRecord, updated: ExecutionRecord) -> bool: ...
    def current_revocation_epoch(self, principal_id: str) -> int: ...
    def reserve_execution(self, record: ExecutionRecord, *, amount_minor: int,
                          currency: str,
                          ceilings_minor: Mapping[str, int]) -> ExecutionRecord: ...
    def settle_execution(self, *, expected: ExecutionRecord,
                         updated: ExecutionRecord) -> bool: ...
    def release_execution(self, *, expected: ExecutionRecord,
                          updated: ExecutionRecord, reason: str) -> bool: ...


@dataclass(frozen=True)
class PreparedPayment:
    execution: ExecutionRecord
    canonical: CanonicalTransaction
    policy: PolicyAuthorityDecision
    runtime: RuntimeAuthorizationReceipt
    authorization: SignedAuthorization


@dataclass(frozen=True)
class CoordinatedPayment:
    execution: ExecutionRecord
    canonical: CanonicalTransaction
    authorization: SignedAuthorization
    submission: RailSubmissionReceipt | None = None
    settlement: SettlementObservation | None = None


class SovereignPaymentCoordinator:
    """Compose deterministic controls without collapsing their trust boundaries."""

    human_name = "Sovereign Payment Coordinator"
    technical_name = "SovereignPaymentCoordinator"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, policy: DeterministicPolicyAuthority,
                 runtime: IndependentRuntimeVerifier,
                 guardian: KeyGuardianClient,
                 rail: PaymentRailSubmitter,
                 settlement: AuthoritativeSettlementObserver,
                 state: CoordinatorStateStore) -> None:
        self.policy = policy
        self.runtime = runtime
        self.guardian = guardian
        self.rail = rail
        self.settlement = settlement
        self.state = state

    def prepare(self, intent: TransactionIntent, measurement: RuntimeMeasurement, *,
                expected_runtime_baseline: str,
                ceilings_minor: Mapping[str, int],
                human_intent: HumanIntentAuthorizationReceipt | None = None,
                now: datetime | None = None) -> PreparedPayment:
        """Authorize, reserve exposure, and obtain one canonical authorization."""
        evaluated_at = now or utcnow()
        decision = self.policy.evaluate(
            intent, runtime=measurement,
            expected_runtime_baseline=expected_runtime_baseline,
            now=evaluated_at,
        )
        if not decision.authorized or decision.canonical is None or decision.receipt is None:
            raise CoordinatorConflictError(
                "policy did not authorize payment: " + ",".join(decision.verdict.codes)
            )
        canonical = decision.canonical
        execution = ExecutionRecord(
            execution_id="exec_" + canonical_hash({
                "intent": canonical.transaction_intent_id,
                "idempotency_key": canonical.idempotency_key,
                "signing_digest": canonical.signing_digest(),
            })[:24],
            transaction_intent_id=canonical.transaction_intent_id,
            canonical_digest=canonical.canonical_digest,
            idempotency_key=canonical.idempotency_key,
            authority_grant_id=canonical.authority_grant_id,
            revocation_epoch=canonical.revocation_epoch,
        )
        self.state.create(execution)
        runtime = self.runtime.verify(
            canonical, measurement,
            expected_baseline=expected_runtime_baseline,
            now=evaluated_at,
        )
        if not runtime.authorized or runtime.receipt is None:
            failed = execution.transition(ExecutionState.FAILED)
            self._cas(execution, failed)
            raise CoordinatorConflictError("independent runtime verification refused authorization")
        accepted = execution.transition(
            ExecutionState.POLICY_ACCEPTED,
            evidence_refs=(decision.receipt.decision_id, measurement.runtime_measurement_id),
        )
        self._cas(execution, accepted)
        reserved = self.state.reserve_execution(
            accepted,
            amount_minor=canonical.amount.minor_units,
            currency=canonical.amount.currency,
            ceilings_minor=ceilings_minor,
        )
        envelope = CredentialReleaseEnvelope(
            execution=reserved,
            canonical=canonical,
            policy=decision.receipt,
            runtime=runtime.receipt,
            human_intent=human_intent,
            observed_revocation_epoch=self.state.current_revocation_epoch(canonical.principal_id),
        )
        try:
            authorization = self.guardian.release(envelope)
        except BrokerRefusal as exc:
            failed = reserved.transition(ExecutionState.FAILED)
            if not self.state.release_execution(expected=reserved, updated=failed, reason=str(exc)):
                raise CoordinatorConflictError(
                    "credential refusal raced with another state change"
                ) from exc
            raise
        released = reserved.transition(
            ExecutionState.CREDENTIAL_RELEASED,
            authorization_id=authorization.authorization_id,
            evidence_refs=reserved.evidence_refs + (authorization.authorization_id,),
        )
        self._cas(reserved, released)
        return PreparedPayment(released, canonical, decision, runtime.receipt, authorization)

    def submit(self, prepared: PreparedPayment) -> CoordinatedPayment:
        """Submit or retrieve by a stable idempotency key; never blindly resubmit."""
        current = self._require_current(prepared.execution)
        try:
            receipt = self.rail.submit_or_retrieve(
                prepared.canonical,
                prepared.authorization,
                execution_id=current.execution_id,
                idempotency_key=current.idempotency_key,
            )
        except RailSubmissionUncertainError:
            ambiguous = current.transition(ExecutionState.AMBIGUOUS)
            self._cas(current, ambiguous)
            return CoordinatedPayment(ambiguous, prepared.canonical, prepared.authorization)
        self._verify_submission(current, prepared, receipt)
        if not receipt.accepted:
            failed = current.transition(
                ExecutionState.FAILED,
                evidence_refs=current.evidence_refs + (receipt.submission_id,),
            )
            if not self.state.release_execution(
                expected=current, updated=failed,
                reason=receipt.reason or "authoritative rail rejection",
            ):
                raise CoordinatorConflictError("rail rejection raced with another state change")
            return CoordinatedPayment(failed, prepared.canonical, prepared.authorization, receipt)
        submitted = current.transition(
            ExecutionState.SUBMITTED,
            evidence_refs=current.evidence_refs + (receipt.submission_id,),
        )
        self._cas(current, submitted)
        return CoordinatedPayment(submitted, prepared.canonical, prepared.authorization, receipt)

    def record_settlement(self, payment: CoordinatedPayment,
                          evidence: RailSettlementEvidence) -> CoordinatedPayment:
        """Apply authoritative truth and atomically commit or release exposure."""
        current = self._require_current(payment.execution)
        if current.state is ExecutionState.AMBIGUOUS:
            reconciling = current.transition(ExecutionState.RECONCILING)
            self._cas(current, reconciling)
            current = reconciling
        if current.state not in {ExecutionState.SUBMITTED, ExecutionState.RECONCILING}:
            raise CoordinatorConflictError("settlement evidence is not valid in the current state")
        observation = self.settlement.observe(payment.canonical, payment.authorization, evidence)
        refs = current.evidence_refs + (observation.evidence_digest,)
        if observation.truth is SettlementTruth.AMBIGUOUS:
            if current.state is ExecutionState.RECONCILING:
                return CoordinatedPayment(current, payment.canonical, payment.authorization,
                                          payment.submission, observation)
            updated = current.transition(ExecutionState.AMBIGUOUS, evidence_refs=refs)
            self._cas(current, updated)
        elif observation.truth is SettlementTruth.SETTLED:
            updated = current.transition(
                ExecutionState.SETTLED,
                settlement_id=observation.settlement_id,
                evidence_refs=refs,
            )
            if not self.state.settle_execution(expected=current, updated=updated):
                raise CoordinatorConflictError("settlement raced with another state change")
        else:
            target = (
                ExecutionState.RELEASED
                if current.state is ExecutionState.RECONCILING
                else ExecutionState.FAILED
            )
            updated = current.transition(target, evidence_refs=refs)
            if not self.state.release_execution(
                expected=current, updated=updated, reason=observation.reason
            ):
                raise CoordinatorConflictError("failure release raced with another state change")
        return CoordinatedPayment(updated, payment.canonical, payment.authorization,
                                  payment.submission, observation)

    def _cas(self, expected: ExecutionRecord, updated: ExecutionRecord) -> None:
        if not self.state.compare_and_swap(expected=expected, updated=updated):
            raise CoordinatorConflictError("execution changed concurrently")

    def _require_current(self, expected: ExecutionRecord) -> ExecutionRecord:
        current = self.state.get(expected.execution_id)
        if current != expected:
            raise CoordinatorConflictError("supplied execution is stale or cannot be reproduced")
        return current

    @staticmethod
    def _verify_submission(execution: ExecutionRecord, prepared: PreparedPayment,
                           receipt: RailSubmissionReceipt) -> None:
        if not receipt.submission_id or not receipt.submitted_at or not all((
            receipt.execution_id == execution.execution_id,
            receipt.authorization_id == prepared.authorization.authorization_id,
            receipt.signing_digest == prepared.canonical.signing_digest(),
            receipt.idempotency_key == execution.idempotency_key,
        )):
            raise CoordinatorConflictError("rail receipt is incomplete or not authorization-bound")
