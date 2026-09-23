"""Adversarial tests for the independent Runtime Verifier boundary."""

import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from nexus_sdk.payments.attestation import HMACTestAttestationVerifier
from nexus_sdk.payments.key_guardian import InProcessHMACReceiptAuthenticator
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    Money,
    PaymentRail,
    RuntimeMeasurement,
)
from nexus_sdk.payments.runtime_verifier import (
    IndependentRuntimeVerifier,
    RuntimeVerifierProfile,
)

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
KEY = b"runtime-attestation-test-key"


def canonical() -> CanonicalTransaction:
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
        rail=PaymentRail.CARD_NETWORK,
        idempotency_key="idem-1",
        decided_at=NOW.isoformat(),
    )


def measurement(*, measured_at=NOW, method="tdx", runtime_id="runtime-1"):
    value = RuntimeMeasurement(
        runtime_measurement_id=runtime_id,
        workload_id="spiffe://nexus.local/agent/buyer",
        attested=True,
        attestation_method=method,
        artifact_digest="sha256:agent-image-1",
        model_id="model-1",
        policy_id="policy-1",
        measured_at=measured_at.isoformat(),
        max_age_seconds=120,
        verifier_challenge="challenge-1",
        attestation_signer="test-root-1",
    )
    evidence = hmac.new(
        KEY, HMACTestAttestationVerifier.message(value), hashlib.sha256
    ).hexdigest()
    return replace(value, attestation_evidence=evidence)


def configured(value=None):
    value = value or measurement()
    evidence_verifier = HMACTestAttestationVerifier(
        {"test-root-1": KEY}, {"challenge-1"}
    )
    authenticator = InProcessHMACReceiptAuthenticator()
    verifier = IndependentRuntimeVerifier(
        verifier=evidence_verifier,
        profile=RuntimeVerifierProfile(
            verifier_id="runtime-verifier-1",
            verifier_version="runtime-verifier/1",
            trust_roots_digest="sha256:test-trust-roots",
            accepted_methods=frozenset({"tdx"}),
            allowed_workload_ids=frozenset({"spiffe://nexus.local/agent/buyer"}),
            max_measurement_age_seconds=120,
        ),
        receipt_issuer=authenticator,
    )
    return verifier, authenticator, value


def test_valid_evidence_issues_authenticated_bound_receipt():
    verifier, authenticator, value = configured()
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert result.authorized
    assert result.receipt is not None
    assert authenticator.verify_runtime(result.receipt)
    assert result.receipt.signing_digest == canonical().signing_digest()
    assert result.receipt.verifier_profile_digest == verifier.profile.profile_digest


def test_runtime_identity_mismatch_never_issues_receipt():
    verifier, _, value = configured(measurement(runtime_id="runtime-other"))
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized
    assert result.receipt is None


def test_stale_measurement_never_reaches_authorization():
    value = measurement(measured_at=NOW - timedelta(minutes=10))
    verifier, _, value = configured(value)
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized
    assert "stale" in result.result.reason


def test_future_measurement_is_not_fresh():
    value = measurement(measured_at=NOW + timedelta(seconds=1))
    verifier, _, value = configured(value)
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized


def test_unapproved_attestation_method_is_rejected():
    value = measurement(method="sev-snp")
    verifier, _, value = configured(value)
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized
    assert "not permitted" in result.result.reason


def test_unapproved_workload_identity_is_rejected():
    value = replace(
        measurement(),
        workload_id="spiffe://attacker.invalid/agent",
        attestation_evidence=None,
    )
    evidence = hmac.new(
        KEY, HMACTestAttestationVerifier.message(value), hashlib.sha256
    ).hexdigest()
    value = replace(value, attestation_evidence=evidence)
    verifier, _, value = configured(value)
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized
    assert "workload identity" in result.result.reason


def test_profile_freshness_ceiling_overrides_attacker_lifetime():
    value = replace(
        measurement(measured_at=NOW - timedelta(seconds=121)),
        max_age_seconds=86_400,
        attestation_evidence=None,
    )
    evidence = hmac.new(
        KEY, HMACTestAttestationVerifier.message(value), hashlib.sha256
    ).hexdigest()
    value = replace(value, attestation_evidence=evidence)
    verifier, _, value = configured(value)
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert not result.authorized


def test_baseline_substitution_is_rejected():
    verifier, _, value = configured()
    result = verifier.verify(
        canonical(), value, expected_baseline="sha256:other", now=NOW
    )
    assert not result.authorized
    assert "baseline" in result.result.reason


def test_challenge_is_single_use():
    verifier, _, value = configured()
    first = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    second = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert first.authorized
    assert not second.authorized
    assert second.receipt is None


def test_profile_digest_tampering_invalidates_receipt():
    verifier, authenticator, value = configured()
    result = verifier.verify(
        canonical(), value, expected_baseline=value.baseline_digest(), now=NOW
    )
    assert result.receipt is not None
    forged = replace(result.receipt, verifier_profile_digest="sha256:forged")
    assert not authenticator.verify_runtime(forged)
