from nexus_sdk.payments import (
    BindingDecision, X402SettlementEvidence, X402VerificationEvidence,
    X402V2EscrowBinding, X402V2UptoBinding,
)


class Verifier:
    def verify(self, request):
        digest = X402V2UptoBinding._request_digest(request)
        return X402VerificationEvidence(True, "trusted", digest, authenticated=True)

    def settlement(self, request):
        digest = X402V2UptoBinding._request_digest(request)
        req = request["paymentRequirements"]
        amount = str(req["amount"])
        return X402SettlementEvidence(True, "trusted", digest, req["network"],
                                      "" if amount == "0" else "0xtx",
                                      amount=amount, authenticated=True)


def upto(actual="60", ceiling="100"):
    accepted = {"scheme": "upto", "network": "eip155:8453", "asset": "usdc",
                "payTo": "payee", "amount": ceiling, "extra": {}}
    return {"x402Version": 2, "accepted": accepted,
            "paymentRequirements": {**accepted, "amount": actual},
            "payload": {"signature": "sig", "permit2Authorization": {
                "permitted": {"amount": ceiling}}}}


def variable():
    return X402V2UptoBinding(verifier=Verifier(), trusted_facilitators={"trusted"},
                            networks={"eip155:8453"}, assets={"usdc"}, payees={"payee"})


def test_variable_accepts_partial_and_zero_settlement():
    assert variable().verify_variable_settlement(upto()).decision is BindingDecision.ACCEPT
    assert variable().verify_variable_settlement(upto(actual="0")).decision is BindingDecision.ACCEPT


def test_variable_rejects_actual_above_signed_ceiling():
    assert variable().verify_variable_settlement(upto(actual="101")).decision is BindingDecision.REJECT


def escrow_payload(kind, amount="100", voucher=None):
    accepted = {"scheme": "upto", "network": "solana:main", "asset": "usdc",
                "payTo": "payee", "amount": "100", "extra": {"paymentFlow": "escrow"}}
    body = {"channelId": "channel-1", "type": kind}
    if voucher is not None:
        body["voucherSignature"] = voucher
    return {"x402Version": 2, "accepted": accepted,
            "paymentRequirements": {**accepted, "amount": amount}, "payload": body}


def escrow():
    return X402V2EscrowBinding(verifier=Verifier(), trusted_facilitators={"trusted"},
                              networks={"solana:main"}, assets={"usdc"}, payees={"payee"})


def test_escrow_requires_deposit_before_authenticated_claim():
    binding = escrow()
    assert binding.settle_phase(escrow_payload("claim", "60", "voucher")).decision is BindingDecision.REJECT
    assert binding.settle_phase(escrow_payload("deposit")).decision is BindingDecision.ACCEPT
    assert binding.settle_phase(escrow_payload("claim", "60")).decision is BindingDecision.REJECT
    assert binding.settle_phase(escrow_payload("claim", "60", "voucher")).decision is BindingDecision.ACCEPT


def test_escrow_zero_charge_refund_still_requires_voucher():
    binding = escrow()
    assert binding.settle_phase(escrow_payload("deposit")).decision is BindingDecision.ACCEPT
    assert binding.settle_phase(escrow_payload("claim", "0")).decision is BindingDecision.REJECT
    assert binding.settle_phase(escrow_payload("claim", "0", "voucher")).decision is BindingDecision.ACCEPT
