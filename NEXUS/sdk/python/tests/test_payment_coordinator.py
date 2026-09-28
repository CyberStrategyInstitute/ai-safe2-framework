"""End-to-end security tests for the Sovereign Payment Coordinator."""

import hashlib
import hmac
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.attestation import HMACTestAttestationVerifier
from nexus_sdk.payments.authority import AuthorityGraph, RevocationPlane
from nexus_sdk.payments.coordinator import RailSubmissionReceipt, SovereignPaymentCoordinator
from nexus_sdk.payments.execution_plane import ComponentAssurance, ExecutionState
from nexus_sdk.payments.firewall import CounterpartyRegistry, TransactionFirewall
from nexus_sdk.payments.key_guardian import (
    InProcessHMACReceiptAuthenticator,
    InProcessHMACTestBackend,
    KeyGuardianClient,
    ReferenceKeyGuardianService,
)
from nexus_sdk.payments.objects import (
    AssuranceLevel,
    AuthorityConstraints,
    AuthorityGrant,
    Money,
    PaymentRail,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
)
from nexus_sdk.payments.policy_authority import DeterministicPolicyAuthority, PolicyDefinition
from nexus_sdk.payments.runtime_verifier import IndependentRuntimeVerifier, RuntimeVerifierProfile
from nexus_sdk.payments.settlement_truth import (
    AuthoritativeSettlementObserver,
    RailSettlementEvidence,
    SettlementObserverProfile,
)
from nexus_sdk.payments.sqlite_state import SQLiteGatewayStateStore

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
ATTESTATION_KEY = b"coordinator-attestation-key"
SETTLEMENT_KEY = b"coordinator-settlement-key"


class FakeRail:
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, accepted=True):
        self.accepted = accepted
        self.calls = []

    def submit_or_retrieve(self, canonical, authorization, *, execution_id, idempotency_key):
        self.calls.append(idempotency_key)
        return RailSubmissionReceipt(
            execution_id=execution_id,
            authorization_id=authorization.authorization_id,
            signing_digest=canonical.signing_digest(),
            idempotency_key=idempotency_key,
            submission_id="submission-1",
            submitted_at=NOW.isoformat(),
            accepted=self.accepted,
            reason="rail rejected" if not self.accepted else "",
        )


class SettlementVerifier:
    def seal(self, evidence):
        return hmac.new(
            SETTLEMENT_KEY, evidence.evidence_digest.encode(), hashlib.sha256
        ).hexdigest()

    def verify(self, evidence):
        return hmac.compare_digest(self.seal(evidence), evidence.proof)


def configured(tmp_path, *, rail_accepted=True):
    store = SQLiteGatewayStateStore(tmp_path / "coordinator.db")
    graph = AuthorityGraph(revocation=RevocationPlane())
    grant = graph.register_root(AuthorityGrant(
        principal_id="principal-1",
        constraints=AuthorityConstraints(
            max_transaction=Money(10_000, "USD"),
            currencies={"USD"},
            allowed_merchants={"merchant-1"},
            allowed_rails={PaymentRail.CARD_NETWORK},
            min_assurance=AssuranceLevel.RUNTIME_BOUND,
            max_finality=SettlementFinality.REVERSIBLE,
            not_after=(NOW + timedelta(days=1)).isoformat(),
        ),
        capabilities={"payment.execute"},
    ))
    registry = CounterpartyRegistry()
    registry.register_merchant("merchant-1", "sha256:merchant-1", destinations={"destination-1"})
    authenticator = InProcessHMACReceiptAuthenticator()
    policy = DeterministicPolicyAuthority(
        firewall=TransactionFirewall(graph, counterparties=registry, policy_id="policy-1"),
        definition=PolicyDefinition(
            policy_id="policy-1", ruleset_version="coordinator/1",
            configuration_digest="sha256:policy-configuration",
            evaluator_id="policy-authority-1", human_approval_consequences=frozenset(),
        ),
        receipt_issuer=authenticator,
    )
    measurement = RuntimeMeasurement(
        runtime_measurement_id="runtime-1",
        workload_id="spiffe://nexus.local/agent/buyer",
        attested=True,
        attestation_method="tdx",
        artifact_digest="sha256:agent-image-1",
        model_id="model-1",
        policy_id="policy-1",
        measured_at=NOW.isoformat(),
        max_age_seconds=120,
        verifier_challenge="challenge-1",
        attestation_signer="test-root-1",
    )
    measurement = replace(
        measurement,
        attestation_evidence=hmac.new(
            ATTESTATION_KEY,
            HMACTestAttestationVerifier.message(measurement),
            hashlib.sha256,
        ).hexdigest(),
    )
    runtime = IndependentRuntimeVerifier(
        verifier=HMACTestAttestationVerifier(
            {"test-root-1": ATTESTATION_KEY}, {"challenge-1"}
        ),
        profile=RuntimeVerifierProfile(
            verifier_id="runtime-verifier-1", verifier_version="runtime/1",
            trust_roots_digest="sha256:runtime-trust",
            accepted_methods=frozenset({"tdx"}),
            allowed_workload_ids=frozenset({"spiffe://nexus.local/agent/buyer"}),
        ),
        receipt_issuer=authenticator,
    )
    guardian = ReferenceKeyGuardianService(
        backend=InProcessHMACTestBackend(),
        state_store=store,
        receipt_authenticator=authenticator,
        trusted_policy_digests={"policy-1": policy.definition.policy_digest},
        trusted_runtime_verifier_digests={
            "runtime-verifier-1": runtime.profile.profile_digest
        },
        trusted_human_authority_digests={},
        revocation_epoch=store.current_revocation_epoch,
        now=lambda: NOW,
    )
    settlement = AuthoritativeSettlementObserver(
        profile=SettlementObserverProfile(
            observer_id="settlement-observer-1", observer_version="settlement/1",
            evidence_trust_digest="sha256:settlement-trust",
            minimum_confirmations=((PaymentRail.CARD_NETWORK, 0),),
        ),
        evidence_verifier=SettlementVerifier(), replay_store=store, now=lambda: NOW,
    )
    rail = FakeRail(rail_accepted)
    coordinator = SovereignPaymentCoordinator(
        policy=policy, runtime=runtime, guardian=KeyGuardianClient(guardian),
        rail=rail, settlement=settlement, state=store,
    )
    intent = TransactionIntent(
        authority_grant_id=grant.authority_grant_id,
        amount=Money(5_000, "USD"), merchant_id="merchant-1", merchant_verified=True,
        merchant_baseline_digest="sha256:merchant-1", destination="destination-1",
        rail=PaymentRail.CARD_NETWORK, finality=SettlementFinality.REVERSIBLE,
        path_assurance=AssuranceLevel.RUNTIME_BOUND, nonce="nonce-1",
    )
    intent.approved_cart_digest = intent.canonical_digest()
    return coordinator, store, rail, intent, measurement


