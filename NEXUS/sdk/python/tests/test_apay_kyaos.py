from copy import deepcopy

import pytest

from nexus_sdk.payments import (
    AssuranceLevel, BindingDecision, KYAOSBinding, KYAOSVerificationEvidence,
    RailBindingCase, RailBindingConformanceSuite, RailBindingContract,
    SettlementFinality,
)


SCOPE_AXES = frozenset({
    "network", "currency", "amount", "counterparty", "transaction", "finality",
})


class Verifier:
    def verify_request(self, request, *, consume_replay):
        operation = request["operation"]
        return KYAOSVerificationEvidence(
            True, "trusted", KYAOSBinding._request_digest(request),
            operation["agentDid"], operation["principalId"], SCOPE_AXES,
            authenticated=True, signature_valid=True, holder_key_bound=True,
            audience_bound=True, request_bound=True, delegation_chain_valid=True,
            trust_root_valid=True, issuer_subject_continuity_valid=True,
            attenuation_valid=True, scope_valid=True, constraints_valid=True,
            consent_valid=True, freshness_valid=True, revocation_current=True,
            replay_safe=True,
        )


def payload():
    return {
        "kyaosVersion": "1.0.0+entity-card.1.1",
        "proofProfile": "org.kya-os/proof.v1",
        "requestProof": {"opaque": "proof-secret"},
        "delegationRef": "urn:kya-os:delegation:1",
        "operation": {
            "canonicalDigest": "sha256:transaction",
            "authorityGrantDigest": "sha256:grant",
            "principalId": "principal-1",
            "agentDid": "did:key:agent-1",
            "scope": "payment:execute",
            "network": "card",
            "currency": "USD",
            "amountMinor": 125,
            "counterparty": "merchant.example",
            "transactionId": "txn-1",
            "finality": "reversible",
        },
        "extensions": {"nexus": {
            "nonce": "nonce-1", "expiresAt": "2026-09-24T00:00:00Z",
            "revocationEpoch": 4,
        }},
    }


def binding(verifier=None):
    return KYAOSBinding(
        verifier=verifier or Verifier(), trusted_verifiers={"trusted"},
        networks={"card"}, assets={"USD"},
        counterparties={"merchant.example"},
        required_scope_axes=set(SCOPE_AXES),
        finality=SettlementFinality.REVERSIBLE,
    )


def test_authority_overlay_binds_exact_transaction_but_not_settlement():
    item = payload()
    assert binding().verify_authority(item).decision is BindingDecision.ACCEPT
    bound = binding().bind_transaction(item, "sha256:transaction")
    assert bound.decision is BindingDecision.ACCEPT
    assert bound.assurance is AssuranceLevel.MANDATE_BOUND
    assert binding().verify_settlement(item).decision is BindingDecision.HALT
    assert binding().reconcile(item).decision is BindingDecision.HALT


def test_operation_substitution_and_unbounded_values_reject():
    changes = [
        ("network", "stablecoin"), ("currency", "EUR"),
        ("amountMinor", True), ("counterparty", "attacker.example"),
        ("scope", "payment:*"), ("finality", "irreversible"),
    ]
    for field, value in changes:
        item = payload()
        item["operation"][field] = value
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
    assert (binding().bind_transaction(payload(), "sha256:attacker").decision
            is BindingDecision.REJECT)


def test_configuration_cannot_omit_a_payment_scope_axis():
    with pytest.raises(ValueError, match="omits payment constraints"):
        KYAOSBinding(
            verifier=Verifier(), trusted_verifiers={"trusted"}, networks={"card"},
            assets={"USD"}, counterparties={"merchant.example"},
            required_scope_axes=set(SCOPE_AXES - {"amount"}),
            finality=SettlementFinality.REVERSIBLE,
        )


def test_every_security_dimension_is_required_and_exactly_boolean():
    fields = (
        "authenticated", "signature_valid", "holder_key_bound", "audience_bound",
        "request_bound", "delegation_chain_valid", "trust_root_valid",
        "issuer_subject_continuity_valid", "attenuation_valid", "scope_valid",
        "constraints_valid", "consent_valid", "freshness_valid",
        "revocation_current", "replay_safe", "valid",
    )
    for field in fields:
        class Weak(Verifier):
            def verify_request(self, request, *, consume_replay, field=field):
                evidence = super().verify_request(
                    request, consume_replay=consume_replay
                )
                return KYAOSVerificationEvidence(
                    **{**evidence.__dict__, field: "false"}
                )
        assert binding(Weak()).verify_authority(payload()).decision is BindingDecision.REJECT


def test_unknown_scope_axis_identity_mismatch_and_wrong_shape_fail_closed():
    class Unmapped(Verifier):
        def verify_request(self, request, *, consume_replay):
            evidence = super().verify_request(request, consume_replay=consume_replay)
            return KYAOSVerificationEvidence(
                **{**evidence.__dict__, "unmapped_scope_axes": ("region",)}
            )

    class WrongIdentity(Verifier):
        def verify_request(self, request, *, consume_replay):
            evidence = super().verify_request(request, consume_replay=consume_replay)
            return KYAOSVerificationEvidence(
                **{**evidence.__dict__, "principal_id": "attacker"}
            )

    class WrongShape(Verifier):
        def verify_request(self, request, *, consume_replay):
            return {"valid": True}

    assert binding(Unmapped()).verify_authority(payload()).decision is BindingDecision.REJECT
    assert binding(WrongIdentity()).verify_authority(payload()).decision is BindingDecision.REJECT
    assert binding(WrongShape()).verify_authority(payload()).decision is BindingDecision.HALT


def test_preflight_does_not_consume_replay_and_bad_digest_cannot_burn_it():
    class SingleUse(Verifier):
        consumed = False

        def verify_request(self, request, *, consume_replay):
            replay_safe = not self.consumed
            if consume_replay and replay_safe:
                self.consumed = True
            evidence = super().verify_request(request, consume_replay=consume_replay)
            return KYAOSVerificationEvidence(
                **{**evidence.__dict__, "replay_safe": replay_safe}
            )

    profile = binding(SingleUse())
    assert profile.verify_authority(payload()).decision is BindingDecision.ACCEPT
    assert (profile.bind_transaction(payload(), "sha256:attacker").decision
            is BindingDecision.REJECT)
    assert (profile.bind_transaction(payload(), "sha256:transaction").decision
            is BindingDecision.ACCEPT)
    assert (profile.bind_transaction(payload(), "sha256:transaction").decision
            is BindingDecision.REJECT)


def test_malformed_or_oversized_request_and_verifier_outage_fail_closed():
    malformed = payload()
    malformed["requestProof"] = {"bad": {1, 2}}
    assert binding().verify_authority(malformed).decision is BindingDecision.REJECT
    oversized = payload()
    oversized["requestProof"] = {"opaque": "x" * 140_000}
    assert binding().verify_authority(oversized).decision is BindingDecision.REJECT

    class Down(Verifier):
        def verify_request(self, request, *, consume_replay):
            raise TimeoutError

    assert binding(Down()).verify_authority(payload()).decision is BindingDecision.HALT


def test_conformance_preserves_input_and_omits_proof_material():
    item = payload()
    original = deepcopy(item)
    contract = RailBindingContract(
        human_name="Portable Delegation Bridge", technical_name="KYAOSBinding",
        protocol="kya-os", protocol_version="1.0.0+entity-card.1.1",
        scheme="org.kya-os/proof.v1", networks=frozenset({"card"}),
        assets=frozenset({"USD"}), payment_flow="authority-overlay",
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
    assert "proof-secret" not in str(report.to_dict())
