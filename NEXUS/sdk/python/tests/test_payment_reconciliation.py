"""Adversarial tests for Governed Payment Recovery."""

import hashlib
import hmac
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.broker import SignedAuthorization
from nexus_sdk.payments.execution_plane import ExecutionRecord, ExecutionState
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    Money,
    PaymentRail,
    SettlementFinality,
)
from nexus_sdk.payments.reconciliation import (
    DeterministicReconciliationAuthority,
    ReconciliationConflictError,
    ReconciliationPolicy,
    ReconciliationStatus,
)
from nexus_sdk.payments.settlement_truth import (
    AuthoritativeSettlementObserver,
    RailSettlementEvidence,
    SettlementObserverProfile,
)
from nexus_sdk.payments.sqlite_state import SQLiteGatewayStateStore

NOW = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
KEY = b"reconciliation-settlement-key"


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        return self.value


class EvidenceVerifier:
    def seal(self, evidence):
        return hmac.new(KEY, evidence.evidence_digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, evidence):
        return hmac.compare_digest(self.seal(evidence), evidence.proof)


def canonical():
    return CanonicalTransaction(
        transaction_intent_id="intent-recovery-1",
        authority_grant_id="grant-1",
        delegation_chain_id="chain-1",
        principal_id="principal-1",
        policy_id="policy-1",
        runtime_measurement_id="runtime-1",
        revocation_epoch=0,
        canonical_digest="sha256:canonical-recovery-1",
        amount=Money(5_000, "USD"),
        merchant_id="merchant-1",
        destination="destination-1",
        rail=PaymentRail.STABLECOIN,
        idempotency_key="idem-recovery-1",
        decided_at=NOW.isoformat(),
        finality=SettlementFinality.IRREVERSIBLE,
    )


def authorization(transaction):
    return SignedAuthorization(
        transaction_intent_id=transaction.transaction_intent_id,
        signing_digest=transaction.signing_digest(),
        signature="signature-1",
        algorithm="TEST",
        key_id="key-1",
        signer_id="guardian-1",
        decision_id="decision-1",
        revocation_epoch=0,
        runtime_measurement_id="runtime-1",
        authorization_id="authorization-recovery-1",
        signed_at=NOW.isoformat(),
    )


def ambiguous_execution(store, transaction, auth):
    initial = ExecutionRecord(
        execution_id="execution-recovery-1",
        transaction_intent_id=transaction.transaction_intent_id,
        canonical_digest=transaction.canonical_digest,
        idempotency_key=transaction.idempotency_key,
        authority_grant_id=transaction.authority_grant_id,
        revocation_epoch=transaction.revocation_epoch,
    )
    store.create(initial)
    accepted = initial.transition(ExecutionState.POLICY_ACCEPTED)
    assert store.compare_and_swap(expected=initial, updated=accepted)
    reserved = store.reserve_execution(
        accepted, amount_minor=transaction.amount.minor_units,
        currency=transaction.amount.currency, ceilings_minor={"grant-1": 10_000},
    )
    released = reserved.transition(
        ExecutionState.CREDENTIAL_RELEASED, authorization_id=auth.authorization_id
    )
    assert store.compare_and_swap(expected=reserved, updated=released)
    submitted = released.transition(ExecutionState.SUBMITTED)
    assert store.compare_and_swap(expected=released, updated=submitted)
    ambiguous = submitted.transition(ExecutionState.AMBIGUOUS)
    assert store.compare_and_swap(expected=submitted, updated=ambiguous)
    return ambiguous


def configured(tmp_path, *, max_observations=2, deadline_seconds=90):
    clock = Clock()
    store = SQLiteGatewayStateStore(tmp_path / "reconciliation.db")
    transaction = canonical()
    auth = authorization(transaction)
    execution = ambiguous_execution(store, transaction, auth)
    observer = AuthoritativeSettlementObserver(
        profile=SettlementObserverProfile(
            observer_id="settlement-observer-1",
            observer_version="settlement/1",
            evidence_trust_digest="sha256:settlement-trust",
            minimum_confirmations=((PaymentRail.STABLECOIN, 12),),
        ),
        evidence_verifier=EvidenceVerifier(), replay_store=store, now=clock,
    )
    authority = DeterministicReconciliationAuthority(
        policy=ReconciliationPolicy(
            policy_id="recovery-policy-1",
            max_observations=max_observations,
            observation_interval_seconds=30,
            escalation_deadline_seconds=deadline_seconds,
        ),
        observer=observer, state=store, now=clock,
    )
    opened = authority.open(execution, transaction, auth)
    return authority, store, clock, transaction, auth, opened


def evidence(transaction, auth, *, status="unknown", confirmations=0,
             settlement_id=None):
    value = RailSettlementEvidence(
        authorization_id=auth.authorization_id,
        signing_digest=auth.signing_digest,
        rail=transaction.rail,
        status=status,
        settlement_id=settlement_id,
        amount_minor=transaction.amount.minor_units,
        currency=transaction.amount.currency,
        destination=transaction.destination,
        confirmations=confirmations,
        finality=transaction.finality,
        observed_at=NOW.isoformat(),
        observer_id="settlement-observer-1",
        proof="",
    )
    return replace(value, proof=EvidenceVerifier().seal(value))


