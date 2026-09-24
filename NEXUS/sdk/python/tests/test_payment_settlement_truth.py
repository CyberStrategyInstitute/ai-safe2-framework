"""Adversarial tests for Settlement Truth Authority."""

import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.broker import SignedAuthorization
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    Money,
    PaymentRail,
    SettlementFinality,
)
from nexus_sdk.payments.settlement_truth import (
    AuthoritativeSettlementObserver,
    RailSettlementEvidence,
    RetryDirective,
    SettlementObserverProfile,
    SettlementTruth,
)
from nexus_sdk.payments.sqlite_state import SQLiteGatewayStateStore

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
KEY = b"settlement-observer-test-key"


class HMACTestSettlementEvidenceVerifier:
    def seal(self, evidence):
        return hmac.new(KEY, evidence.evidence_digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, evidence):
        return hmac.compare_digest(self.seal(evidence), evidence.proof)


def canonical():
    return CanonicalTransaction(
        transaction_intent_id="intent-1",
        authority_grant_id="grant-1",
        delegation_chain_id="chain-1",
        principal_id="principal-1",
        policy_id="policy-1",
        runtime_measurement_id="runtime-1",
        revocation_epoch=0,
        canonical_digest="sha256:canonical-1",
        amount=Money(5_000, "USD"),
        merchant_id="merchant-1",
        destination="destination-1",
        rail=PaymentRail.STABLECOIN,
        idempotency_key="idem-1",
        decided_at=NOW.isoformat(),
        finality=SettlementFinality.IRREVERSIBLE,
    )


def authorization(transaction=None):
    transaction = transaction or canonical()
    return SignedAuthorization(
        transaction_intent_id=transaction.transaction_intent_id,
        signing_digest=transaction.signing_digest(),
        signature="signature-1",
        algorithm="TEST",
        key_id="key-1",
        signer_id="key-guardian-1",
        decision_id="decision-1",
        revocation_epoch=transaction.revocation_epoch,
        runtime_measurement_id=transaction.runtime_measurement_id,
        signed_at=NOW.isoformat(),
        authorization_id="authorization-1",
    )


def evidence(transaction=None, auth=None, *, status="settled", confirmations=12,
             settlement_id="settlement-1", observed_at=NOW):
    transaction = transaction or canonical()
    auth = auth or authorization(transaction)
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
        observed_at=observed_at.isoformat(),
        observer_id="settlement-observer-1",
        proof="",
    )
    verifier = HMACTestSettlementEvidenceVerifier()
    return replace(value, proof=verifier.seal(value))


def configured(tmp_path):
    return AuthoritativeSettlementObserver(
        profile=SettlementObserverProfile(
            observer_id="settlement-observer-1",
            observer_version="settlement-observer/1",
            evidence_trust_digest="sha256:settlement-trust-roots",
            minimum_confirmations=((PaymentRail.STABLECOIN, 12),),
            max_observation_age_seconds=300,
        ),
        evidence_verifier=HMACTestSettlementEvidenceVerifier(),
        replay_store=SQLiteGatewayStateStore(tmp_path / "settlement.db"),
        now=lambda: NOW,
    )


def test_authoritative_settlement_is_terminal_and_never_retried(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    result = configured(tmp_path).observe(transaction, auth, evidence(transaction, auth))
    assert result.truth is SettlementTruth.SETTLED
    assert result.retry is RetryDirective.NEVER
    assert result.settlement_id == "settlement-1"


def test_identical_observation_is_idempotent(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    proof = evidence(transaction, auth)
    observer = configured(tmp_path)
    assert observer.observe(transaction, auth, proof) == observer.observe(transaction, auth, proof)


def test_conflicting_terminal_claim_halts(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    observer = configured(tmp_path)
    observer.observe(transaction, auth, evidence(transaction, auth))
    failed = evidence(
        transaction, auth, status="failed", confirmations=0, settlement_id=None
    )
    with pytest.raises(ValueError, match="conflicting"):
        observer.observe(transaction, auth, failed)


def test_insufficient_finality_is_ambiguous_not_failed(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    result = configured(tmp_path).observe(
        transaction, auth, evidence(transaction, auth, confirmations=11)
    )
    assert result.truth is SettlementTruth.AMBIGUOUS
    assert result.retry is RetryDirective.RECONCILE


def test_ambiguous_observation_can_progress_to_settled(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    observer = configured(tmp_path)
    early = observer.observe(
        transaction, auth, evidence(transaction, auth, confirmations=11)
    )
    final = observer.observe(
        transaction, auth, evidence(transaction, auth, confirmations=12)
    )
    assert early.truth is SettlementTruth.AMBIGUOUS
    assert final.truth is SettlementTruth.SETTLED


def test_timeout_is_ambiguous_and_never_blindly_retried(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    result = configured(tmp_path).observe(
        transaction,
        auth,
        evidence(transaction, auth, status="unknown", confirmations=0, settlement_id=None),
    )
    assert result.truth is SettlementTruth.AMBIGUOUS
    assert result.retry is RetryDirective.RECONCILE


def test_authoritative_failure_requires_new_authorization(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    result = configured(tmp_path).observe(
        transaction,
        auth,
        evidence(transaction, auth, status="failed", confirmations=0, settlement_id=None),
    )
    assert result.truth is SettlementTruth.FAILED
    assert result.retry is RetryDirective.NEW_AUTHORIZATION_REQUIRED


@pytest.mark.parametrize("field,value", [
    ("amount_minor", 5_001),
    ("destination", "destination-attacker"),
    ("signing_digest", "sha256:other"),
    ("finality", SettlementFinality.REVERSIBLE),
])
def test_settlement_mutation_is_rejected(tmp_path, field, value):
    transaction = canonical()
    auth = authorization(transaction)
    forged = replace(evidence(transaction, auth), **{field: value}, proof="")
    forged = replace(forged, proof=HMACTestSettlementEvidenceVerifier().seal(forged))
    with pytest.raises(ValueError, match="authorization-bound"):
        configured(tmp_path).observe(transaction, auth, forged)


def test_stale_future_and_unauthenticated_observations_are_rejected(tmp_path):
    transaction = canonical()
    auth = authorization(transaction)
    values = (
        evidence(transaction, auth, observed_at=NOW - timedelta(seconds=301)),
        evidence(transaction, auth, observed_at=NOW + timedelta(seconds=1)),
        replace(evidence(transaction, auth), proof="forged"),
    )
    for index, value in enumerate(values):
        with pytest.raises(ValueError, match="authorization-bound"):
            configured(tmp_path / str(index)).observe(transaction, auth, value)
