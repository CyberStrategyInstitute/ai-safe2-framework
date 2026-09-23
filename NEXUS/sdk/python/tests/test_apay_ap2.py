import base64
import hashlib
from copy import deepcopy

from nexus_sdk.payments import (
    AP2ReceiptEvidence, AP2V02Binding, AP2VerificationEvidence,
    AssuranceLevel, BindingDecision, RailBindingCase,
    RailBindingConformanceSuite, RailBindingContract, SettlementFinality,
)


class Verifier:
    def verify(self, request):
        return AP2VerificationEvidence(
            True, "trusted", AP2V02Binding._request_digest(request),
            authenticated=True, signatures_valid=True, constraints_valid=True,
            key_confirmation_valid=True, replay_safe=True,
            merchant_checkout_jwt_valid=True,
        )

    def verify_receipts(self, request):
        return AP2ReceiptEvidence(
            True, "trusted", AP2V02Binding._request_digest(request),
            authenticated=True, checkout_reference_valid=True,
            payment_reference_valid=True, receipts_signed=True,
        )


def checkout_hash(value="merchant.signed.checkout"):
    digest = hashlib.sha256(value.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def payload(mode="direct"):
    transaction_id = checkout_hash()
    result = {
        "ap2Version": "0.2", "mode": mode,
        "checkoutMandate": {
            "vct": "mandate.checkout.1", "checkout_jwt": "merchant.signed.checkout",
            "checkout_hash": transaction_id, "iss": "https://merchant.example", "exp": 2000000000,
        },
        "paymentMandate": {
            "vct": "mandate.payment.1", "transaction_id": transaction_id,
            "payee": {"website": "https://merchant.example"},
            "payment_amount": {"currency": "USD", "amount": 2599},
            "payment_instrument": {"id": "token-ref", "type": "card"},
            "aud": "credential-provider.example", "iss": "did:user:123", "exp": 2000000000,
        },
        "extensions": {"nexus": {
            "canonicalDigest": "sha256:cart", "authorityGrantDigest": "sha256:grant",
            "revocationEpoch": 7, "nonce": "n-1", "expiresAt": "2030-01-01T00:00:00Z",
        }},
        "receipts": {"checkout": "signed.checkout.receipt", "payment": "signed.payment.receipt"},
    }
    if mode == "autonomous":
        result.update({
            "openCheckoutMandate": {"vct": "mandate.checkout.open.1", "cnf": {"jwk": {}}},
            "openPaymentMandate": {"vct": "mandate.payment.open.1", "cnf": {"jwk": {}}},
            "disclosures": [{"type": "payment.amount_range"}],
        })
    return result


def binding(mode="direct", verifier=None):
    return AP2V02Binding(
        verifier=verifier or Verifier(), trusted_verifiers={"trusted"},
        audiences={"credential-provider.example"}, currencies={"USD"}, mode=mode,
        now=lambda: 1800000000,
    )


def test_direct_mandates_and_receipts_are_authoritatively_verified():
    item = payload()
    assert binding().verify_authority(item).decision is BindingDecision.ACCEPT
    assert binding().bind_transaction(item, "sha256:cart").decision is BindingDecision.ACCEPT
    assert binding().verify_receipts(item).decision is BindingDecision.ACCEPT


def test_hash_version_amount_audience_and_canonical_substitution_fail_closed():
    changes = [
        ("checkoutMandate", "checkout_hash", "attacker"),
        ("paymentMandate", "vct", "mandate.payment.2"),
        ("paymentMandate", "aud", "attacker.example"),
        ("paymentMandate", "payment_amount", {"currency": "USD", "amount": True}),
    ]
    for section, field, value in changes:
        item = payload()
        item[section][field] = value
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
    assert (binding().bind_transaction(payload(), "sha256:attacker").decision
            is BindingDecision.REJECT)


def test_autonomous_mode_requires_open_mandates_key_confirmation_and_disclosures():
    item = payload("autonomous")
    assert binding("autonomous").verify_authority(item).decision is BindingDecision.ACCEPT
    for missing in ("openCheckoutMandate", "openPaymentMandate", "disclosures"):
        changed = deepcopy(item)
        del changed[missing]
        assert binding("autonomous").verify_authority(changed).decision is BindingDecision.REJECT


def test_untrusted_or_incomplete_verifier_evidence_is_rejected_and_outage_halts():
    class Weak(Verifier):
        def verify(self, request):
            return AP2VerificationEvidence(True, "trusted", AP2V02Binding._request_digest(request),
                                           authenticated=True, signatures_valid=True)
    assert binding(verifier=Weak()).verify_authority(payload()).decision is BindingDecision.REJECT

    class Down(Verifier):
        def verify(self, request):
            raise TimeoutError
    assert binding(verifier=Down()).verify_authority(payload()).decision is BindingDecision.HALT


def test_malformed_truthy_and_reason_collision_evidence_fail_closed():
    class WrongShape(Verifier):
        def verify(self, request):
            return {"valid": True}

    class Truthy(Verifier):
        def verify(self, request):
            evidence = super().verify(request)
            return AP2VerificationEvidence(
                **{**evidence.__dict__, "authenticated": "false", "valid": "false"}
            )

    class Collision(Verifier):
        def verify(self, request):
            evidence = super().verify(request)
            return AP2VerificationEvidence(
                **{**evidence.__dict__, "constraints_valid": False,
                   "invalid_reason": "mandate constraints are invalid"}
            )

    wrong_shape = binding(verifier=WrongShape()).verify_authority(payload())
    assert binding(verifier=Truthy()).verify_authority(payload()).decision is BindingDecision.REJECT
    collision = binding(verifier=Collision()).verify_authority(payload())
    assert wrong_shape.decision is BindingDecision.HALT
    assert collision.decision is BindingDecision.REJECT


def test_receipts_must_be_signed_and_bound_by_authenticated_verifier():
    class WeakReceipt(Verifier):
        def verify_receipts(self, request):
            return AP2ReceiptEvidence(True, "trusted", AP2V02Binding._request_digest(request),
                                      authenticated=True)
    assert (binding(verifier=WeakReceipt()).verify_receipts(payload()).decision
            is BindingDecision.REJECT)

    class WrongShape(Verifier):
        def verify_receipts(self, request):
            return {"valid": True}

    assert (binding(verifier=WrongShape()).verify_receipts(payload()).decision
            is BindingDecision.HALT)


def test_malformed_nested_objects_reject_without_raising():
    for section in ("extensions", "paymentMandate"):
        item = payload()
        item[section] = "attacker-controlled"
        assert binding().verify_authority(item).decision is BindingDecision.REJECT
        assert binding().bind_transaction(item, "sha256:cart").decision is BindingDecision.REJECT
        assert binding().assurance_of(item) is AssuranceLevel.NONE
        assert isinstance(binding().support_tuple_of(item), dict)
    item = payload()
    item["extensions"]["nexus"] = ["not", "an", "object"]
    assert binding().verify_authority(item).decision is BindingDecision.REJECT


def test_offsetless_authority_expiry_is_rejected():
    item = payload()
    item["extensions"]["nexus"]["expiresAt"] = "2030-01-01T00:00:00"
    assert binding().verify_authority(item).decision is BindingDecision.REJECT


def test_receipts_cannot_bypass_invalid_or_expired_mandates():
    item = payload()
    item["paymentMandate"]["vct"] = "mandate.payment.2"
    assert binding().verify_receipts(item).decision is BindingDecision.REJECT


def test_mandate_bridge_passes_railguard_lab():
    item = payload()
    contract = RailBindingContract(
        human_name="Mandate Bridge", technical_name="AP2V02Binding", protocol="ap2",
        protocol_version="0.2", scheme="sd-jwt",
        networks=frozenset({"credential-provider.example"}), assets=frozenset({"USD"}),
        payment_flow="direct", finality=SettlementFinality.REVERSIBLE,
        max_native_assurance=AssuranceLevel.MANDATE_BOUND,
        authoritative_verification=True,
    )
    case = RailBindingCase("direct", item, "sha256:cart",
                           BindingDecision.ACCEPT, BindingDecision.ACCEPT,
                           SettlementFinality.REVERSIBLE)
    assert RailBindingConformanceSuite().evaluate(binding(), contract, [case]).passed