def settlement_evidence(payment, *, status="settled", settlement_id="settlement-1"):
    value = RailSettlementEvidence(
        authorization_id=payment.authorization.authorization_id,
        signing_digest=payment.authorization.signing_digest,
        rail=payment.canonical.rail,
        status=status,
        settlement_id=settlement_id,
        amount_minor=payment.canonical.amount.minor_units,
        currency=payment.canonical.amount.currency,
        destination=payment.canonical.destination,
        confirmations=0,
        finality=payment.canonical.finality,
        observed_at=NOW.isoformat(),
        observer_id="settlement-observer-1",
        proof="",
    )
    return replace(value, proof=SettlementVerifier().seal(value))


def prepare(coordinator, intent, measurement):
    return coordinator.prepare(
        intent, measurement,
        expected_runtime_baseline=measurement.baseline_digest(),
        ceilings_minor={intent.authority_grant_id: 10_000},
        now=NOW,
    )


def reservation_status(store, reservation_id):
    with sqlite3.connect(store.path) as connection:
        return connection.execute(
            "SELECT status FROM reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()[0]


def test_happy_path_commits_exposure_with_settlement(tmp_path):
    coordinator, store, rail, intent, measurement = configured(tmp_path)
    prepared = prepare(coordinator, intent, measurement)
    assert prepared.execution.state is ExecutionState.CREDENTIAL_RELEASED
    payment = coordinator.submit(prepared)
    assert payment.execution.state is ExecutionState.SUBMITTED
    settled = coordinator.record_settlement(payment, settlement_evidence(payment))
    assert settled.execution.state is ExecutionState.SETTLED
    assert reservation_status(store, settled.execution.reservation_id) == "committed"
    assert rail.calls == [intent.idempotency_key]


def test_authoritative_rail_rejection_atomically_releases_exposure(tmp_path):
    coordinator, store, _, intent, measurement = configured(tmp_path, rail_accepted=False)
    rejected = coordinator.submit(prepare(coordinator, intent, measurement))
    assert rejected.execution.state is ExecutionState.FAILED
    assert reservation_status(store, rejected.execution.reservation_id) == "released"


def test_failed_settlement_releases_exposure(tmp_path):
    coordinator, store, _, intent, measurement = configured(tmp_path)
    payment = coordinator.submit(prepare(coordinator, intent, measurement))
    failed = coordinator.record_settlement(
        payment, settlement_evidence(payment, status="failed", settlement_id=None)
    )
    assert failed.execution.state is ExecutionState.FAILED
    assert reservation_status(store, failed.execution.reservation_id) == "released"


def test_tampered_submission_receipt_never_advances_state(tmp_path):
    coordinator, store, rail, intent, measurement = configured(tmp_path)
    prepared = prepare(coordinator, intent, measurement)
    original = rail.submit_or_retrieve
    rail.submit_or_retrieve = lambda *args, **kwargs: replace(
        original(*args, **kwargs), authorization_id="attacker-authorization"
    )
    with pytest.raises(Exception, match="authorization-bound"):
        coordinator.submit(prepared)
    assert store.get(prepared.execution.execution_id).state is ExecutionState.CREDENTIAL_RELEASED


def test_guardian_retry_uses_stable_authorization_identity(tmp_path):
    coordinator, _, _, intent, measurement = configured(tmp_path)
    prepared = prepare(coordinator, intent, measurement)
    # The stable identity lets a durable guardian return the same authorization after a crash.
    assert prepared.authorization.authorization_id.startswith("auth_")
    assert len(prepared.authorization.authorization_id) == 29
