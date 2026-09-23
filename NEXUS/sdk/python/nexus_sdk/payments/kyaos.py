"""Portable Delegation Bridge: KYA-OS v1 authority-overlay profile."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Protocol

from nexus_sdk.payments.adapters import BindingDecision, BindingResult, RailBinding
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality


@dataclass(frozen=True)
class KYAOSVerificationEvidence:
    """Strict output from a trusted KYA-OS verifier implementation."""

    valid: bool
    verifier_id: str
    request_digest: str
    agent_did: str
    principal_id: str
    mapped_scope_axes: frozenset[str]
    unmapped_scope_axes: tuple[str, ...] = ()
    authenticated: bool = False
    signature_valid: bool = False
    holder_key_bound: bool = False
    audience_bound: bool = False
    request_bound: bool = False
    delegation_chain_valid: bool = False
    trust_root_valid: bool = False
    issuer_subject_continuity_valid: bool = False
    attenuation_valid: bool = False
    scope_valid: bool = False
    constraints_valid: bool = False
    consent_valid: bool = False
    freshness_valid: bool = False
    revocation_current: bool = False
    replay_safe: bool = False
    invalid_reason: Optional[str] = None


class KYAOSAuthoritativeVerifier(Protocol):
    """Trusted boundary backed by a conformant KYA-OS verifier."""

    def verify_request(
        self, request: dict, *, consume_replay: bool
    ) -> KYAOSVerificationEvidence:
        """Inspect replay state, or atomically consume it for canonical binding."""
        ...


class KYAOSBinding(RailBinding):
    """Portable Delegation Bridge (`KYAOSBinding`).

    KYA-OS proves identity, delegated authority, and per-request key control. It
    does not prove settlement, workload integrity, merchant honesty, or user
    wisdom. This profile therefore acts only as an authority overlay.
    """

    human_name = "Portable Delegation Bridge"
    technical_name = "KYAOSBinding"
    protocol = "kya-os"
    protocol_version = "1.0.0+entity-card.1.1"
    scheme = "org.kya-os/proof.v1"
    payment_flow = "authority-overlay"
    authoritative_verification = True
    max_native_assurance = AssuranceLevel.MANDATE_BOUND
    _MAX_REQUEST_BYTES = 131_072
    _MAX_REFERENCE_CHARS = 4_096
    _MAX_AMOUNT_MINOR = 2**63 - 1
    _PAYMENT_SCOPE_AXES = frozenset({
        "network", "currency", "amount", "counterparty", "transaction", "finality",
    })

    def __init__(
        self, *, verifier: KYAOSAuthoritativeVerifier,
        trusted_verifiers: set[str], networks: set[str], assets: set[str],
        counterparties: set[str], required_scope_axes: set[str],
        finality: SettlementFinality,
    ):
        self.verifier = verifier
        self.trusted_verifiers = set(trusted_verifiers)
        self.networks = set(networks)
        self.assets = set(assets)
        self.counterparties = set(counterparties)
        self.required_scope_axes = frozenset(required_scope_axes)
        missing_axes = self._PAYMENT_SCOPE_AXES - self.required_scope_axes
        if missing_axes:
            raise ValueError(
                "required_scope_axes omits payment constraints: "
                + ", ".join(sorted(missing_axes))
            )
        self.native_finality = finality

    @staticmethod
    def _object(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _request(payload: dict) -> dict:
        return {
            key: payload.get(key)
            for key in (
                "kyaosVersion", "proofProfile", "requestProof",
                "delegationRef", "operation", "extensions",
            )
            if key in payload
        }

    @classmethod
    def _encoded_request(cls, request: dict) -> bytes:
        return json.dumps(
            request, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()

    @classmethod
    def _request_digest(cls, request: dict) -> str:
        return "sha256:" + hashlib.sha256(cls._encoded_request(request)).hexdigest()

    def _findings(self, payload: dict) -> list[str]:
        findings: list[str] = []
        if payload.get("kyaosVersion") != self.protocol_version:
            findings.append("unsupported KYA-OS profile version")
        if payload.get("proofProfile") != self.scheme:
            findings.append("unsupported KYA-OS proof profile")
        proof = payload.get("requestProof")
        if not isinstance(proof, dict) or not proof:
            findings.append("KYA-OS request proof is required")
        delegation_ref = payload.get("delegationRef")
        if (not isinstance(delegation_ref, str) or not delegation_ref
                or len(delegation_ref) > self._MAX_REFERENCE_CHARS):
            findings.append("bounded delegation reference is required")

        operation = self._object(payload.get("operation"))
        required_strings = (
            "canonicalDigest", "authorityGrantDigest", "principalId",
            "agentDid", "transactionId",
        )
        for name in required_strings:
            value = operation.get(name)
            if not isinstance(value, str) or not value:
                findings.append(f"operation.{name} is required")
        if operation.get("scope") != "payment:execute":
            findings.append("operation scope must be payment:execute")
        if operation.get("network") not in self.networks:
            findings.append("operation network is not allowlisted")
        if operation.get("currency") not in self.assets:
            findings.append("operation currency is not allowlisted")
        if operation.get("counterparty") not in self.counterparties:
            findings.append("operation counterparty is not allowlisted")
        amount = operation.get("amountMinor")
        if (type(amount) is not int or amount < 0
                or amount > self._MAX_AMOUNT_MINOR):
            findings.append("operation amountMinor is outside the bounded integer range")
        if operation.get("finality") != self.native_finality.value:
            findings.append("operation finality differs from the configured payment path")

        extensions = self._object(payload.get("extensions"))
        nexus = self._object(extensions.get("nexus"))
        for name in ("nonce", "expiresAt", "revocationEpoch"):
            if nexus.get(name) in (None, ""):
                findings.append(f"missing nexus.{name}")
        try:
            encoded = self._encoded_request(self._request(payload))
            if len(encoded) > self._MAX_REQUEST_BYTES:
                findings.append("KYA-OS authority request exceeds the size limit")
        except (TypeError, ValueError):
            findings.append("KYA-OS authority request is not canonical JSON")
        return findings

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        operation = self._object(payload.get("operation"))
        return {
            "protocol_version": str(payload.get("kyaosVersion", "")),
            "scheme": str(payload.get("proofProfile", "")),
            "network": str(operation.get("network", "")),
            "asset": str(operation.get("currency", "")),
            "payment_flow": self.payment_flow,
        }

    def _verify_authority(
        self, payload: dict, *, consume_replay: bool
    ) -> BindingResult:
        findings = self._findings(payload)
        if findings:
            return BindingResult(
                BindingDecision.REJECT, reason="; ".join(findings), findings=findings
            )
        request = self._request(payload)
        digest = self._request_digest(request)
        try:
            evidence = self.verifier.verify_request(
                request, consume_replay=consume_replay
            )
        except Exception as exc:
            return BindingResult(
                BindingDecision.HALT,
                reason=f"KYA-OS verifier unavailable: {type(exc).__name__}",
            )
        if not isinstance(evidence, KYAOSVerificationEvidence):
            return BindingResult(
                BindingDecision.HALT,
                reason="KYA-OS verifier returned malformed evidence",
            )
        operation = self._object(payload.get("operation"))
        rejection_reason = (
            evidence.invalid_reason
            if isinstance(evidence.invalid_reason, str) and evidence.invalid_reason
            else "KYA-OS verifier rejected authority"
        )
        checks = [
            ("verification response is unauthenticated", evidence.authenticated is True),
            ("request proof signature is invalid", evidence.signature_valid is True),
            ("agent does not control the holder key", evidence.holder_key_bound is True),
            ("proof audience is not bound", evidence.audience_bound is True),
            ("proof is not bound to the request", evidence.request_bound is True),
            ("delegation chain is invalid", evidence.delegation_chain_valid is True),
            ("delegation trust root is invalid", evidence.trust_root_valid is True),
            ("delegation issuer-subject continuity failed",
             evidence.issuer_subject_continuity_valid is True),
            ("delegation attenuation failed", evidence.attenuation_valid is True),
            ("delegation scope is invalid", evidence.scope_valid is True),
            ("delegation constraints are invalid", evidence.constraints_valid is True),
            ("required user consent is absent", evidence.consent_valid is True),
            ("proof is expired or not yet valid", evidence.freshness_valid is True),
            ("revocation evidence is stale", evidence.revocation_current is True),
            ("proof replay check failed", evidence.replay_safe is True),
            ("authority evidence request digest mismatch",
             isinstance(evidence.request_digest, str)
             and evidence.request_digest == digest),
            ("untrusted KYA-OS verifier",
             isinstance(evidence.verifier_id, str)
             and evidence.verifier_id in self.trusted_verifiers),
            ("agent DID mismatch",
             isinstance(evidence.agent_did, str)
             and evidence.agent_did == operation.get("agentDid")),
            ("principal identity mismatch",
             isinstance(evidence.principal_id, str)
             and evidence.principal_id == operation.get("principalId")),
            ("scope axes were not mapped losslessly",
             type(evidence.mapped_scope_axes) is frozenset
             and evidence.mapped_scope_axes == self.required_scope_axes),
            ("unmapped delegation scope axes remain",
             type(evidence.unmapped_scope_axes) is tuple
             and not evidence.unmapped_scope_axes),
            (rejection_reason, evidence.valid is True),
        ]
        findings = [message for message, passed in checks if not passed]
        return BindingResult(
            BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
            assurance=(AssuranceLevel.NONE if findings else self.max_native_assurance),
            finality=self.native_finality,
            reason="; ".join(findings) or "authenticated KYA-OS authority accepted",
            findings=findings,
        )

    def verify_authority(self, payload: dict) -> BindingResult:
        """Perform non-consuming preflight; canonical binding consumes the nonce."""
        return self._verify_authority(payload, consume_replay=False)

    def bind_transaction(self, payload: dict, canonical_digest: str) -> BindingResult:
        operation = self._object(payload.get("operation"))
        if operation.get("canonicalDigest") != canonical_digest:
            finding = "canonical transaction digest mismatch"
            return BindingResult(
                BindingDecision.REJECT, reason=finding, findings=[finding]
            )
        authority = self._verify_authority(payload, consume_replay=True)
        if authority.decision is not BindingDecision.ACCEPT:
            return authority
        return BindingResult(
            BindingDecision.ACCEPT,
            assurance=self.max_native_assurance,
            finality=self.native_finality,
            canonical_digest=canonical_digest,
            reason="KYA-OS delegation bound to canonical transaction",
        )

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        return AssuranceLevel.NONE

    def finality_of(self, payload: dict) -> SettlementFinality:
        findings = self._findings(payload)
        if findings:
            raise ValueError("unsupported KYA-OS path: " + "; ".join(findings))
        return self.native_finality

    def verify_settlement(self, payload: dict) -> BindingResult:
        return BindingResult(
            BindingDecision.HALT,
            reason="KYA-OS provides no settlement evidence",
        )

    def reconcile(self, payload: dict) -> BindingResult:
        return BindingResult(
            BindingDecision.HALT,
            reason="KYA-OS cannot reconcile payment settlement",
        )
