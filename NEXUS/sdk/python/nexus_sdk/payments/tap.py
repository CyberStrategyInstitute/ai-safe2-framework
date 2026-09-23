"""Card Trust Bridge: Visa TAP request-recognition profile."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Protocol

from nexus_sdk.payments.adapters import BindingDecision, BindingResult, RailBinding
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality


@dataclass(frozen=True)
class TAPVerificationEvidence:
    """Authenticated evidence from a deterministic RFC 9421/TAP verifier."""

    valid: bool
    verifier_id: str
    request_digest: str
    authenticated: bool = False
    signature_valid: bool = False
    covered_components_valid: bool = False
    freshness_valid: bool = False
    replay_safe: bool = False
    key_trusted: bool = False
    discovery_ssrf_safe: bool = False
    payment_container_valid: bool = False
    invalid_reason: Optional[str] = None


class TAPAuthoritativeVerifier(Protocol):
    """Trusted verifier boundary; implementations own crypto and key discovery."""

    def verify(self, request: dict) -> TAPVerificationEvidence: ...


class VisaTAPBinding(RailBinding):
    """Card Trust Bridge (`VisaTAPBinding`) for Visa TAP payment requests."""

    human_name = "Card Trust Bridge"
    technical_name = "VisaTAPBinding"
    protocol = "visa-tap"
    # Visa's public Merchant Specification exposes no formal version identifier.
    protocol_version = "merchant-spec@2026-09-22"
    scheme = "rfc9421"
    payment_flow = "agent-payer-auth"
    native_finality = SettlementFinality.REVERSIBLE
    authoritative_verification = True
    max_native_assurance = AssuranceLevel.SIGNED_REQUEST

    def __init__(self, *, verifier: TAPAuthoritativeVerifier,
                 trusted_verifiers: set[str], authorities: set[str],
                 algorithms: set[str], payment_container_types: set[str],
                 status_resolver=None):
        self.verifier = verifier
        self.trusted_verifiers = set(trusted_verifiers)
        self.networks = set(authorities)
        self.assets = set(payment_container_types)
        self.algorithms = set(algorithms)
        self.status_resolver = status_resolver

    @staticmethod
    def _request(payload: dict) -> dict:
        return {
            key: payload.get(key) for key in (
                "tapVersion", "method", "authority", "path", "headers",
                "signatureInput", "signature", "agenticPaymentContainer",
                "extensions",
            ) if key in payload
        }

    @staticmethod
    def _request_digest(request: dict) -> str:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _object(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    def _findings(self, payload: dict) -> list[str]:
        findings: list[str] = []
        if payload.get("tapVersion") != self.protocol_version:
            findings.append("unsupported or unpinned TAP specification snapshot")
        method = payload.get("method")
        authority = payload.get("authority")
        path = payload.get("path")
        if not isinstance(method, str) or method.upper() != "POST":
            findings.append("payment recognition requires POST")
        if not isinstance(authority, str) or authority not in self.networks:
            findings.append("request authority is not allowlisted")
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            findings.append("request path is not a canonical origin path")
        signature_input = self._object(payload.get("signatureInput"))
        if signature_input.get("tag") != "agent-payer-auth":
            findings.append("signature tag is not agent-payer-auth")
        components = signature_input.get("coveredComponents")
        required = {"@method", "@authority", "@path", "content-digest"}
        if (not isinstance(components, list)
                or not all(isinstance(item, str) for item in components)
                or not required.issubset(components)):
            findings.append("signature omits required request components")
        for name in ("created", "expires"):
            value = signature_input.get(name)
            if isinstance(value, bool) or not isinstance(value, int):
                findings.append(f"signature {name} must be an integer timestamp")
        if (isinstance(signature_input.get("created"), int)
                and isinstance(signature_input.get("expires"), int)
                and signature_input["expires"] <= signature_input["created"]):
            findings.append("signature expiry must follow creation")
        nonce = signature_input.get("nonce")
        key_id = signature_input.get("keyid")
        algorithm = signature_input.get("alg")
        if not isinstance(nonce, str) or not nonce:
            findings.append("signature nonce is required")
        if not isinstance(key_id, str) or not key_id:
            findings.append("signature keyid is required")
        if not isinstance(algorithm, str) or algorithm not in self.algorithms:
            findings.append("signature algorithm is not allowlisted")
        if not isinstance(payload.get("signature"), str) or not payload.get("signature"):
            findings.append("HTTP message signature is required")
        headers = self._object(payload.get("headers"))
        if not isinstance(headers.get("content-digest"), str):
            findings.append("content-digest header is required")
        container = self._object(payload.get("agenticPaymentContainer"))
        for name in ("nonce", "kid", "alg", "signature", "type"):
            if container.get(name) in (None, ""):
                findings.append(f"payment container {name} is required")
        if container.get("nonce") != nonce:
            findings.append("payment container nonce does not match message signature")
        if container.get("kid") != key_id:
            findings.append("payment container key does not match message signature")
        if container.get("alg") != algorithm:
            findings.append("payment container algorithm does not match message signature")
        container_type = container.get("type")
        if not isinstance(container_type, str) or container_type not in self.assets:
            findings.append("payment container type is not allowlisted")
        extensions = self._object(payload.get("extensions"))
        nexus = self._object(extensions.get("nexus"))
        for name in ("authorityGrantDigest", "revocationEpoch", "nonce", "expiresAt"):
            if nexus.get(name) in (None, ""):
                findings.append(f"missing nexus.{name}")
        return findings

    def support_tuple_of(self, payload: dict) -> dict[str, str]:
        container = self._object(payload.get("agenticPaymentContainer"))
        signature_input = self._object(payload.get("signatureInput"))
        return {
            "protocol_version": str(payload.get("tapVersion", "")),
            "scheme": self.scheme,
            "network": str(payload.get("authority", "")),
            "asset": str(container.get("type", "")),
            "payment_flow": str(signature_input.get("tag", "")),
        }

    def verify_authority(self, payload: dict) -> BindingResult:
        findings = self._findings(payload)
        if findings:
            return BindingResult(BindingDecision.REJECT, reason="; ".join(findings),
                                 findings=findings)
        request = self._request(payload)
        digest = self._request_digest(request)
        try:
            evidence = self.verifier.verify(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT,
                                 reason=f"TAP verifier unavailable: {type(exc).__name__}")
        if not isinstance(evidence, TAPVerificationEvidence):
            return BindingResult(BindingDecision.HALT,
                                 reason="TAP verifier returned malformed evidence")
        rejection_reason = (evidence.invalid_reason
                            if isinstance(evidence.invalid_reason, str)
                            and evidence.invalid_reason
                            else "TAP verifier rejected request")
        checks = [
            ("verification response is unauthenticated", evidence.authenticated is True),
            ("HTTP message signature is invalid", evidence.signature_valid is True),
            ("signed request components do not match",
             evidence.covered_components_valid is True),
            ("signature freshness check failed", evidence.freshness_valid is True),
            ("nonce replay/relay check failed", evidence.replay_safe is True),
            ("agent key is not trusted", evidence.key_trusted is True),
            ("key discovery did not enforce SSRF controls",
             evidence.discovery_ssrf_safe is True),
            ("payment container signature or binding is invalid",
             evidence.payment_container_valid is True),
            ("verification evidence request digest mismatch",
             isinstance(evidence.request_digest, str)
             and evidence.request_digest == digest),
            ("untrusted TAP verifier", isinstance(evidence.verifier_id, str)
             and evidence.verifier_id in self.trusted_verifiers),
            (rejection_reason, evidence.valid is True),
        ]
        findings = [message for message, passed in checks if not passed]
        return BindingResult(
            BindingDecision.REJECT if findings else BindingDecision.ACCEPT,
            assurance=(AssuranceLevel.NONE if findings else self.max_native_assurance),
            finality=self.native_finality,
            reason="; ".join(findings) or "authenticated TAP request accepted",
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
                             reason="TAP request bound to canonical transaction")

    def assurance_of(self, payload: dict) -> AssuranceLevel:
        # This query must not consume replay state. Callers obtain the verified
        # assurance from verify_authority/bind_transaction's BindingResult.
        return AssuranceLevel.NONE

    def finality_of(self, payload: dict) -> SettlementFinality:
        findings = self._findings(payload)
        if findings:
            raise ValueError("unsupported TAP path: " + "; ".join(findings))
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
                                 reason=f"merchant status unavailable: {type(exc).__name__}")
        if status not in {"authorized", "declined", "pending"}:
            return BindingResult(BindingDecision.HALT, reason="unknown merchant status")
        return BindingResult(BindingDecision.ACCEPT if status in {"authorized", "declined"}
                             else BindingDecision.HALT,
                             reason=f"merchant status: {status}")
