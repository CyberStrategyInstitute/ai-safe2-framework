"""Adversarial tests for the Key Guardian credential-release boundary."""

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from nexus_sdk.payments.broker import BrokerRefusal
from nexus_sdk.payments.execution_plane import ExecutionRecord, ExecutionState
from nexus_sdk.payments.key_guardian import (
    CredentialReleaseEnvelope,
    InProcessHMACReceiptAuthenticator,
    InProcessHMACTestBackend,
    KeyGuardianClient,
    NullKeyGuardianTransport,
    PolicyAuthorizationReceipt,
    ReferenceKeyGuardianService,
    RuntimeAuthorizationReceipt,
)
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    Money,
    PaymentDecision,
    PaymentRail,
    PaymentReasonCode,
)
from nexus_sdk.payments.sqlite_state import SQLiteGatewayStateStore


def canonical(*, amount: int = 5000, epoch: int = 0) -> CanonicalTransaction:
    return CanonicalTransaction(
        transaction_intent_id="intent-1",
        authority_grant_id="grant-1",
        delegation_chain_id="chain-1",
        principal_id="principal-1",
        policy_id="policy-1",
        runtime_measurement_id="runtime-1",
        revocation_epoch=epoch,
        canonical_digest="sha256:intent-1",
        amount=Money(amount, "USD"),
        merchant_id="merchant-1",
        destination="destination-1",
        rail=PaymentRail.CARD_NETWORK,
        idempotency_key="idem-1",
    )


def envelope(transaction: CanonicalTransaction | None = None,
             execution: ExecutionRecord | None = None) -> CredentialReleaseEnvelope:
    transaction = transaction or canonical()
    execution = execution or ExecutionRecord(
            execution_id="execution-1",
            transaction_intent_id=transaction.transaction_intent_id,
            canonical_digest=transaction.canonical_digest,
            idempotency_key=transaction.idempotency_key,
            authority_grant_id=transaction.authority_grant_id,
            revocation_epoch=transaction.revocation_epoch,
        ).transition(ExecutionState.POLICY_ACCEPTED).transition(
            ExecutionState.RESERVED, reservation_id="reservation-1"
        )
    signing_digest = transaction.signing_digest()
    authenticator = InProcessHMACReceiptAuthenticator()
    policy = PolicyAuthorizationReceipt(
        decision_id="decision-1",
        decision=PaymentDecision.ALLOW,
        canonical_digest=transaction.canonical_digest,
        signing_digest=signing_digest,
        policy_id=transaction.policy_id,
        evaluated_at="2026-09-23T00:00:00+00:00",
        authenticator_id=authenticator.authenticator_id,
        proof="",
        policy_digest="sha256:policy-definition-1",
    )
    policy = replace(policy, proof=authenticator.seal_policy(policy))
    runtime = RuntimeAuthorizationReceipt(
        runtime_measurement_id=transaction.runtime_measurement_id,
        canonical_digest=transaction.canonical_digest,
        signing_digest=signing_digest,
        verifier_id="attestation-verifier-1",
        accepted=True,
        verified_at="2026-09-23T00:00:01+00:00",
        authenticator_id=authenticator.authenticator_id,
        proof="",
    )
    runtime = replace(runtime, proof=authenticator.seal_runtime(runtime))
    return CredentialReleaseEnvelope(
        execution=execution,
        canonical=transaction,
        policy=policy,
        runtime=runtime,
        observed_revocation_epoch=transaction.revocation_epoch,
    )


def configured(tmp_path, transaction=None, backend=None):
    transaction = transaction or canonical()
    store = SQLiteGatewayStateStore(tmp_path / "guardian.db")
    initial = ExecutionRecord(
        execution_id="execution-1",
        transaction_intent_id=transaction.transaction_intent_id,
        canonical_digest=transaction.canonical_digest,
        idempotency_key=transaction.idempotency_key,
        authority_grant_id=transaction.authority_grant_id,
        revocation_epoch=transaction.revocation_epoch,
    )
    store.create(initial)
    accepted = initial.transition(ExecutionState.POLICY_ACCEPTED)
    assert store.compare_and_swap(expected=initial, updated=accepted)
    reservation_id = store.reserve(
        accepted,
        amount_minor=transaction.amount.minor_units,
        currency=transaction.amount.currency,
        ceilings_minor={"grant-1": transaction.amount.minor_units},
    )
    reserved = accepted.transition(ExecutionState.RESERVED, reservation_id=reservation_id)
    assert store.compare_and_swap(expected=accepted, updated=reserved)
    request = envelope(transaction, reserved)
    guardian = ReferenceKeyGuardianService(
        backend=backend or InProcessHMACTestBackend(),
        state_store=store,
        receipt_authenticator=InProcessHMACReceiptAuthenticator(),
        trusted_policy_digests={"policy-1": "sha256:policy-definition-1"},
        revocation_epoch=store.current_revocation_epoch,
        now=lambda: datetime(2026, 9, 23, 0, 0, 30, tzinfo=timezone.utc),
    )
    return request, guardian


