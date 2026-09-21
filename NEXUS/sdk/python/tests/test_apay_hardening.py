"""Adversarial tests for the v0.4 hardening pass (Steps 1-7)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nexus_sdk.payments import (
    AssuranceLevel, AttestationResult, AttestationVerifier, AuthorityConstraints,
    AuthorityGrant, AuthorityGraph, CounterpartyRegistry, DurableEvidenceLedger,
    InProcessTestBroker, Money, PaymentIntegrityGateway, PaymentRail,
    RevocationPlane, RuntimeMeasurement, SettlementFinality, SettlementResult,
    SettlementState, TransactionFirewall, TransactionIntent, UserControlPolicy,
    X402V2ExactEVMUSDCBinding,
)

NOW = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)


class AcceptFixtureProof(AttestationVerifier):
    def verify(self, measurement, *, expected_baseline, now=None):
        return AttestationResult(True, "fixture", type(self).__name__)


def system(maximum="100.00", *, user_controls=None, ledger=None):
    graph = AuthorityGraph(RevocationPlane())
    grant = graph.register_root(AuthorityGrant(
        principal_id="p", agent_did="did:a", capabilities={"payment.execute"},
        constraints=AuthorityConstraints(
            max_transaction=Money.parse(maximum), max_aggregate=Money.parse(maximum),
            currencies={"USD"}, allowed_merchants={"m"}, allowed_categories={"cloud"},
            allowed_geographies={"US"}, allowed_rails={PaymentRail.CARD_NETWORK},
            allowed_destinations={"acct"}, min_assurance=AssuranceLevel.RUNTIME_BOUND,
            max_finality=SettlementFinality.REVERSIBLE,
            not_after=(NOW + timedelta(days=1)).isoformat(),
        )))
    registry = CounterpartyRegistry()
    registry.register_merchant("m", "baseline", {"acct"})
    firewall = TransactionFirewall(graph, counterparties=registry)
    gateway = PaymentIntegrityGateway(
        graph, firewall=firewall, broker=InProcessTestBroker(), ledger=ledger,
        attestation_verifier=AcceptFixtureProof(), user_controls=user_controls)
    return graph, grant, gateway


def intent(grant, amount, nonce):
    value = TransactionIntent(
        authority_grant_id=grant.authority_grant_id, amount=Money.parse(amount),
        merchant_id="m", merchant_verified=True, merchant_baseline_digest="baseline",
        destination="acct", category="cloud", geography="US",
        rail=PaymentRail.CARD_NETWORK, finality=SettlementFinality.REVERSIBLE,
        path_assurance=AssuranceLevel.RUNTIME_BOUND, nonce=nonce)
    value.approved_cart_digest = value.canonical_digest()
    return value


def runtime():
    return RuntimeMeasurement(workload_id="spiffe://a", attested=True,
                              attestation_method="tdx", measured_at=NOW.isoformat())


def test_spend_hold_blocks_second_authorization_before_first_settles():
    _, grant, gateway = system()
    first = gateway.authorize(intent(grant, "60.00", "n1"), runtime=runtime(), now=NOW)
    second = gateway.authorize(intent(grant, "60.00", "n2"), runtime=runtime(), now=NOW)
    assert first.authorized
    assert not second.authorized


def test_ambiguous_without_amount_consumes_authorized_hold():
    graph, grant, gateway = system()
    outcome = gateway.authorize(intent(grant, "60.00", "n1"), runtime=runtime(), now=NOW)
    gateway.settle(outcome, SettlementResult(SettlementState.AMBIGUOUS), now=NOW)
    assert graph.subtree_spend(grant.authority_grant_id).minor_units == 0
    assert graph.subtree_exposure(grant.authority_grant_id).minor_units == 6000


def test_ambiguous_can_reconcile_to_failure_and_release_hold():
    graph, grant, gateway = system()
    outcome = gateway.authorize(intent(grant, "60.00", "n1"), runtime=runtime(), now=NOW)
    gateway.settle(outcome, SettlementResult(SettlementState.AMBIGUOUS), now=NOW)
    gateway.settle(outcome, SettlementResult(SettlementState.FAILED, "rail-1"), now=NOW)
    assert graph.subtree_exposure(grant.authority_grant_id).minor_units == 0


def test_terminal_settlement_cannot_be_counted_twice():
    graph, grant, gateway = system()
    outcome = gateway.authorize(intent(grant, "60.00", "n1"), runtime=runtime(), now=NOW)
    result = SettlementResult(SettlementState.SETTLED, "rail-1", Money.parse("60.00"))
    gateway.settle(outcome, result, now=NOW)
    gateway.settle(outcome, result, now=NOW)
    assert graph.subtree_spend(grant.authority_grant_id).minor_units == 6000


def test_finality_and_facilitator_are_approval_bound():
    value = intent(system()[1], "1.00", "n")
    before = value.canonical_digest()
    value.finality = SettlementFinality.IRREVERSIBLE
    assert value.canonical_digest() != before


def test_human_shield_pause_denies_even_valid_payment():
    controls = UserControlPolicy(paused=True)
    _, grant, gateway = system(user_controls=controls)
    assert not gateway.authorize(intent(grant, "1.00", "n"), runtime=runtime(), now=NOW).authorized


def test_safepay_exact_rejects_requirement_substitution():
    binding = X402V2ExactEVMUSDCBinding(
        networks={"eip155:8453"}, assets={"usdc"}, payees={"0xpayee"})
    payload = {
        "x402Version": 2,
        "accepted": {"scheme": "exact", "network": "eip155:8453", "asset": "usdc",
                     "amount": "100", "payTo": "0xpayee", "extra": {}},
        "paymentRequirements": {"scheme": "exact", "network": "eip155:8453", "asset": "usdc",
                                "amount": "101", "payTo": "0xpayee", "extra": {}},
    }
    assert binding.bind_transaction(payload, "digest").decision.value == "reject"


def test_evidence_vault_uses_keyed_commitment(tmp_path):
    ledger = DurableEvidenceLedger(str(tmp_path / "evidence.jsonl"), integrity_key=b"k" * 32)
    receipt = ledger.append({"owner_of_record": "person", "decision": "deny"})
    redacted = ledger.redacted_receipt(receipt)
    assert redacted["_commitment_type"] == "HMAC-SHA256"
    assert (tmp_path / "evidence.jsonl").exists()
    restored = DurableEvidenceLedger(
        str(tmp_path / "evidence.jsonl"), integrity_key=b"k" * 32
    )
    assert len(restored) == 1