def reservation_status(store, reservation_id):
    with sqlite3.connect(store.path) as connection:
        return connection.execute(
            "SELECT status FROM reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()[0]


def test_open_is_atomic_and_retains_exposure(tmp_path):
    _, store, _, _, _, opened = configured(tmp_path)
    assert opened.execution.state is ExecutionState.RECONCILING
    assert opened.case.status is ReconciliationStatus.OPEN
    assert store.get_reconciliation_case(opened.case.case_id) == opened.case
    assert reservation_status(store, opened.execution.reservation_id) == "reserved"


def test_authoritative_settlement_atomically_commits_and_closes(tmp_path):
    authority, store, _, transaction, auth, opened = configured(tmp_path)
    proof = evidence(
        transaction, auth, status="settled", confirmations=12,
        settlement_id="settlement-1",
    )
    result = authority.observe(
        opened.case, opened.execution, transaction, auth, proof
    )
    assert result.case.status is ReconciliationStatus.SETTLED
    assert result.execution.state is ExecutionState.SETTLED
    assert reservation_status(store, result.execution.reservation_id) == "committed"


def test_authoritative_failure_atomically_releases_and_closes(tmp_path):
    authority, store, _, transaction, auth, opened = configured(tmp_path)
    result = authority.observe(
        opened.case, opened.execution, transaction, auth,
        evidence(transaction, auth, status="failed"),
    )
    assert result.case.status is ReconciliationStatus.FAILED
    assert result.execution.state is ExecutionState.RELEASED
    assert reservation_status(store, result.execution.reservation_id) == "released"


def test_unknown_outcome_escalates_without_releasing_exposure(tmp_path):
    authority, store, clock, transaction, auth, opened = configured(tmp_path)
    first = authority.observe(
        opened.case, opened.execution, transaction, auth, evidence(transaction, auth)
    )
    assert first.case.status is ReconciliationStatus.OPEN
    clock.value += timedelta(seconds=30)
    escalated = authority.observe(
        first.case, first.execution, transaction, auth,
        evidence(transaction, auth, status="pending"),
    )
    assert escalated.case.status is ReconciliationStatus.ESCALATED
    assert escalated.execution.state is ExecutionState.ESCALATED
    assert reservation_status(store, escalated.execution.reservation_id) == "reserved"


def test_polling_before_governed_cadence_is_refused(tmp_path):
    authority, _, _, transaction, auth, opened = configured(tmp_path)
    first = authority.observe(
        opened.case, opened.execution, transaction, auth, evidence(transaction, auth)
    )
    new_evidence = evidence(transaction, auth, status="pending")
    with pytest.raises(ReconciliationConflictError, match="cadence"):
        authority.observe(
            first.case, first.execution, transaction, auth, new_evidence
        )


def test_identical_ambiguous_evidence_is_idempotent_not_attempt_exhaustion(tmp_path):
    authority, _, _, transaction, auth, opened = configured(tmp_path)
    proof = evidence(transaction, auth)
    first = authority.observe(
        opened.case, opened.execution, transaction, auth, proof
    )
    repeated = authority.observe(
        first.case, first.execution, transaction, auth, proof
    )
    assert repeated.case == first.case
    assert repeated.case.observation_count == 1
    assert repeated.case.status is ReconciliationStatus.OPEN


def test_deadline_escalates_but_does_not_restore_capacity(tmp_path):
    authority, store, clock, transaction, auth, opened = configured(
        tmp_path, max_observations=10, deadline_seconds=30
    )
    clock.value += timedelta(seconds=30)
    escalated = authority.observe(
        opened.case, opened.execution, transaction, auth, evidence(transaction, auth)
    )
    assert escalated.execution.state is ExecutionState.ESCALATED
    assert reservation_status(store, escalated.execution.reservation_id) == "reserved"


def test_overdue_case_escalates_without_fabricated_rail_evidence(tmp_path):
    authority, store, clock, transaction, auth, opened = configured(
        tmp_path, max_observations=10, deadline_seconds=30
    )
    clock.value += timedelta(seconds=30)
    escalated = authority.escalate_overdue(
        opened.case, opened.execution, transaction, auth
    )
    assert escalated.observation is None
    assert escalated.case.status is ReconciliationStatus.ESCALATED
    assert reservation_status(store, escalated.execution.reservation_id) == "reserved"


def test_case_cannot_escalate_before_deadline(tmp_path):
    authority, _, _, transaction, auth, opened = configured(tmp_path)
    with pytest.raises(ReconciliationConflictError, match="not elapsed"):
        authority.escalate_overdue(
            opened.case, opened.execution, transaction, auth
        )


def test_stale_worker_and_artifact_substitution_fail_closed(tmp_path):
    authority, _, clock, transaction, auth, opened = configured(tmp_path)
    first = authority.observe(
        opened.case, opened.execution, transaction, auth, evidence(transaction, auth)
    )
    clock.value += timedelta(seconds=30)
    with pytest.raises(ReconciliationConflictError, match="stale"):
        authority.observe(
            opened.case, opened.execution, transaction, auth, evidence(transaction, auth)
        )
    forged = replace(auth, authorization_id="attacker-authorization")
    with pytest.raises(ReconciliationConflictError, match="bound"):
        authority.observe(
            first.case, first.execution, transaction, forged,
            evidence(transaction, forged),
        )
