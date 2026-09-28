"""Adversarial tests for Human Intent Authority."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.human_intent import (
    HumanApprovalEvidence,
    HumanIntentAuthorityProfile,
    InMemoryTestApprovalChallengeStore,
    InProcessHMACTestHumanApprovalVerifier,
    TrustedIntentAuthority,
    TrustedTransactionRendering,
)
from nexus_sdk.payments.key_guardian import InProcessHMACReceiptAuthenticator
from nexus_sdk.payments.objects import CanonicalTransaction, Money, PaymentRail

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)


def canonical(*, amount=5_000):
    return CanonicalTransaction(
        transaction_intent_id="intent-1",
        authority_grant_id="grant-1",
        delegation_chain_id="chain-1",
        principal_id="principal-1",
        policy_id="policy-1",
        runtime_measurement_id="runtime-1",
        revocation_epoch=0,
        canonical_digest="sha256:canonical-1",
        amount=Money(amount, "USD"),
        merchant_id="merchant-1",
        destination="destination-1",
        rail=PaymentRail.CARD_NETWORK,
        idempotency_key="idem-1",
        decided_at=NOW.isoformat(),
    )


def configured(transaction=None, *, approved_at=NOW):
    transaction = transaction or canonical()
    rendering = TrustedTransactionRendering.from_canonical(
        transaction, surface_id="trusted-surface-1"
    )
    verifier = InProcessHMACTestHumanApprovalVerifier()
    evidence = HumanApprovalEvidence(
        approver_id="owner@example.org",
        action="approve",
        canonical_digest=transaction.canonical_digest,
        signing_digest=transaction.signing_digest(),
        rendering_digest=rendering.rendering_digest,
        challenge="challenge-1",
        approved_at=approved_at.isoformat(),
        evidence_verifier_id=verifier.verifier_id,
        proof="",
    )
    evidence = replace(evidence, proof=verifier.seal(evidence))
    receipt_issuer = InProcessHMACReceiptAuthenticator()
    authority = TrustedIntentAuthority(
        profile=HumanIntentAuthorityProfile(
            authority_id="human-intent-authority-1",
            authority_version="human-intent/1",
            trusted_surface_ids=frozenset({"trusted-surface-1"}),
            authorized_approvers=frozenset({"owner@example.org"}),
            evidence_trust_digest="sha256:human-trust-roots",
            max_approval_age_seconds=120,
        ),
        evidence_verifier=verifier,
        challenge_store=InMemoryTestApprovalChallengeStore({"challenge-1"}),
        receipt_issuer=receipt_issuer,
        now=lambda: NOW,
    )
    return authority, receipt_issuer, transaction, rendering, evidence


def test_exact_fresh_approval_issues_authenticated_receipt():
    authority, authenticator, transaction, rendering, evidence = configured()
    receipt = authority.authorize(transaction, rendering, evidence)
    assert authenticator.verify_human_intent(receipt)
    assert receipt.signing_digest == transaction.signing_digest()
    assert receipt.rendering_digest == rendering.rendering_digest
    assert receipt.authority_profile_digest == authority.profile.profile_digest


def test_approval_challenge_is_single_use():
    authority, _, transaction, rendering, evidence = configured()
    authority.authorize(transaction, rendering, evidence)
    with pytest.raises(ValueError, match="challenge"):
        authority.authorize(transaction, rendering, evidence)


def test_amount_mutation_invalidates_approval():
    authority, _, transaction, rendering, evidence = configured()
    with pytest.raises(ValueError, match="transaction-bound"):
        authority.authorize(canonical(amount=5_001), rendering, evidence)


def test_untrusted_surface_is_rejected():
    authority, _, transaction, rendering, evidence = configured()
    forged = replace(rendering, surface_id="agent-controlled-surface")
    with pytest.raises(ValueError, match="transaction-bound"):
        authority.authorize(transaction, forged, evidence)


def test_unlisted_approver_is_rejected_even_with_valid_proof():
    authority, _, transaction, rendering, evidence = configured()
    verifier = InProcessHMACTestHumanApprovalVerifier()
    forged = replace(evidence, approver_id="attacker@example.org", proof="")
    forged = replace(forged, proof=verifier.seal(forged))
    with pytest.raises(ValueError, match="transaction-bound"):
        authority.authorize(transaction, rendering, forged)


def test_denial_action_cannot_become_approval():
    authority, _, transaction, rendering, evidence = configured()
    verifier = InProcessHMACTestHumanApprovalVerifier()
    denied = replace(evidence, action="deny", proof="")
    denied = replace(denied, proof=verifier.seal(denied))
    with pytest.raises(ValueError, match="transaction-bound"):
        authority.authorize(transaction, rendering, denied)


def test_stale_and_future_approvals_are_rejected():
    for approved_at in (NOW - timedelta(seconds=121), NOW + timedelta(seconds=1)):
        authority, _, transaction, rendering, evidence = configured(approved_at=approved_at)
        with pytest.raises(ValueError, match="transaction-bound"):
            authority.authorize(transaction, rendering, evidence)


def test_rendering_mutation_invalidates_surface_proof():
    authority, _, transaction, rendering, evidence = configured()
    forged = replace(rendering, merchant_id="merchant-attacker")
    with pytest.raises(ValueError, match="transaction-bound"):
        authority.authorize(transaction, forged, evidence)
