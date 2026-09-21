"""RailGuard Contract and RailGuard Lab conformance tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nexus_sdk.payments import (
    AssuranceLevel, BindingDecision, RailBindingCase, RailBindingConformanceSuite,
    RailBindingContract, SettlementFinality, X402V2ExactEVMUSDCBinding,
)


def contract(**overrides) -> RailBindingContract:
    values = {
        "human_name": "SafePay Exact",
        "technical_name": "X402V2ExactEVMUSDCBinding",
        "protocol": "x402",
        "protocol_version": "2",
        "scheme": "exact",
        "networks": frozenset({"eip155:8453"}),
        "assets": frozenset({"usdc"}),
        "payment_flow": "authorization",
        "finality": SettlementFinality.IRREVERSIBLE,
        "max_native_assurance": AssuranceLevel.NONE,
        "authoritative_verification": False,
    }
    values.update(overrides)
    return RailBindingContract(**values)


def payload(*, digest: str = "sha256:approved", amount: str = "100") -> dict:
    accepted = {
        "scheme": "exact", "network": "eip155:8453", "asset": "usdc",
        "amount": amount, "payTo": "0xpayee", "extra": {
            "paymentFlow": "authorization"
        },
    }
    return {
        "x402Version": 2,
        "accepted": accepted,
        "paymentRequirements": dict(accepted),
        "extensions": {"nexus": {
            "authorityGrantDigest": "sha256:grant", "revocationEpoch": 1,
            "nonce": "n-1",
            "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "canonicalDigest": digest,
        }},
    }


def binding() -> X402V2ExactEVMUSDCBinding:
    return X402V2ExactEVMUSDCBinding(
        networks={"eip155:8453"}, assets={"usdc"}, payees={"0xpayee"}
    )


def test_safepay_exact_passes_shared_conformance_vectors():
    valid = payload()
    wrong_digest = payload(digest="sha256:attacker")
    missing_authority = payload()
    del missing_authority["extensions"]["nexus"]["authorityGrantDigest"]
    cases = [
        RailBindingCase(
            "valid exact payment", valid, "sha256:approved",
            BindingDecision.ACCEPT, BindingDecision.ACCEPT,
            SettlementFinality.IRREVERSIBLE,
        ),
        RailBindingCase(
            "canonical substitution", wrong_digest, "sha256:approved",
            BindingDecision.ACCEPT, BindingDecision.REJECT,
            SettlementFinality.IRREVERSIBLE,
        ),
        RailBindingCase(
            "missing authority continuity", missing_authority, "sha256:approved",
            BindingDecision.REJECT, BindingDecision.ACCEPT,
            SettlementFinality.IRREVERSIBLE,
        ),
    ]
    report = RailBindingConformanceSuite().evaluate(binding(), contract(), cases)
    assert report.passed, report.to_dict()
    assert report.to_dict()["privacy"] == "payloads omitted"


def test_contract_rejects_assurance_overclaim_without_authoritative_verification():
    findings = contract(max_native_assurance=AssuranceLevel.MANDATE_BOUND).validate()
    assert any("non-authoritative" in item for item in findings)


def test_contract_rejects_runtime_assurance_claim():
    findings = contract(
        max_native_assurance=AssuranceLevel.RUNTIME_BOUND,
        authoritative_verification=True,
    ).validate()
    assert any("Runtime Proof" in item for item in findings)


def test_report_does_not_copy_sensitive_payload_values():
    bad = payload()
    bad["secretCardToken"] = "do-not-log-me"
    bad["accepted"]["network"] = "unknown"
    report = RailBindingConformanceSuite().evaluate(
        binding(), contract(), [RailBindingCase(
            "private vector", bad, "sha256:approved",
            BindingDecision.REJECT, BindingDecision.REJECT,
        )]
    )
    assert "do-not-log-me" not in str(report.to_dict())


def test_empty_case_corpus_fails_conformance():
    report = RailBindingConformanceSuite().evaluate(binding(), contract(), [])
    assert not report.passed
    assert report.findings[0].control == "coverage"
