"""
nexus_sdk.payments - CP.5.APAY Agentic Payments Integrity Profile
Cyber Strategy Institute | NEXUS-A2A v0.4 | AI SAFE2 v3.1

The agent-to-payment enforcement plane.

    Identity proves which agent arrived.
    Mandates prove what authority was granted.
    This plane proves whether this measured workload may still use that
    authority for this transaction, at this moment - and stops the entire
    authority tree when it may not.

STATUS
    Core enforcement is implemented as a reference. Narrow SafePay, Mandate
    Bridge, Card Trust Bridge, Agent Token Bridge, and Portable Delegation
    Bridge profiles have explicit verifier boundaries. See
    HARDENING-AND-EXTENSION.md for their deployment limits.

    Nothing in this package should be described as production-assured until a
    deployment demonstrates the MVP acceptance gates in NEXUS/payments/README.md.

Quick start:
    from nexus_sdk.payments import (
        AuthorityGraph, MandateCompiler, Money, PaymentIntegrityGateway,
        TransactionFirewall, TransactionIntent, InProcessTestBroker,
    )
"""

from nexus_sdk.payments.objects import (
    AssuranceLevel,
    AuthorityConstraints,
    AuthorityGrant,
    CanonicalTransaction,
    ConsequenceClass,
    Money,
    PaymentDecision,
    PaymentRail,
    PaymentReasonCode,
    PrincipalBinding,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
    canonical_hash,
)
from nexus_sdk.payments.authority import (
    AttenuationError,
    AuthorityGraph,
    RevocationPlane,
    SpendRecord,
    ExposureReservation,
    VelocityProfile,
)
from nexus_sdk.payments.mandate import (
    Ambiguity,
    CompiledMandate,
    MandateCompiler,
    RenderedMandate,
    classify_consequence,
)
from nexus_sdk.payments.firewall import (
    CounterpartyRegistry,
    PaymentVerdict,
    ReplayLedger,
    TransactionFirewall,
)
from nexus_sdk.payments.broker import (
    BrokerRefusal,
    CredentialBroker,
    InProcessTestBroker,
    NullCredentialBroker,
    SignedAuthorization,
)
from nexus_sdk.payments.evidence import (
    REQUIRED_EVIDENCE_FIELDS,
    DisclosureTier,
    EvidenceLedger,
    DurableEvidenceLedger,
    PaymentTransactionReceipt,
)
from nexus_sdk.payments.gateway import (
    GatewayMetrics,
    HumanApprovalVerifier,
    NullHumanApprovalVerifier,
    PaymentIntegrityGateway,
    PaymentOutcome,
    SettlementResult,
    SettlementState,
)
from nexus_sdk.payments.opa_input import OPA_INPUT_FIELDS, build_opa_input
from nexus_sdk.payments.execution_plane import (
    ComponentAssurance,
    CredentialReleaseStateStore,
    ExecutionRecord,
    ExecutionState,
    ExecutionTransitionError,
    GatewayReadiness,
    NEXUSPaymentExecutionPlane,
    ReplayDecision,
    SettlementStateStore,
    TransactionalAuthorityStore,
    TransactionalReplayStore,
)
from nexus_sdk.payments.sqlite_state import (
    ExposureCeilingExceededError,
    SQLiteGatewayStateStore,
    StateConflictError,
)
from nexus_sdk.payments.key_guardian import (
    CredentialReleaseEnvelope,
    InProcessHMACReceiptAuthenticator,
    InProcessHMACTestBackend,
    KeyGuardianClient,
    KeyGuardianTransport,
    NullKeyGuardianTransport,
    PolicyAuthorizationReceipt,
    ProtectedSigningBackend,
    ReceiptAuthenticator,
    ReferenceKeyGuardianService,
    RuntimeAuthorizationReceipt,
)
from nexus_sdk.payments.adapters import (
    AP2Binding,
    AgenticTokenBinding,
    BindingDecision,
    BindingResult,
    IdentityClaim,
    IdentityNormalizer,
    IdentitySource,
    RailBinding,
    TrustedAgentBinding,
    X402Binding,
    X402V2ExactEVMUSDCBinding,
    X402VerificationEvidence,
    X402SettlementEvidence,
    X402AuthoritativeVerifier,
    X402V2ExactEVMUSDCAuthoritativeBinding,
)
from nexus_sdk.payments.attestation import (
    AttestationResult, AttestationVerifier, HMACTestAttestationVerifier,
    NullAttestationVerifier,
)
from nexus_sdk.payments.user_control import UserControlDecision, UserControlPolicy
from nexus_sdk.payments.conformance import (
    ConformanceFinding, ConformanceReport, RailBindingCase, RailBindingConformanceSuite,
    RailBindingContract,
)
from nexus_sdk.payments.x402_variable import (
    EscrowPhase, VariableCharge, X402V2EscrowBinding, X402V2UptoBinding,
)
from nexus_sdk.payments.ap2 import (
    AP2AuthoritativeVerifier, AP2ReceiptEvidence, AP2V02Binding,
    AP2VerificationEvidence,
)
from nexus_sdk.payments.tap import (
    TAPAuthoritativeVerifier, TAPVerificationEvidence, VisaTAPBinding,
)
from nexus_sdk.payments.ap4m import (
    AP4MAuthoritativeVerifier, AP4MAuthorityEvidence, AP4MSettlementEvidence,
    MastercardAP4MBinding,
)
from nexus_sdk.payments.kyaos import (
    KYAOSAuthoritativeVerifier, KYAOSBinding, KYAOSVerificationEvidence,
)

