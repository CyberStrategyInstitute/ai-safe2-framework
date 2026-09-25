"""Governed Payment Recovery: deterministic reconciliation of uncertain payments."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

from nexus_sdk.payments.broker import SignedAuthorization
from nexus_sdk.payments.execution_plane import ComponentAssurance, ExecutionRecord, ExecutionState
from nexus_sdk.payments.objects import CanonicalTransaction, canonical_hash, utcnow
from nexus_sdk.payments.settlement_truth import (
    AuthoritativeSettlementObserver,
    RailSettlementEvidence,
    SettlementObservation,
    SettlementTruth,
)

__all__ = [
    "DeterministicReconciliationAuthority",
    "ReconciliationCase",
    "ReconciliationConflictError",
    "ReconciliationPolicy",
    "ReconciliationResult",
    "ReconciliationStatus",
]


class ReconciliationStatus(str, Enum):
    OPEN = "open"
    SETTLED = "settled"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class ReconciliationPolicy:
    """Pinned retry cadence and escalation bounds; none authorize resubmission."""

    policy_id: str
    max_observations: int = 12
    observation_interval_seconds: int = 30
    escalation_deadline_seconds: int = 900

    def __post_init__(self) -> None:
        if (
            not self.policy_id
            or self.max_observations < 1
            or self.observation_interval_seconds < 0
            or self.escalation_deadline_seconds < 1
        ):
            raise ValueError("valid reconciliation identity and positive bounds are required")

    @property
    def policy_digest(self) -> str:
        return canonical_hash(self.__dict__)


@dataclass(frozen=True)
class ReconciliationCase:
    case_id: str
    execution_id: str
    authorization_id: str
    signing_digest: str
    policy_digest: str
    opened_at: str
    deadline_at: str
    next_observation_at: str
    status: ReconciliationStatus = ReconciliationStatus.OPEN
    version: int = 0
    observation_count: int = 0
    evidence_refs: tuple[str, ...] = ()
    resolution_observation_digest: str | None = None


@dataclass(frozen=True)
class ReconciliationResult:
    case: ReconciliationCase
    execution: ExecutionRecord
    observation: SettlementObservation | None = None


class ReconciliationConflictError(RuntimeError):
    """Recovery state or evidence is stale, conflicting, or improperly bound."""


class ReconciliationStateStore(Protocol):
    assurance: ComponentAssurance

    def get(self, execution_id: str) -> ExecutionRecord | None: ...
    def get_reconciliation_case(self, case_id: str) -> ReconciliationCase | None: ...
    def open_reconciliation(self, *, expected: ExecutionRecord,
                            updated: ExecutionRecord,
                            case: ReconciliationCase) -> bool: ...
    def update_reconciliation_case(self, *, expected: ReconciliationCase,
                                   updated: ReconciliationCase) -> bool: ...
    def resolve_reconciliation(self, *, expected_execution: ExecutionRecord,
                               updated_execution: ExecutionRecord,
                               expected_case: ReconciliationCase,
                               updated_case: ReconciliationCase,
                               release_reason: str | None = None) -> bool: ...


class DeterministicReconciliationAuthority:
    """Drive ambiguous payments to authoritative truth or exposure-preserving escalation."""

    human_name = "Governed Payment Recovery"
    technical_name = "DeterministicReconciliationAuthority"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, policy: ReconciliationPolicy,
                 observer: AuthoritativeSettlementObserver,
                 state: ReconciliationStateStore,
                 now=utcnow) -> None:
        self.policy = policy
        self.observer = observer
        self.state = state
        self.now = now

    def open(self, execution: ExecutionRecord,
             canonical: CanonicalTransaction,
             authorization: SignedAuthorization) -> ReconciliationResult:
        """Atomically enter reconciliation while retaining reserved exposure."""
        current = self.state.get(execution.execution_id)
        if current != execution or execution.state is not ExecutionState.AMBIGUOUS:
            raise ReconciliationConflictError("only the current ambiguous execution may open")
        self._verify_bindings(execution, canonical, authorization)
        opened_at = self.now()
        if opened_at.tzinfo is None:
            raise ReconciliationConflictError("reconciliation clock must include a timezone")
        case = ReconciliationCase(
            case_id="rec_" + canonical_hash({
                "execution_id": execution.execution_id,
                "authorization_id": authorization.authorization_id,
                "policy_digest": self.policy.policy_digest,
            })[:24],
            execution_id=execution.execution_id,
            authorization_id=authorization.authorization_id,
            signing_digest=canonical.signing_digest(),
            policy_digest=self.policy.policy_digest,
            opened_at=opened_at.isoformat(),
            deadline_at=(
                opened_at + timedelta(seconds=self.policy.escalation_deadline_seconds)
            ).isoformat(),
            next_observation_at=opened_at.isoformat(),
        )
        updated = execution.transition(
            ExecutionState.RECONCILING,
            evidence_refs=execution.evidence_refs + (case.case_id,),
        )
        if not self.state.open_reconciliation(expected=execution, updated=updated, case=case):
            raise ReconciliationConflictError("reconciliation case raced with another worker")
        return ReconciliationResult(case, updated)

    def observe(self, case: ReconciliationCase,
                execution: ExecutionRecord,
                canonical: CanonicalTransaction,
                authorization: SignedAuthorization,
                evidence: RailSettlementEvidence) -> ReconciliationResult:
        """Record one authoritative observation; never submits or reauthorizes payment."""
        current_case = self.state.get_reconciliation_case(case.case_id)
        current_execution = self.state.get(execution.execution_id)
        if current_case != case or current_execution != execution:
            raise ReconciliationConflictError("reconciliation input is stale")
        if (
            case.status is not ReconciliationStatus.OPEN
            or execution.state is not ExecutionState.RECONCILING
        ):
            raise ReconciliationConflictError("reconciliation case is terminal")
        self._verify_bindings(execution, canonical, authorization)
        current_time = self.now()
        next_time = self._parse(case.next_observation_at)
        deadline = self._parse(case.deadline_at)
        if current_time.tzinfo is None:
            raise ReconciliationConflictError("reconciliation clock must include a timezone")
        observation = self.observer.observe(canonical, authorization, evidence)
        if observation.evidence_digest in case.evidence_refs:
            return ReconciliationResult(case, execution, observation)
        if current_time < next_time:
            raise ReconciliationConflictError("observation attempted before the governed cadence")
        count = case.observation_count + 1
        refs = case.evidence_refs + (observation.evidence_digest,)
        if observation.truth is SettlementTruth.SETTLED:
            updated_case = replace(
                case, status=ReconciliationStatus.SETTLED,
                version=case.version + 1, observation_count=count,
                evidence_refs=refs,
                resolution_observation_digest=observation.observation_digest,
            )
            updated_execution = execution.transition(
                ExecutionState.SETTLED,
                settlement_id=observation.settlement_id,
                evidence_refs=execution.evidence_refs + (observation.evidence_digest,),
            )
            self._resolve(execution, updated_execution, case, updated_case)
        elif observation.truth is SettlementTruth.FAILED:
            updated_case = replace(
                case, status=ReconciliationStatus.FAILED,
                version=case.version + 1, observation_count=count,
                evidence_refs=refs,
                resolution_observation_digest=observation.observation_digest,
            )
            updated_execution = execution.transition(
                ExecutionState.RELEASED,
                evidence_refs=execution.evidence_refs + (observation.evidence_digest,),
            )
            self._resolve(
                execution, updated_execution, case, updated_case,
                release_reason=observation.reason,
            )
        elif current_time >= deadline or count >= self.policy.max_observations:
            updated_case = replace(
                case, status=ReconciliationStatus.ESCALATED,
                version=case.version + 1, observation_count=count,
                evidence_refs=refs,
            )
            updated_execution = execution.transition(
                ExecutionState.ESCALATED,
                evidence_refs=execution.evidence_refs + (observation.evidence_digest,),
            )
            self._resolve(execution, updated_execution, case, updated_case)
        else:
            updated_case = replace(
                case, version=case.version + 1, observation_count=count,
                evidence_refs=refs,
                next_observation_at=(
                    current_time
                    + timedelta(seconds=self.policy.observation_interval_seconds)
                ).isoformat(),
            )
            if not self.state.update_reconciliation_case(
                expected=case, updated=updated_case
            ):
                raise ReconciliationConflictError("observation raced with another worker")
            updated_execution = execution
        return ReconciliationResult(updated_case, updated_execution, observation)

    def escalate_overdue(self, case: ReconciliationCase,
                         execution: ExecutionRecord,
                         canonical: CanonicalTransaction,
                         authorization: SignedAuthorization) -> ReconciliationResult:
        """Escalate an expired case without inventing settlement evidence."""
        current_case = self.state.get_reconciliation_case(case.case_id)
        current_execution = self.state.get(execution.execution_id)
        if current_case != case or current_execution != execution:
            raise ReconciliationConflictError("reconciliation input is stale")
        if (
            case.status is not ReconciliationStatus.OPEN
            or execution.state is not ExecutionState.RECONCILING
        ):
            raise ReconciliationConflictError("reconciliation case is terminal")
        self._verify_bindings(execution, canonical, authorization)
        current_time = self.now()
        if current_time.tzinfo is None:
            raise ReconciliationConflictError("reconciliation clock must include a timezone")
        if current_time < self._parse(case.deadline_at):
            raise ReconciliationConflictError("reconciliation deadline has not elapsed")
        updated_case = replace(
            case, status=ReconciliationStatus.ESCALATED, version=case.version + 1
        )
        updated_execution = execution.transition(ExecutionState.ESCALATED)
        self._resolve(execution, updated_execution, case, updated_case)
        return ReconciliationResult(updated_case, updated_execution)

    def _resolve(self, execution: ExecutionRecord, updated_execution: ExecutionRecord,
                 case: ReconciliationCase, updated_case: ReconciliationCase,
                 release_reason: str | None = None) -> None:
        if not self.state.resolve_reconciliation(
            expected_execution=execution,
            updated_execution=updated_execution,
            expected_case=case,
            updated_case=updated_case,
            release_reason=release_reason,
        ):
            raise ReconciliationConflictError("resolution raced with another worker")

    @staticmethod
    def _parse(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ReconciliationConflictError("reconciliation timestamp is invalid") from exc
        if parsed.tzinfo is None:
            raise ReconciliationConflictError("reconciliation timestamp needs a timezone")
        return parsed

    @staticmethod
    def _verify_bindings(execution: ExecutionRecord,
                         canonical: CanonicalTransaction,
                         authorization: SignedAuthorization) -> None:
        if not all((
            execution.transaction_intent_id == canonical.transaction_intent_id,
            execution.canonical_digest == canonical.canonical_digest,
            execution.idempotency_key == canonical.idempotency_key,
            execution.authority_grant_id == canonical.authority_grant_id,
            execution.revocation_epoch == canonical.revocation_epoch,
            execution.authorization_id == authorization.authorization_id,
            authorization.transaction_intent_id == canonical.transaction_intent_id,
            authorization.signing_digest == canonical.signing_digest(),
        )):
            raise ReconciliationConflictError("recovery artifacts are not exactly bound")
