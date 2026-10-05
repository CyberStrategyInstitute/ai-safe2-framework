"""Security tests for deterministic Policy Authority receipts."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from nexus_sdk.payments.authority import AuthorityGraph, RevocationPlane
from nexus_sdk.payments.firewall import CounterpartyRegistry, TransactionFirewall
from nexus_sdk.payments.key_guardian import InProcessHMACReceiptAuthenticator
from nexus_sdk.payments.objects import (
    AssuranceLevel,
    AuthorityConstraints,
    AuthorityGrant,
    Money,
    PaymentDecision,
    PaymentRail,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
)
from nexus_sdk.payments.policy_authority import (
    DeterministicPolicyAuthority,
    PolicyDefinition,
)

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)


def configured():
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
    registry.register_merchant(
        "merchant-1", "sha256:merchant-1", destinations={"destination-1"}
    )
    firewall = TransactionFirewall(graph, counterparties=registry, policy_id="policy-1")
    authenticator = InProcessHMACReceiptAuthenticator()
    authority = DeterministicPolicyAuthority(
        firewall=firewall,
        definition=PolicyDefinition(
            policy_id="policy-1",
            ruleset_version="nexus-apay/0.4",
            configuration_digest="sha256:configuration-1",
            evaluator_id="policy-authority-1",
        ),
        receipt_issuer=authenticator,
    )
    intent = TransactionIntent(
        authority_grant_id=grant.authority_grant_id,
        amount=Money(5_000, "USD"),
        merchant_id="merchant-1",
        merchant_verified=True,
        merchant_baseline_digest="sha256:merchant-1",
        destination="destination-1",
        rail=PaymentRail.CARD_NETWORK,
        finality=SettlementFinality.REVERSIBLE,
        path_assurance=AssuranceLevel.RUNTIME_BOUND,
        nonce="nonce-1",
    )
    intent.approved_cart_digest = intent.canonical_digest()
    runtime = RuntimeMeasurement(
        runtime_measurement_id="runtime-1",
        attested=True,
        attestation_method="tdx",
        measured_at=NOW.isoformat(),
    )
    return authority, authenticator, intent, runtime


def test_allow_issues_authenticated_exactly_bound_receipt():
    authority, authenticator, intent, runtime = configured()
    result = authority.evaluate(intent, runtime=runtime, now=NOW)
    assert result.authorized
    assert result.receipt is not None
    assert result.canonical is not None
    assert authenticator.verify_policy(result.receipt)
    assert result.receipt.signing_digest == result.canonical.signing_digest()
    assert result.receipt.policy_digest == authority.definition.policy_digest


def test_same_inputs_and_policy_snapshot_produce_same_decision_id():
    authority, _, intent, runtime = configured()
    first = authority.evaluate(intent, runtime=runtime, now=NOW)
    second = authority.evaluate(intent, runtime=runtime, now=NOW)
    assert first.verdict.decision_id == second.verdict.decision_id


def test_denial_never_contains_signing_authority():
    authority, _, intent, runtime = configured()
    intent.amount = Money(10_001, "USD")
    intent.approved_cart_digest = intent.canonical_digest()
    result = authority.evaluate(intent, runtime=runtime, now=NOW)
    assert result.verdict.decision is PaymentDecision.DENY
    assert result.canonical is None
    assert result.receipt is None
    assert not result.authorized


def test_missing_runtime_never_contains_signing_authority():
    authority, _, intent, _ = configured()
    result = authority.evaluate(intent, runtime=None, now=NOW)
    assert result.verdict.decision is PaymentDecision.DENY
    assert result.receipt is None


def test_policy_configuration_change_changes_snapshot_digest():
    authority, _, _, _ = configured()
    changed = replace(
        authority.definition, configuration_digest="sha256:configuration-2"
    )
    assert changed.policy_digest != authority.definition.policy_digest


def test_human_approval_rule_changes_policy_snapshot_digest():
    authority, _, _, _ = configured()
    changed = replace(authority.definition, human_approval_consequences=frozenset())
    assert changed.policy_digest != authority.definition.policy_digest


def test_tampered_policy_snapshot_invalidates_receipt():
    authority, authenticator, intent, runtime = configured()
    result = authority.evaluate(intent, runtime=runtime, now=NOW)
    assert result.receipt is not None
    forged = replace(result.receipt, policy_digest="sha256:forged")
    assert not authenticator.verify_policy(forged)


def test_policy_identifier_mismatch_is_rejected_at_startup():
    authority, authenticator, _, _ = configured()
    with pytest.raises(ValueError, match="identifiers"):
        DeterministicPolicyAuthority(
            firewall=authority.firewall,
            definition=replace(authority.definition, policy_id="other-policy"),
            receipt_issuer=authenticator,
        )
