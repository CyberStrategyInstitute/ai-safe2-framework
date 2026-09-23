"""Agent Token Bridge: Mastercard AP4M verifier-evidence profile."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Protocol

from nexus_sdk.payments.adapters import BindingDecision, BindingResult, RailBinding
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality


@dataclass(frozen=True)
class AP4MAuthorityEvidence:
    """Authenticated output from a Mastercard-network verifier."""

    valid: bool
    verifier_id: str
    request_digest: str
    authenticated: bool = False
    credential_active: bool = False
    agent_bound: bool = False
    principal_bound: bool = False
    authorization_valid: bool = False
    transaction_bound: bool = False
    scope_valid: bool = False
    spend_limit_valid: bool = False
    cumulative_budget_valid: bool = False
    velocity_valid: bool = False
    counterparty_valid: bool = False
    currency_valid: bool = False
    freshness_valid: bool = False
    revocation_current: bool = False
    replay_safe: bool = False
    invalid_reason: Optional[str] = None


@dataclass(frozen=True)
class AP4MSettlementEvidence:
    """Authenticated network settlement evidence for the exact request."""

    success: bool
    verifier_id: str
    request_digest: str
    rail: str
    currency: str
    amount_minor: int
    transaction_id: str
    finality: SettlementFinality
    authenticated: bool = False
    authority_continuity_valid: bool = False
    settlement_guarantee_valid: bool = False
    invalid_reason: Optional[str] = None


class AP4MAuthoritativeVerifier(Protocol):
    """Trusted boundary for proprietary credential and settlement verification."""

    def verify_authority(self, request: dict) -> AP4MAuthorityEvidence: ...

    def verify_settlement(self, request: dict) -> AP4MSettlementEvidence: ...


class MastercardAP4MBinding(RailBinding):
    """Agent Token Bridge (`MastercardAP4MBinding`).

    Mastercard exposes no public AP4M wire schema. This class validates a
    NEXUS-owned evidence request and trusts only authenticated verifier output;
    it never interprets a proprietary credential or payment token locally.
    """

    human_name = "Agent Token Bridge"
    technical_name = "MastercardAP4MBinding"
    protocol = "mastercard-ap4m"
    protocol_version = "public-product@2026-09-23"
    scheme = "network-verifier-evidence"
    payment_flow = "machine-commerce"
    authoritative_verification = True
    max_native_assurance = AssuranceLevel.MANDATE_BOUND

    def __init__(self, *, verifier: AP4MAuthoritativeVerifier,
                 trusted_verifiers: set[str], rails: set[str],
                 currencies: set[str], counterparties: set[str],
                 finality: SettlementFinality, status_resolver=None):
        self.verifier = verifier
        self.trusted_verifiers = set(trusted_verifiers)
        self.networks = set(rails)
        self.assets = set(currencies)
        self.counterparties = set(counterparties)
        self.native_finality = finality
        self.status_resolver = status_resolver

    @staticmethod
    def _object(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _request(payload: dict) -> dict:
        return {
            key: payload.get(key) for key in (
                "ap4mProfile", "credentialArtifact", "authorizationArtifact",
                "transaction", "extensions",
            ) if key in payload
        }

    @staticmethod
    def _request_digest(request: dict) -> str:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def _findings(self, payload: dict) -> list[str]:
        findings: list[str] = []
        if payload.get("ap4mProfile") != self.protocol_version:
            findings.append("unsupported or unpinned AP4M public-product snapshot")
        for artifact in ("credentialArtifact", "authorizationArtifact"):
            value = payload.get(artifact)
            if not isinstance(value, str) or not value:
                findings.append(f"opaque {artifact} reference is required")
        transaction = self._object(payload.get("transaction"))
        rail = transaction.get("rail")
        currency = transaction.get("currency")
        amount = transaction.get("amountMinor")
        counterparty = transaction.get("counterparty")
        if not isinstance(rail, str) or rail not in self.networks:
            findings.append("settlement rail is not allowlisted")
        if not isinstance(currency, str) or currency not in self.assets:
            findings.append("currency is not allowlisted")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            findings.append("amountMinor must be a non-negative integer")
        if not isinstance(counterparty, str) or counterparty not in self.counterparties:
            findings.append("counterparty is not allowlisted")
        transaction_id = transaction.get("transactionId")
        if not isinstance(transaction_id, str) or not transaction_id:
            findings.append("transactionId is required")
        extensions = self._object(payload.get("extensions"))
        nexus = self._object(extensions.get("nexus"))
        for name in (
            "canonicalDigest", "authorityGrantDigest", "revocationEpoch",
            "nonce", "expiresAt",
        ):
            if nexus.get(name) in (None, ""):
                findings.append(f"missing nexus.{name}")
        return findings

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        transaction = self._object(payload.get("transaction"))
        return {
            "protocol_version": str(payload.get("ap4mProfile", "")),
            "scheme": self.scheme,
            "network": str(transaction.get("rail", "")),
            "asset": str(transaction.get("currency", "")),
            "payment_flow": self.payment_flow,
        }

    def verify_authority(self, payload: dict) -> BindingResult:
        findings = self._findings(payload)
        if findings:
            return BindingResult(BindingDecision.REJECT, reason="; ".join(findings),
                                 findings=findings)
        request = self._request(payload)
        digest = self._request_digest(request)
        try:
            evidence = self.verifier.verify_authority(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT,
                                 reason=f"AP4M verifier unavailable: {type(exc).__name__}")
        checks = [
            ("verification response is unauthenticated", evidence.authenticated),
            ("credential is inactive", evidence.credential_active),
            ("credential is not bound to the agent", evidence.agent_bound),
            ("credential is not bound to the principal", evidence.principal_bound),
            ("verifiable authorization is invalid", evidence.authorization_valid),
            ("authorization is not transaction-bound", evidence.transaction_bound),
            ("authorization scope is invalid", evidence.scope_valid),
            ("transaction exceeds its spend limit", evidence.spend_limit_valid),
            ("authority-tree cumulative budget is exceeded",
             evidence.cumulative_budget_valid),
            ("transaction violates velocity policy", evidence.velocity_valid),
            ("counterparty constraint failed", evidence.counterparty_valid),
            ("currency constraint failed", evidence.currency_valid),
            ("authorization is expired or not yet valid", evidence.freshness_valid),
            ("revocation state is stale", evidence.revocation_current),
            ("authorization replay check failed", evidence.replay_safe),
            ("authority evidence request digest mismatch",
             evidence.request_digest == digest),
            ("untrusted AP4M verifier", evidence.verifier_id in self.trusted_verifiers),
            (evidence.invalid_reason or "AP4M verifier rejected authority", evidence.valid),
        ]
        findings = [message for message, passed in checks if not passed]
        return BindingResult(
            BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
            assurance=(AssuranceLevel.NONE if findings else self.max_native_assurance),
            finality=self.native_finality,
            reason="; ".join(findings) or "authenticated AP4M authority accepted",
            findings=findings,
        )

    def bind_transaction(self, payload: dict, canonical_digest: str) -> BindingResult:
        authority = self.verify_authority(payload)
        if authority.decision is not BindingDecision.ACCEPT:
            return authority
        extensions = self._object(payload.get("extensions"))
        nexus = self._object(extensions.get("nexus"))
        if nexus.get("canonicalDigest") != canonical_digest:
            return BindingResult(BindingDecision.REJECT,
                                 reason="canonical transaction digest mismatch",
                                 findings=["canonical transaction digest mismatch"])
        return BindingResult(BindingDecision.ACCEPT,
                             assurance=self.max_native_assurance,
                             finality=self.native_finality,
                             canonical_digest=canonical_digest,
                             reason="AP4M authority bound to canonical transaction")

    def verify_settlement(self, payload: dict) -> BindingResult:
        findings = self._findings(payload)
        if findings:
            return BindingResult(BindingDecision.REJECT, reason="; ".join(findings),
                                 findings=findings)
        request = self._request(payload)
        digest = self._request_digest(request)
        transaction = self._object(payload.get("transaction"))
        try:
            evidence = self.verifier.verify_settlement(request)
        except Exception as exc:
            reason = f"AP4M settlement verifier unavailable: {type(exc).__name__}"
            return BindingResult(BindingDecision.HALT, reason=reason)
        checks = [
            ("settlement response is unauthenticated", evidence.authenticated),
            ("settlement failed", evidence.success),
            ("settlement lost authority continuity", evidence.authority_continuity_valid),
            ("settlement guarantee is invalid", evidence.settlement_guarantee_valid),
            ("settlement evidence request digest mismatch", evidence.request_digest == digest),
            ("untrusted AP4M verifier", evidence.verifier_id in self.trusted_verifiers),
            ("settlement rail mismatch", evidence.rail == transaction.get("rail")),
            ("settlement currency mismatch", evidence.currency == transaction.get("currency")),
            ("settlement amount mismatch", evidence.amount_minor == transaction.get("amountMinor")),
            ("settlement transaction identifier mismatch",
             evidence.transaction_id == transaction.get("transactionId")),
            ("settlement finality mismatch", evidence.finality is self.native_finality),
        ]
        findings = [message for message, passed in checks if not passed]
        if not evidence.success and evidence.invalid_reason:
            findings.append(evidence.invalid_reason)
        return BindingResult(
            BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
            assurance=(AssuranceLevel.NONE if findings else self.max_native_assurance),
            finality=self.native_finality,
            reason="; ".join(findings) or "authenticated AP4M settlement accepted",
            findings=findings,
        )

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        # Avoid consuming replay state in a metadata query.
        return AssuranceLevel.NONE

    def finality_of(self, payload: dict) -> SettlementFinality:
        findings = self._findings(payload)
        if findings:
            raise ValueError("unsupported AP4M path: " + "; ".join(findings))
        return self.native_finality

    def reconcile(self, payload: dict) -> BindingResult:
        key = payload.get("idempotencyKey")
        if not key or self.status_resolver is None:
            return BindingResult(BindingDecision.HALT,
                                 reason="reconciliation unavailable; do not resubmit")
        try:
            status = self.status_resolver(key)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT,
                                 reason=f"AP4M status unavailable: {type(exc).__name__}")
        if status not in {"settled", "failed", "pending"}:
            return BindingResult(BindingDecision.HALT, reason="unknown AP4M status")
        return BindingResult(BindingDecision.ACCEPT if status in {"settled", "failed"}
                             else BindingDecision.HALT,
                             reason=f"AP4M status: {status}")
