"""Mandate Bridge: a narrow authoritative AP2 v0.2 binding."""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol

from nexus_sdk.payments.adapters import BindingDecision, BindingResult, RailBinding
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality


@dataclass(frozen=True)
class AP2VerificationEvidence:
    """Authenticated result from deterministic SD-JWT/JWS verification."""

    valid: bool
    verifier_id: str
    request_digest: str
    authenticated: bool = False
    signatures_valid: bool = False
    constraints_valid: bool = False
    key_confirmation_valid: bool = False
    replay_safe: bool = False
    merchant_checkout_jwt_valid: bool = False
    invalid_reason: Optional[str] = None


@dataclass(frozen=True)
class AP2ReceiptEvidence:
    """Authenticated receipt-chain verification result."""

    valid: bool
    verifier_id: str
    request_digest: str
    authenticated: bool = False
    checkout_reference_valid: bool = False
    payment_reference_valid: bool = False
    receipts_signed: bool = False
    invalid_reason: Optional[str] = None


class AP2AuthoritativeVerifier(Protocol):
    """Trusted deterministic verifier boundary; an LLM cannot implement it."""

    def verify(self, request: dict) -> AP2VerificationEvidence: ...

    def verify_receipts(self, request: dict) -> AP2ReceiptEvidence: ...