__profile_version__ = "CP.5.APAY/0.4"

__all__ = [
    "__profile_version__",
    # objects
    "AssuranceLevel", "AuthorityConstraints", "AuthorityGrant", "CanonicalTransaction",
    "ConsequenceClass", "Money", "PaymentDecision", "PaymentRail", "PaymentReasonCode",
    "PrincipalBinding", "RuntimeMeasurement", "SettlementFinality", "TransactionIntent",
    "canonical_hash",
    # authority
    "AttenuationError", "AuthorityGraph", "RevocationPlane", "SpendRecord", "ExposureReservation", "VelocityProfile",
    # mandate
    "Ambiguity", "CompiledMandate", "MandateCompiler", "RenderedMandate", "classify_consequence",
    # firewall
    "CounterpartyRegistry", "PaymentVerdict", "ReplayLedger", "TransactionFirewall",
    # broker
    "BrokerRefusal", "CredentialBroker", "InProcessTestBroker", "NullCredentialBroker",
    "SignedAuthorization",
    # evidence
    "REQUIRED_EVIDENCE_FIELDS", "DisclosureTier", "EvidenceLedger", "DurableEvidenceLedger", "PaymentTransactionReceipt",
    # gateway
    "GatewayMetrics", "PaymentIntegrityGateway", "PaymentOutcome", "SettlementResult",
    "SettlementState", "HumanApprovalVerifier", "NullHumanApprovalVerifier",
    # OPA binding
    "OPA_INPUT_FIELDS", "build_opa_input",
    # Sovereign Payment Gateway execution contracts
    "ComponentAssurance", "ExecutionRecord", "ExecutionState",
    "ExecutionTransitionError", "GatewayReadiness", "NEXUSPaymentExecutionPlane",
    "ReplayDecision",
    "CredentialReleaseStateStore",
    "SettlementStateStore", "TransactionalAuthorityStore", "TransactionalReplayStore",
    "ExposureCeilingExceededError", "SQLiteGatewayStateStore", "StateConflictError",
    # Isolated credential release
    "CredentialReleaseEnvelope", "InProcessHMACReceiptAuthenticator",
    "InProcessHMACTestBackend", "KeyGuardianClient",
    "KeyGuardianTransport", "NullKeyGuardianTransport", "PolicyAuthorizationReceipt",
    "ProtectedSigningBackend", "ReceiptAuthenticator", "ReferenceKeyGuardianService",
    "RuntimeAuthorizationReceipt",
    # adapters
    "AP2Binding", "AgenticTokenBinding", "BindingDecision", "BindingResult",
    "IdentityClaim", "IdentityNormalizer", "IdentitySource", "KYAOSBinding",
    "RailBinding", "TrustedAgentBinding", "X402Binding", "X402V2ExactEVMUSDCBinding",
    "X402VerificationEvidence", "X402SettlementEvidence", "X402AuthoritativeVerifier",
    "X402V2ExactEVMUSDCAuthoritativeBinding",
    # Runtime Proof and Human Shield
    "AttestationResult", "AttestationVerifier", "HMACTestAttestationVerifier",
    "NullAttestationVerifier", "UserControlDecision", "UserControlPolicy",
    # RailGuard Contract and Lab
    "ConformanceFinding", "ConformanceReport", "RailBindingCase",
    "RailBindingConformanceSuite", "RailBindingContract",
    "EscrowPhase", "VariableCharge", "X402V2EscrowBinding", "X402V2UptoBinding",
    # Mandate Bridge
    "AP2AuthoritativeVerifier", "AP2ReceiptEvidence", "AP2V02Binding",
    "AP2VerificationEvidence",
    # Card Trust Bridge
    "TAPAuthoritativeVerifier", "TAPVerificationEvidence", "VisaTAPBinding",
    # Agent Token Bridge
    "AP4MAuthoritativeVerifier", "AP4MAuthorityEvidence", "AP4MSettlementEvidence",
    "MastercardAP4MBinding",
    # Portable Delegation Bridge
    "KYAOSAuthoritativeVerifier", "KYAOSBinding", "KYAOSVerificationEvidence",
]
