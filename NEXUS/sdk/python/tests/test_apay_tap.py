from copy import deepcopy

from nexus_sdk.payments import (
    AssuranceLevel, BindingDecision, RailBindingCase,
    RailBindingConformanceSuite, RailBindingContract, SettlementFinality,
    TAPVerificationEvidence, VisaTAPBinding,
)


class Verifier:
    def verify(self, request):
        return TAPVerificationEvidence(
            True, "trusted", VisaTAPBinding._request_digest(request),
            authenticated=True, signature_valid=True,
            covered_components_valid=True, freshness_valid=True,
            replay_safe=True, key_trusted=True, discovery_ssrf_safe=True,
            payment_container_valid=True,
        )


def payload():
    return {
        "tapVersion": "merchant-spec@2026-09-22",
        "method": "POST", "authority": "merchant.example", "path": "/checkout",
        "headers": {"content-digest": "sha-256=:digest:"},
        "signatureInput": {
            "tag": "agent-payer-auth",
            "coveredComponents": ["@method", "@authority", "@path", "content-digest"],
            "created": 1790100000, "expires": 1790100300,
            "nonce": "fresh-nonce", "keyid": "trusted-key", "alg": "Ed25519",
        },
        "signature": "message-signature",
        "agenticPaymentContainer": {
            "nonce": "fresh-nonce", "kid": "trusted-key", "alg": "Ed25519",
            "signature": "container-signature", "type": "network-token",
        },
        "extensions": {"nexus": {
            "canonicalDigest": "sha256:cart", "authorityGrantDigest": "sha256:grant",
            "revocationEpoch": 8, "nonce": "nexus-nonce",
            "expiresAt": "2026-09-22T23:00:00Z",
        }},
    }


def binding(verifier=None):
    return VisaTAPBinding(
        verifier=verifier or Verifier(), trusted_verifiers={"trusted"},
        authorities={"merchant.example"}, algorithms={"Ed25519"},
        payment_container_types={"network-token"},
    )


def test_payment_request_is_authoritatively_verified_and_bound():
    assert binding().verify_authority(payload()).decision is BindingDecision.ACCEPT
    result = binding().bind_transaction(payload(), "sha256:cart")
    assert result.decision is BindingDecision.ACCEPT
    assert result.assurance is AssuranceLevel.SIGNED_REQUEST


def test_request_substitution_and_browse_intent_are_rejected():
    mutations = [
        ("authority", "attacker.example"),
        ("path", "https://attacker.example/checkout"),
        ("method", "GET"),
    ]
    for field, value in mutations:
        item = payload()
        item[field] = value
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
    item = payload()
    item["signatureInput"]["tag"] = "agent-browser-auth"
    assert binding().verify_authority(item).decision is BindingDecision.REJECT


def test_required_covered_components_are_not_optional():
    item = payload()
    item["signatureInput"]["coveredComponents"].remove("content-digest")
    assert binding().verify_authority(item).decision is BindingDecision.REJECT


def test_payment_container_must_bind_nonce_key_algorithm_and_type():
    for field, value in (
        ("nonce", "replayed"), ("kid", "other-key"),
        ("alg", "none"), ("type", "raw-pan"),
    ):
        item = payload()
        item["agenticPaymentContainer"][field] = value
        assert binding().verify_authority(item).decision is BindingDecision.REJECT


def test_weak_verifier_evidence_rejects_and_outage_halts():
    class Weak(Verifier):
        def verify(self, request):
            return TAPVerificationEvidence(
                True, "trusted", VisaTAPBinding._request_digest(request),
                authenticated=True, signature_valid=True,
            )
    assert binding(Weak()).verify_authority(payload()).decision is BindingDecision.REJECT

    class Down(Verifier):
        def verify(self, request):
            raise TimeoutError
    assert binding(Down()).verify_authority(payload()).decision is BindingDecision.HALT


def test_malformed_nested_values_fail_closed_without_mutation():
    original = payload()
    for field in ("signatureInput", "agenticPaymentContainer", "headers", "extensions"):
        item = deepcopy(original)
        item[field] = "attacker-controlled"
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
    assert original == payload()


def test_card_trust_bridge_passes_railguard_lab():
    contract = RailBindingContract(
        human_name="Card Trust Bridge", technical_name="VisaTAPBinding",
        protocol="visa-tap", protocol_version="merchant-spec@2026-09-22",
        scheme="rfc9421", networks=frozenset({"merchant.example"}),
        assets=frozenset({"network-token"}), payment_flow="agent-payer-auth",
        finality=SettlementFinality.REVERSIBLE,
        max_native_assurance=AssuranceLevel.SIGNED_REQUEST,
        authoritative_verification=True,
    )
    case = RailBindingCase(
        "payment", payload(), "sha256:cart", BindingDecision.ACCEPT,
        BindingDecision.ACCEPT, SettlementFinality.REVERSIBLE,
    )
    assert RailBindingConformanceSuite().evaluate(binding(), contract, [case]).passed