def test_guardian_signs_only_fully_bound_reserved_execution(tmp_path):
    backend = InProcessHMACTestBackend()
    request, guardian = configured(tmp_path, backend=backend)
    authorization = guardian.release(request)
    assert backend.verify(authorization)
    assert authorization.transaction_intent_id == "intent-1"
    assert authorization.decision_id == "decision-1"


def test_default_client_refuses_without_isolated_transport():
    client = KeyGuardianClient(NullKeyGuardianTransport())
    with pytest.raises(BrokerRefusal) as refusal:
        client.release(envelope())
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT


def test_policy_denial_never_reaches_signer(tmp_path):
    request, guardian = configured(tmp_path)
    request = replace(
        request,
        policy=replace(request.policy, decision=PaymentDecision.DENY),
    )
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(request)
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT


def test_unverified_runtime_never_reaches_signer(tmp_path):
    request, guardian = configured(tmp_path)
    request = replace(request, runtime=replace(request.runtime, accepted=False))
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(request)
    assert refusal.value.code is PaymentReasonCode.ATTESTATION_VERIFICATION_FAILED


def test_amount_mutation_breaks_policy_and_runtime_binding(tmp_path):
    approved, guardian = configured(tmp_path)
    changed = canonical(amount=5001)
    attacked = replace(approved, canonical=changed)
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(attacked)
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT


def test_stale_or_unreproducible_revocation_epoch_refuses(tmp_path):
    request, guardian = configured(tmp_path)
    guardian.revocation_epoch = lambda _: 1
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(request)
    assert refusal.value.code is PaymentReasonCode.STALE_REVOCATION_EPOCH


def test_release_requires_durable_reservation(tmp_path):
    request, guardian = configured(tmp_path)
    unreserved = ExecutionRecord(
        execution_id="execution-1",
        transaction_intent_id="intent-1",
        canonical_digest="sha256:intent-1",
        idempotency_key="idem-1",
        authority_grant_id="grant-1",
        revocation_epoch=0,
    ).transition(ExecutionState.POLICY_ACCEPTED)
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(replace(request, execution=unreserved))
    assert refusal.value.code is PaymentReasonCode.EXPOSURE_RESERVATION_FAILED


def test_second_release_is_rejected_before_signing(tmp_path):
    backend = InProcessHMACTestBackend()
    request, guardian = configured(tmp_path, backend=backend)
    guardian.release(request)
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(request)
    assert refusal.value.code is PaymentReasonCode.REPLAY_DETECTED


def test_forged_policy_receipt_is_rejected(tmp_path):
    request, guardian = configured(tmp_path)
    forged = replace(request, policy=replace(request.policy, decision_id="forged"))
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(forged)
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT


def test_unpersisted_reservation_copy_is_rejected(tmp_path):
    request, guardian = configured(tmp_path)
    forged_execution = replace(request.execution, reservation_id="reservation-forged")
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(replace(request, execution=forged_execution))
    assert refusal.value.code is PaymentReasonCode.EXPOSURE_RESERVATION_FAILED


def test_stale_receipt_is_rejected(tmp_path):
    request, guardian = configured(tmp_path)
    stale = replace(request, policy=replace(request.policy, evaluated_at="2026-09-22T00:00:00+00:00"))
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(stale)
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT


def test_released_reservation_cannot_sign(tmp_path):
    request, guardian = configured(tmp_path)
    getattr(guardian.state_store, "release")(
        request.execution.reservation_id, reason="user cancelled"
    )
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(request)
    assert refusal.value.code is PaymentReasonCode.EXPOSURE_RESERVATION_FAILED


def test_untrusted_policy_snapshot_cannot_sign(tmp_path):
    request, guardian = configured(tmp_path)
    forged = replace(request, policy=replace(request.policy, policy_digest="sha256:other"))
    with pytest.raises(BrokerRefusal) as refusal:
        guardian.release(forged)
    assert refusal.value.code is PaymentReasonCode.FAIL_CLOSED_DEFAULT
