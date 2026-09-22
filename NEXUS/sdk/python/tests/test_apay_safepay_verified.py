"""SafePay Verified authoritative evidence tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nexus_sdk.payments import (
    BindingDecision, X402SettlementEvidence, X402VerificationEvidence,
    X402V2ExactEVMUSDCAuthoritativeBinding,
)


def payload():
    accepted = {"scheme": "exact", "network": "eip155:8453", "asset": "usdc",
                "amount": "100", "payTo": "0xpayee", "extra": {}}
    return {"x402Version": 2, "accepted": accepted,
            "paymentRequirements": dict(accepted),
            "payload": {"signature": "0xsig", "authorization": {
                "from": "0xpayer", "to": "0xpayee", "value": "100",
                "validAfter": "0", "validBefore": "9999999999", "nonce": "0x" + "01" * 32}},
            "extensions": {"nexus": {"authorityGrantDigest": "sha256:grant",
                "revocationEpoch": 1, "nonce": "n", "canonicalDigest": "sha256:tx",
                "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}}}


class FixtureVerifier:
    facilitator = "facilitator.example"

    def verify(self, request):
        digest = X402V2ExactEVMUSDCAuthoritativeBinding._request_digest(request)
        return X402VerificationEvidence(True, self.facilitator, digest,
                                        payer="0xpayer", authenticated=True)

    def settlement(self, request):
        digest = X402V2ExactEVMUSDCAuthoritativeBinding._request_digest(request)
        return X402SettlementEvidence(True, self.facilitator, digest, "eip155:8453",
                                      "0xtransaction", payer="0xpayer", amount="100",
                                      authenticated=True)


def binding(verifier=None):
    return X402V2ExactEVMUSDCAuthoritativeBinding(
        verifier=verifier or FixtureVerifier(), trusted_facilitators={"facilitator.example"},
        networks={"eip155:8453"}, assets={"usdc"}, payees={"0xpayee"})


def test_authenticated_verification_and_settlement_are_accepted():
    assert binding().verify_authority(payload()).decision is BindingDecision.ACCEPT
    assert binding().verify_settlement(payload()).decision is BindingDecision.ACCEPT


def test_untrusted_facilitator_is_rejected():
    verifier = FixtureVerifier()
    verifier.facilitator = "attacker.example"
    assert binding(verifier).verify_authority(payload()).decision is BindingDecision.REJECT


def test_request_digest_mismatch_is_rejected():
    class WrongDigest(FixtureVerifier):
        def verify(self, request):
            return X402VerificationEvidence(True, self.facilitator, "sha256:wrong",
                                            authenticated=True)
    assert binding(WrongDigest()).verify_authority(payload()).decision is BindingDecision.REJECT


def test_verifier_outage_halts_without_claiming_authority():
    class Down(FixtureVerifier):
        def verify(self, request):
            raise TimeoutError
    result = binding(Down()).verify_authority(payload())
    assert result.decision is BindingDecision.HALT
    assert result.assurance.value == 0


def test_settlement_amount_substitution_is_rejected():
    class WrongAmount(FixtureVerifier):
        def settlement(self, request):
            evidence = super().settlement(request)
            return X402SettlementEvidence(**{**evidence.__dict__, "amount": "101"})
    assert binding(WrongAmount()).verify_settlement(payload()).decision is BindingDecision.REJECT
