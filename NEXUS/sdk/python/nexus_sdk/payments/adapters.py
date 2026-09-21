"""
nexus_sdk/payments/adapters.py
Protocol bindings for CP.5.APAY.

TWO CLASSES OF CODE LIVE HERE, AND THEY ARE LABELLED DIFFERENTLY.

1. IdentityNormalizer - IMPLEMENTED AND TESTED.
   Collapses heterogeneous identity sources into one PrincipalBinding. This is
   real because it is a mapping problem NEXUS owns end to end.

2. Rail bindings (AP2, generic x402, Visa TAP / Web Bot Auth, Mastercard Agent
   Pay, KYA-OS) - FAIL-CLOSED CONTRACTS. NOT IMPLEMENTED. DO NOT DEPLOY.
   Every enforcement method raises NotImplementedError by design, matching the
   convention already used by NEXUS/adapters/mcp/adapter.py. An incomplete
   adapter must fail closed, not pass traffic.

   `SafePay Exact` (`X402V2ExactEVMUSDCBinding`) is the sole exception: a narrow
   structural, shadow-mode x402 profile. It performs no live facilitator or
   chain verification and is not production support.

   The remaining contracts are published rather than permissive stubs because:
   each one requires conformance testing against a live counterparty before it
   can be claimed, and shipping a stub that returns success would let a
   deployment believe it has binding it does not have. The contract states what
   must be verified; the implementation is a deliverable, not a detail.

WHAT A BINDING OWES THE GATEWAY
    Every rail binding maps its protocol's artifacts onto exactly four answers:
      - what authority does the counterparty believe exists (mandate/token/grant)
      - what assurance level does this path actually provide
      - what canonical transaction does this protocol's payload correspond to
      - what settlement finality applies
    A binding that cannot answer all four returns REJECT, not a partial result.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Optional

from nexus_sdk.payments.objects import (
    AssuranceLevel,
    PaymentRail,
    PrincipalBinding,
    SettlementFinality,
)

__all__ = [
    "IdentitySource",
    "IdentityClaim",
    "IdentityNormalizer",
    "BindingDecision",
    "BindingResult",
    "RailBinding",
    "AP2Binding",
    "X402Binding",
    "X402V2ExactEVMUSDCBinding",
    "TrustedAgentBinding",
    "AgenticTokenBinding",
    "KYAOSBinding",
]


# ── Identity normalization (implemented) ──────────────────────────────────────

class IdentitySource(str, enum.Enum):
    """Where an identity assertion came from, and what it is good for.

    Each source is strong at something and silent about the rest, which is why
    the normalizer requires the combination rather than picking a winner:

      ENTRA        enterprise ownership and lifecycle; tenant-bound, so it does
                   not travel to another organization's APIs
      KYA_OS       DID-based identity with scoped, revocable delegation and
                   holder-of-key proof; says nothing about payment settlement
      SPIFFE       workload instance identity; the only source that speaks to
                   *which running process*, and the anchor for runtime binding
      WEB_BOT_AUTH per-request authentication of an automated HTTP client;
                   authenticates the operator, not the workload's software state
      ERC_8004     portable on-chain identity and reputation; transferable, so
                   reputation continuity needs a separate continuity rule
      LOCAL_NHI    the deployment's own non-human identity register
    """
    ENTRA = "entra-agent-id"
    KYA_OS = "kya-os"
    SPIFFE = "spiffe"
    WEB_BOT_AUTH = "web-bot-auth"
    ERC_8004 = "erc-8004"
    LOCAL_NHI = "local-nhi"


@dataclass
class IdentityClaim:
    """One assertion from one source."""
    source: IdentitySource
    subject: str
    verified: bool = False
    owner_of_record: Optional[str] = None
    principal_id: Optional[str] = None
    tenant: Optional[str] = None
    key_bound: bool = False           # proof of possession, not a bearer assertion
    transferable: bool = False        # can this identity change hands (ERC-8004 case)
    attributes: dict[str, Any] = field(default_factory=dict)


class IdentityNormalizer:
    """Collapse identity claims into a single verified PrincipalBinding.

    The rule that matters: a payment-capable binding requires a workload-level
    claim (SPIFFE or equivalent) *and* an accountability claim naming a human
    owner. Neither alone is sufficient.

      - Workload identity without an owner is an orphan that can spend.
      - An owner without workload identity cannot support runtime binding, so
        the strongest assurance level it can ever reach is MANDATE_BOUND.

    Transferable identities never raise assurance on their own. An ERC-8004
    token proves possession of a registry entry, not continuity of the operator
    that earned its reputation, so it contributes provenance and nothing else.
    """

    REQUIRED_FOR_PAYMENT = {IdentitySource.SPIFFE}

    def normalize(self, agent_did: str, claims: list[IdentityClaim], *,
                  act_tier: int = 2,
                  hear_authority: Optional[str] = None) -> PrincipalBinding:
        verified = [c for c in claims if c.verified]
        if not verified:
            raise ValueError("no verified identity claims; refusing to bind a payment principal")

        owner = next((c.owner_of_record for c in verified if c.owner_of_record), None)
        if not owner:
            raise ValueError(
                "no owner of record in any verified claim (AISM I-5); "
                "a payment-capable agent requires accountable human ownership"
            )

        principal_id = next((c.principal_id for c in verified if c.principal_id), None)
        if not principal_id:
            raise ValueError("no principal_id in any verified claim")

        spiffe = next((c.subject for c in verified if c.source is IdentitySource.SPIFFE), None)

        return PrincipalBinding(
            principal_id=principal_id,
            owner_of_record=owner,
            agent_did=agent_did,
            act_tier=act_tier,
            hear_authority=hear_authority,
            identity_sources=[c.source.value for c in verified],
            spiffe_id=spiffe,
        )

    def max_assurance(self, claims: list[IdentityClaim]) -> AssuranceLevel:
        """Ceiling on assurance that identity alone can support.

        Identity never reaches RUNTIME_BOUND by itself. That level requires a
        fresh workload measurement, which is a different kind of evidence than
        any identity assertion: identity says who, measurement says what is
        running. Conflating them is the gap this whole profile exists to close.
        """
        verified = {c.source for c in claims if c.verified}
        if IdentitySource.SPIFFE in verified:
            return AssuranceLevel.MANDATE_BOUND
        if verified & {IdentitySource.KYA_OS, IdentitySource.ENTRA}:
            return AssuranceLevel.MANDATE_BOUND
        if IdentitySource.WEB_BOT_AUTH in verified:
            return AssuranceLevel.SIGNED_REQUEST
        if verified:
            return AssuranceLevel.BEARER
        return AssuranceLevel.NONE

    def payment_eligible(self, claims: list[IdentityClaim]) -> tuple[bool, list[str]]:
        verified = {c.source for c in claims if c.verified}
        missing = [s.value for s in self.REQUIRED_FOR_PAYMENT if s not in verified]
        has_owner = any(c.verified and c.owner_of_record for c in claims)
        if not has_owner:
            missing.append("owner_of_record")
        return (not missing), missing


# ── Rail bindings (fail-closed contracts) ─────────────────────────────────────

class BindingDecision(str, enum.Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    HALT = "halt"


@dataclass
class BindingResult:
    decision: BindingDecision
    assurance: AssuranceLevel = AssuranceLevel.NONE
    finality: SettlementFinality = SettlementFinality.IRREVERSIBLE
    canonical_digest: Optional[str] = None
    reason: str = ""
    findings: list[str] = field(default_factory=list)


class RailBinding:
    """In-path contract for one payment protocol.

    STATUS: CONTRACT ONLY. Every method raises. Implementations must be
    conformance-tested against a live counterparty before the binding is
    described as supported anywhere in this repository.
    """

    protocol: str = "abstract"
    protocol_version: str = ""
    scheme: str = ""
    payment_flow: str = ""
    native_finality: SettlementFinality = SettlementFinality.IRREVERSIBLE
    authoritative_verification: bool = False
    rail: PaymentRail = PaymentRail.CARD_NETWORK
    #: The highest assurance this protocol can provide on its own, before any
    #: runtime measurement is added. No protocol here reaches RUNTIME_BOUND.
    max_native_assurance: AssuranceLevel = AssuranceLevel.NONE

    def verify_authority(self, payload: dict) -> BindingResult:
        """Confirm the counterparty's own authority artifact is valid and unexpired."""
        raise NotImplementedError(f"{self.protocol}.verify_authority: fail closed until implemented")

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        """Extract the support tuple actually exercised by a payload."""
        raise NotImplementedError(f"{self.protocol}.support_tuple_of: fail closed until implemented")

    def bind_transaction(self, payload: dict, canonical_digest: str) -> BindingResult:
        """Confirm the protocol payload corresponds to the canonical transaction."""
        raise NotImplementedError(f"{self.protocol}.bind_transaction: fail closed until implemented")

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        """Report the assurance this specific path provides. Never optimistic."""
        raise NotImplementedError(f"{self.protocol}.assurance_of: fail closed until implemented")

    def finality_of(self, payload: dict) -> SettlementFinality:
        raise NotImplementedError(f"{self.protocol}.finality_of: fail closed until implemented")

    def reconcile(self, payload: dict) -> BindingResult:
        """Resolve an ambiguous settlement. Must be idempotent and never retry blindly."""
        raise NotImplementedError(f"{self.protocol}.reconcile: fail closed until implemented")