class AP2V02Binding(RailBinding):
    """Mandate Bridge (`AP2V02Binding`) for one AP2 v0.2 mode and audience."""

    human_name = "Mandate Bridge"
    technical_name = "AP2V02Binding"
    protocol = "ap2"
    protocol_version = "0.2"
    scheme = "sd-jwt"
    native_finality = SettlementFinality.REVERSIBLE
    authoritative_verification = True
    max_native_assurance = AssuranceLevel.MANDATE_BOUND

    def __init__(self, *, verifier: AP2AuthoritativeVerifier,
                 trusted_verifiers: set[str], audiences: set[str],
                 currencies: set[str], mode: str,
                 status_resolver=None, now=None):
        if mode not in {"direct", "autonomous"}:
            raise ValueError("mode must be direct or autonomous")
        self.verifier = verifier
        self.trusted_verifiers = set(trusted_verifiers)
        self.networks = set(audiences)
        self.assets = set(currencies)
        self.payment_flow = mode
        self.status_resolver = status_resolver
        self._now = now or (lambda: datetime.now(timezone.utc).timestamp())

    @staticmethod
    def _request(payload: dict) -> dict:
        return {
            key: payload.get(key) for key in (
                "ap2Version", "mode", "checkoutMandate", "paymentMandate",
                "openCheckoutMandate", "openPaymentMandate", "disclosures",
                "extensions",
            ) if key in payload
        }

    @staticmethod
    def _request_digest(request: dict) -> str:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _checkout_hash(checkout_jwt: str) -> str:
        digest = hashlib.sha256(checkout_jwt.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def _structural_findings(self, payload: dict) -> list[str]:
        findings: list[str] = []
        if payload.get("ap2Version") != "0.2":
            findings.append("unsupported AP2 version")
        if payload.get("mode") != self.payment_flow:
            findings.append("AP2 mode differs from configured profile")
        checkout = payload.get("checkoutMandate")
        payment = payload.get("paymentMandate")
        if not isinstance(checkout, dict) or not isinstance(payment, dict):
            return findings + ["closed Checkout and Payment Mandates are required"]
        if checkout.get("vct") != "mandate.checkout.1":
            findings.append("unsupported Checkout Mandate vct")
        if payment.get("vct") != "mandate.payment.1":
            findings.append("unsupported Payment Mandate vct")
        checkout_jwt = checkout.get("checkout_jwt")
        if not isinstance(checkout_jwt, str) or not checkout_jwt:
            findings.append("merchant-signed checkout_jwt is required")
        else:
            expected = self._checkout_hash(checkout_jwt)
            if checkout.get("checkout_hash") != expected:
                findings.append("Checkout Mandate hash does not bind checkout_jwt")
            if payment.get("transaction_id") != expected:
                findings.append("Payment Mandate is not bound to checkout_jwt")
        audience = payment.get("aud")
        if not isinstance(audience, str) or audience not in self.networks:
            findings.append("Payment Mandate audience is not allowlisted")
        amount = payment.get("payment_amount")
        if not isinstance(amount, dict):
            findings.append("payment_amount is required")
        else:
            currency, value = amount.get("currency"), amount.get("amount")
            if currency not in self.assets:
                findings.append("payment currency is not allowlisted")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                findings.append("payment amount must be a non-negative integer in minor units")
        now = self._now()
        for label, mandate in (("Checkout", checkout), ("Payment", payment)):
            exp = mandate.get("exp")
            if isinstance(exp, bool) or not isinstance(exp, int) or exp <= now:
                findings.append(f"{label} Mandate is expired or lacks a valid exp")
            if not isinstance(mandate.get("iss"), str) or not mandate.get("iss"):
                findings.append(f"{label} Mandate issuer is required")
        extensions = payload.get("extensions")
        if not isinstance(extensions, dict):
            findings.append("extensions must be an object")
            nexus: dict = {}
        else:
            supplied_nexus = extensions.get("nexus")
            if not isinstance(supplied_nexus, dict):
                findings.append("extensions.nexus must be an object")
                nexus = {}
            else:
                nexus = supplied_nexus
        for claim in ("authorityGrantDigest", "revocationEpoch", "nonce", "expiresAt"):
            if nexus.get(claim) in (None, ""):
                findings.append(f"missing nexus.{claim}")
        try:
            expires = datetime.fromisoformat(
                str(nexus.get("expiresAt", "")).replace("Z", "+00:00")
            )
            if expires.tzinfo is None or expires.utcoffset() is None:
                raise ValueError("timezone required")
            if expires.timestamp() <= now:
                findings.append("NEXUS authority binding expired")
        except ValueError:
            findings.append("invalid nexus.expiresAt")
        if self.payment_flow == "autonomous":
            open_checkout = payload.get("openCheckoutMandate")
            open_payment = payload.get("openPaymentMandate")
            if (not isinstance(open_checkout, dict)
                    or open_checkout.get("vct") != "mandate.checkout.open.1"):
                findings.append("autonomous flow requires exact-version open Checkout Mandate")
            if (not isinstance(open_payment, dict)
                    or open_payment.get("vct") != "mandate.payment.open.1"):
                findings.append("autonomous flow requires exact-version open Payment Mandate")
            mandate_pairs: tuple[tuple[str, object], ...] = (
                ("Checkout", open_checkout), ("Payment", open_payment),
            )
            for label, open_mandate in mandate_pairs:
                if (isinstance(open_mandate, dict)
                        and not isinstance(open_mandate.get("cnf"), dict)):
                    findings.append(f"open {label} Mandate lacks agent key confirmation")
            if not isinstance(payload.get("disclosures"), list):
                findings.append("autonomous flow requires explicit selective disclosures")
        return findings

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        supplied_payment = payload.get("paymentMandate")
        payment = supplied_payment if isinstance(supplied_payment, dict) else {}
        supplied_amount = payment.get("payment_amount")
        amount = supplied_amount if isinstance(supplied_amount, dict) else {}
        return {
            "protocol_version": str(payload.get("ap2Version", "")),
            "scheme": self.scheme,
            "network": str(payment.get("aud", "")),
            "asset": str(amount.get("currency", "")),
            "payment_flow": str(payload.get("mode", "")),
        }

    def verify_authority(self, payload: dict) -> BindingResult:
        findings = self._structural_findings(payload)
        if findings:
            return BindingResult(BindingDecision.REJECT, reason="; ".join(findings),
                                 findings=findings)
        request = self._request(payload)
        try:
            evidence = self.verifier.verify(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT,
                                 reason=f"AP2 verifier unavailable: {type(exc).__name__}")
        if not isinstance(evidence, AP2VerificationEvidence):
            return BindingResult(BindingDecision.HALT,
                                 reason="AP2 verifier returned malformed evidence")
        rejection_reason = (evidence.invalid_reason
                            if isinstance(evidence.invalid_reason, str)
                            and evidence.invalid_reason
                            else "AP2 verifier rejected mandates")
        checks = [
            ("verification response is unauthenticated", evidence.authenticated is True),
            ("mandate signatures are invalid", evidence.signatures_valid is True),
            ("mandate constraints are invalid", evidence.constraints_valid is True),
            ("key confirmation is invalid", evidence.key_confirmation_valid is True),
            ("mandate replay/single-use check failed", evidence.replay_safe is True),
            ("merchant checkout JWT is invalid or uses an unsupported signature",
             evidence.merchant_checkout_jwt_valid is True),
            ("verification evidence request digest mismatch",
             isinstance(evidence.request_digest, str)
             and evidence.request_digest == self._request_digest(request)),
            ("untrusted AP2 verifier", isinstance(evidence.verifier_id, str)
             and evidence.verifier_id in self.trusted_verifiers),
            (rejection_reason, evidence.valid is True),
        ]
        findings = [message for message, ok in checks if not ok]
        return BindingResult(BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
                             assurance=(self.max_native_assurance if not findings
                                        else AssuranceLevel.NONE),
                             finality=self.native_finality,
                             reason="; ".join(findings) or "authenticated AP2 mandates accepted",
                             findings=findings)

    def bind_transaction(self, payload: dict, canonical_digest: str) -> BindingResult:
        extensions = payload.get("extensions")
        nexus = extensions.get("nexus") if isinstance(extensions, dict) else None
        bound = nexus.get("canonicalDigest") if isinstance(nexus, dict) else None
        if bound != canonical_digest:
            return BindingResult(BindingDecision.REJECT,
                                 reason="canonical transaction digest mismatch",
                                 findings=["canonical transaction digest mismatch"])
        authority = self.verify_authority(payload)
        if authority.decision is not BindingDecision.ACCEPT:
            return authority
        return BindingResult(BindingDecision.ACCEPT,
                             assurance=self.max_native_assurance,
                             finality=self.native_finality,
                             canonical_digest=canonical_digest,
                             reason="AP2 mandates bound to canonical transaction")

    def verify_receipts(self, payload: dict) -> BindingResult:
        authority = self.verify_authority(payload)
        if authority.decision is not BindingDecision.ACCEPT:
            return BindingResult(
                authority.decision,
                assurance=AssuranceLevel.NONE,
                finality=self.native_finality,
                reason="receipt verification refused because mandate validation failed: "
                + authority.reason,
                findings=list(authority.findings),
            )
        receipts = payload.get("receipts")
        if (not isinstance(receipts, dict) or not receipts.get("checkout")
                or not receipts.get("payment")):
            return BindingResult(BindingDecision.REJECT,
                                 reason="signed Checkout and Payment Receipts are required")
        request = {"mandates": self._request(payload), "receipts": receipts}
        try:
            evidence = self.verifier.verify_receipts(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT,
                                 reason=f"AP2 receipt verifier unavailable: {type(exc).__name__}")
        if not isinstance(evidence, AP2ReceiptEvidence):
            return BindingResult(BindingDecision.HALT,
                                 reason="AP2 verifier returned malformed receipt evidence")
        ok = (evidence.valid is True and evidence.authenticated is True
              and evidence.receipts_signed is True
              and evidence.checkout_reference_valid is True
              and evidence.payment_reference_valid is True
              and isinstance(evidence.verifier_id, str)
              and evidence.verifier_id in self.trusted_verifiers
              and isinstance(evidence.request_digest, str)
              and evidence.request_digest == self._request_digest(request))
        return BindingResult(BindingDecision.ACCEPT if ok else BindingDecision.REJECT,
                             assurance=self.max_native_assurance if ok else AssuranceLevel.NONE,
                             finality=self.native_finality,
                             reason="authenticated AP2 receipt chain accepted" if ok
                             else (evidence.invalid_reason
                                   if isinstance(evidence.invalid_reason, str)
                                   and evidence.invalid_reason
                                   else "AP2 receipt evidence rejected"))

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        # Metadata queries must not consume a single-use mandate or replay nonce.
        return AssuranceLevel.NONE

    def finality_of(self, payload: dict) -> SettlementFinality:
        findings = self._structural_findings(payload)
        if findings:
            raise ValueError("unsupported AP2 path: " + "; ".join(findings))
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
                                 reason=f"receipt status unavailable: {type(exc).__name__}")
        if status not in {"success", "error", "pending"}:
            return BindingResult(BindingDecision.HALT, reason="unknown receipt status")
        return BindingResult(BindingDecision.ACCEPT if status in {"success", "error"}
                             else BindingDecision.HALT,
                             reason=f"AP2 receipt status: {status}")
