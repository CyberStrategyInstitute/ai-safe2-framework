from copy import deepcopy

from nexus_sdk.payments import (
    AP4MAuthorityEvidence, AP4MSettlementEvidence, AssuranceLevel,
    BindingDecision, MastercardAP4MBinding, RailBindingCase,
    RailBindingConformanceSuite, RailBindingContract, SettlementFinality,
)


class Verifier:
    def verify_authority(self, request):
        return AP4MAuthorityEvidence(
            True, "trusted", MastercardAP4MBinding._request_digest(request),
            authenticated=True, credential_active=True, agent_bound=True,
            principal_bound=True, authorization_valid=True, transaction_bound=True,
            scope_valid=True, spend_limit_valid=True, cumulative_budget_valid=True,
            velocity_valid=True, counterparty_valid=True, currency_valid=True,
            freshness_valid=True, revocation_current=True, replay_safe=True,
        )

    def verify_settlement(self, request):
        transaction = request["transaction"]
        return AP4MSettlementEvidence(
            True, "trusted", MastercardAP4MBinding._request_digest(request),
            transaction["rail"], transaction["currency"], transaction["amountMinor"],
            transaction["transactionId"], SettlementFinality.REVERSIBLE,
            authenticated=True, authority_continuity_valid=True,
            settlement_guarantee_valid=True,
        )


def payload():
    return {
        "ap4mProfile": "public-product@2026-09-23",
        "credentialArtifact": "opaque:credential:1",
        "authorizationArtifact": "opaque:authorization:1",
        "transaction": {
            "rail": "card", "currency": "USD", "amountMinor": 125,
            "counterparty": "merchant.example", "transactionId": "txn-1",
        },
        "extensions": {"nexus": {
            "canonicalDigest": "sha256:transaction", "authorityGrantDigest": "sha256:grant",
            "revocationEpoch": 4, "nonce": "n-1", "expiresAt": "2026-09-24T00:00:00Z",
        }},
    }


def binding(verifier=None):
    return MastercardAP4MBinding(
        verifier=verifier or Verifier(), trusted_verifiers={"trusted"},
        rails={"card"}, currencies={"USD"}, counterparties={"merchant.example"},
        finality=SettlementFinality.REVERSIBLE,
    )


def test_authority_transaction_and_settlement_are_independently_verified():
    item = payload()
    assert binding().verify_authority(item).decision is BindingDecision.ACCEPT
    result = binding().bind_transaction(item, "sha256:transaction")
    assert result.decision is BindingDecision.ACCEPT
    assert result.assurance is AssuranceLevel.MANDATE_BOUND
    assert binding().verify_settlement(item).decision is BindingDecision.ACCEPT


def test_route_amount_counterparty_and_canonical_substitution_reject():
    changes = [
        ("rail", "stablecoin"), ("currency", "EUR"),
        ("amountMinor", True), ("counterparty", "attacker.example"),
    ]
    for field, value in changes:
        item = payload()
        item["transaction"][field] = value
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
    assert (binding().bind_transaction(payload(), "sha256:attacker").decision
            is BindingDecision.REJECT)


def test_every_authority_dimension_is_required():
    fields = (
        "credential_active", "agent_bound", "principal_bound", "authorization_valid",
        "transaction_bound", "scope_valid", "spend_limit_valid",
        "cumulative_budget_valid", "velocity_valid", "counterparty_valid",
        "currency_valid", "freshness_valid", "revocation_current", "replay_safe",
    )
    for field in fields:
        class Weak(Verifier):
            def verify_authority(self, request, field=field):
                evidence = super().verify_authority(request)
                values = {**evidence.__dict__, field: False}
                return AP4MAuthorityEvidence(**values)
        assert binding(Weak()).verify_authority(payload()).decision is BindingDecision.REJECT


def test_settlement_must_match_exact_transaction_and_guarantee():
    class Wrong(Verifier):
        def verify_settlement(self, request):
            evidence = super().verify_settlement(request)
            return AP4MSettlementEvidence(
                **{**evidence.__dict__, "amount_minor": evidence.amount_minor + 1,
                   "settlement_guarantee_valid": False}
            )
    assert binding(Wrong()).verify_settlement(payload()).decision is BindingDecision.REJECT


def test_malformed_nested_values_and_verifier_outage_fail_closed():
    for field in ("transaction", "extensions"):
        item = payload()
        item[field] = "attacker-controlled"
        assert binding().verify_authority(item).decision is BindingDecision.REJECT

    class Down(Verifier):
        def verify_authority(self, request):
            raise TimeoutError
    assert binding(Down()).verify_authority(payload()).decision is BindingDecision.HALT


def test_payload_is_not_mutated_or_logged_in_conformance_report():
    item = payload()
    original = deepcopy(item)
    contract = RailBindingContract(
        human_name="Agent Token Bridge", technical_name="MastercardAP4MBinding",
        protocol="mastercard-ap4m", protocol_version="public-product@2026-09-23",
        scheme="network-verifier-evidence", networks=frozenset({"card"}),
        assets=frozenset({"USD"}), payment_flow="machine-commerce",
        finality=SettlementFinality.REVERSIBLE,
        max_native_assurance=AssuranceLevel.MANDATE_BOUND,
        authoritative_verification=True,
    )
    case = RailBindingCase(
        "card", item, "sha256:transaction", BindingDecision.ACCEPT,
        BindingDecision.ACCEPT, SettlementFinality.REVERSIBLE,
    )
    report = RailBindingConformanceSuite().evaluate(binding(), contract, [case])
    assert report.passed
    assert item == original
    assert "opaque:credential:1" not in str(report.to_dict())