class AP2Binding(RailBinding):
    """Google AP2, contributed to the FIDO Alliance in April 2026.

    What AP2 already gives us, and we therefore do not rebuild: signed open and
    closed mandates, cart-to-payment binding, constraint evaluation, receipts,
    selective disclosure, and a security model that explicitly treats the agent
    and the LLM as potential attackers because prompt injection cannot be
    assumed preventable.

    What the binding must still verify, because AP2 does not:
      - the mandate's constraints are not wider than the NEXUS authority grant
      - the executing workload matches a fresh, approved runtime measurement
      - the revocation epoch in the grant is current at credential release
      - the cart bound into the mandate matches the canonical transaction digest
    """
    protocol = "ap2"
    max_native_assurance = AssuranceLevel.MANDATE_BOUND


class X402Binding(RailBinding):
    """Coinbase x402, under Linux Foundation governance since April 2026.

    Settlement here is typically irreversible, which changes the control
    calculus rather than simplifying it: removing the chargeback removes
    recourse for both sides, so destination binding and pre-settlement policy
    hooks carry weight that dispute rights would otherwise carry.

    The binding must distinguish verification from settlement timing, enforce
    idempotency across retries, and treat facilitator identity as a trust
    decision rather than a routing detail.
    """
    protocol = "x402"
    rail = PaymentRail.STABLECOIN
    max_native_assurance = AssuranceLevel.MANDATE_BOUND


