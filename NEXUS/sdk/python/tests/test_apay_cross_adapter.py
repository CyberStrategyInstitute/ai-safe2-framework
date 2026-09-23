from dataclasses import MISSING, fields

from nexus_sdk.payments import (
    AP2ReceiptEvidence, AP2VerificationEvidence, AP4MAuthorityEvidence,
    AP4MSettlementEvidence, AssuranceLevel, KYAOSVerificationEvidence,
    MastercardAP4MBinding, TAPVerificationEvidence, VisaTAPBinding,
    X402SettlementEvidence, X402V2ExactEVMUSDCAuthoritativeBinding,
    X402VerificationEvidence,
)
from nexus_sdk.payments.ap2 import AP2V02Binding
from nexus_sdk.payments.kyaos import KYAOSBinding


class CrossAdapterSecuritySuite:
    """Verifier Contract Shield: invariants shared by authoritative adapters."""

    evidence_types = (
        AP2VerificationEvidence, AP2ReceiptEvidence, TAPVerificationEvidence,
        AP4MAuthorityEvidence, AP4MSettlementEvidence, KYAOSVerificationEvidence,
        X402VerificationEvidence, X402SettlementEvidence,
    )

    def test_security_boolean_defaults_never_fail_open(self):
        for evidence_type in self.evidence_types:
            for item in fields(evidence_type):
                if item.type == "bool" or item.type is bool:
                    if item.default is not MISSING:
                        assert item.default is False, (
                            evidence_type.__name__, item.name,
                        )

    def test_no_adapter_claims_native_runtime_proof(self):
        for adapter in (
            X402V2ExactEVMUSDCAuthoritativeBinding, AP2V02Binding,
            VisaTAPBinding, MastercardAP4MBinding, KYAOSBinding,
        ):
            assert adapter.max_native_assurance < AssuranceLevel.RUNTIME_BOUND


TestCrossAdapterSecuritySuite = CrossAdapterSecuritySuite