class X402V2ExactEVMUSDCBinding(X402Binding):
    """SafePay Exact (`X402V2ExactEVMUSDCBinding`).

    A deliberately narrow, shadow-mode binding for x402 v2 `exact`, EVM,
    USDC-like atomic amounts, and the `authorization` flow. Unknown fields do
    not widen support: unsupported versions, schemes, flows, networks, assets,
    and missing NEXUS continuity claims are rejected.
    """
    human_name = "SafePay Exact"
    technical_name = "X402V2ExactEVMUSDCBinding"
    protocol_version = "2"
    scheme = "exact"
    payment_flow = "authorization"
    native_finality = SettlementFinality.IRREVERSIBLE
    authoritative_verification = False
    # Structural validation is not cryptographic authority verification.
    max_native_assurance = AssuranceLevel.NONE

    def __init__(self, *, networks: set[str], assets: set[str], payees: set[str],
                 facilitator: Optional[str] = None, status_resolver=None):
        self.networks = set(networks)
        self.assets = set(assets)
        self.payees = set(payees)
        self.facilitator = facilitator
        self.status_resolver = status_resolver

    def _accepted(self, payload: dict) -> tuple[Optional[dict], list[str]]:
        findings: list[str] = []
        if payload.get("x402Version") != 2:
            findings.append("unsupported x402 version")
        accepted = payload.get("accepted")
        requirements = payload.get("paymentRequirements")
        if not isinstance(accepted, dict):
            findings.append("accepted requirements missing")
            return None, findings
        if requirements is not None and accepted != requirements:
            findings.append("accepted requirements differ from trusted requirements")
        if accepted.get("scheme") != "exact":
            findings.append("scheme is not exact")
        if accepted.get("network") not in self.networks:
            findings.append("network not allowlisted")
        if accepted.get("asset") not in self.assets:
            findings.append("asset not allowlisted")
        if accepted.get("payTo") not in self.payees:
            findings.append("payee not allowlisted")
        if not str(accepted.get("amount", "")).isdigit():
            findings.append("amount is not atomic-unit integer")
        flow = (accepted.get("extra") or {}).get("paymentFlow", "authorization")
        if flow != "authorization":
            findings.append("only authorization flow is supported")
        return accepted, findings

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        accepted = payload.get("accepted")
        if not isinstance(accepted, dict):
            return {}
        extra = accepted.get("extra")
        if not isinstance(extra, dict):
            extra = {}
        return {
            "protocol_version": str(payload.get("x402Version", "")),
            "scheme": str(accepted.get("scheme", "")),
            "network": str(accepted.get("network", "")),
            "asset": str(accepted.get("asset", "")),
            "payment_flow": str(extra.get("paymentFlow", "authorization")),
        }

    def verify_authority(self, payload: dict) -> BindingResult:
        _, findings = self._accepted(payload)
        nexus = ((payload.get("extensions") or {}).get("nexus") or {})
        for claim_name in ("authorityGrantDigest", "revocationEpoch", "nonce", "expiresAt"):
            if nexus.get(claim_name) in (None, ""):
                findings.append(f"missing nexus.{claim_name}")
        try:
            expires = datetime.fromisoformat(str(nexus.get("expiresAt", "")).replace("Z", "+00:00"))
            if expires <= datetime.now(timezone.utc):
                findings.append("nexus authority binding expired")
        except ValueError:
            findings.append("invalid nexus.expiresAt")
        return BindingResult(BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
                             assurance=self.max_native_assurance,
                             finality=SettlementFinality.IRREVERSIBLE,
                             reason="; ".join(findings) or "structure and continuity claims accepted",
                             findings=findings)

    def bind_transaction(self, payload: dict, canonical_digest: str) -> BindingResult:
        accepted, findings = self._accepted(payload)
        nexus = ((payload.get("extensions") or {}).get("nexus") or {})
        bound = nexus.get("canonicalDigest")
        if bound != canonical_digest:
            findings.append("canonical transaction digest mismatch")
        return BindingResult(BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
                             assurance=self.max_native_assurance,
                             finality=SettlementFinality.IRREVERSIBLE,
                             canonical_digest=bound,
                             reason="; ".join(findings) or "transaction bound",
                             findings=findings)

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        return (self.max_native_assurance if self.verify_authority(payload).decision is BindingDecision.ACCEPT
                else AssuranceLevel.NONE)

    def finality_of(self, payload: dict) -> SettlementFinality:
        _, findings = self._accepted(payload)
        if findings:
            raise ValueError("unsupported x402 path: " + "; ".join(findings))
        return SettlementFinality.IRREVERSIBLE

    def reconcile(self, payload: dict) -> BindingResult:
        key = payload.get("idempotencyKey")
        if not key or self.status_resolver is None:
            return BindingResult(BindingDecision.HALT, reason="reconciliation unavailable; do not resubmit")
        status = self.status_resolver(key)
        if status not in {"settled", "failed", "pending"}:
            return BindingResult(BindingDecision.HALT, reason="unknown facilitator status")
        return BindingResult(BindingDecision.ACCEPT if status in {"settled", "failed"} else BindingDecision.HALT,
                             reason=f"facilitator status: {status}")


class TrustedAgentBinding(RailBinding):
    """Visa Trusted Agent Protocol, aligned with Web Bot Auth.

    TAP establishes signed agent-to-merchant interaction and browse-versus-pay
    intent using HTTP Message Signatures. Web Bot Auth remains an IETF
    Internet-Draft, not an RFC.

    The distinction this binding must preserve: TAP authenticates the automated
    client or its operator. It does not attest the workload's software state,
    memory integrity, or conformance with the principal's mandate. Treating a
    valid TAP signature as evidence of an uncompromised agent is the specific
    error CP.5.APAY exists to prevent.
    """
    protocol = "visa-tap"
    max_native_assurance = AssuranceLevel.SIGNED_REQUEST


class AgenticTokenBinding(RailBinding):
    """Mastercard Agent Pay agentic tokens and Agent Pay for Machines.

    Agentic tokens bind a tokenized credential to an agent, a merchant scope and
    a consent policy. The binding must confirm that the token's scope is not
    wider than the NEXUS grant, and that high-frequency machine transactions
    aggregate against the authority tree rather than only against the token's
    own per-transaction limit.
    """
    protocol = "mastercard-agent-pay"
    max_native_assurance = AssuranceLevel.MANDATE_BOUND


class KYAOSBinding(RailBinding):
    """KYA-OS, stewarded by the Decentralized Identity Foundation.

    Provides DID-based identity, scoped and revocable delegation, holder-of-key
    proof, consent gating and audit trails. It is an identity and delegation
    layer, not a payment layer: it does not establish settlement invariants or
    workload-behavior assurance.

    The binding maps KYA-OS delegation scopes onto AuthorityConstraints axes and
    must fail closed on any scope dimension it cannot map, rather than treating
    an unmapped dimension as unconstrained.
    """
    protocol = "kya-os"
    max_native_assurance = AssuranceLevel.MANDATE_BOUND
