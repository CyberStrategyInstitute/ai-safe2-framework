"""Human Intent Authority: trusted rendering and exact approval evidence."""

from __future__ import annotations

import hashlib
import hmac
import threading
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance
from nexus_sdk.payments.key_guardian import HumanIntentAuthorizationReceipt
from nexus_sdk.payments.objects import CanonicalTransaction, canonical_hash, utcnow

__all__ = [
    "HumanApprovalEvidence",
    "HumanApprovalEvidenceVerifier",
    "HumanIntentAuthorityProfile",
    "InMemoryTestApprovalChallengeStore",
    "InProcessHMACTestHumanApprovalVerifier",
    "TrustedIntentAuthority",
    "TrustedTransactionRendering",
]


@dataclass(frozen=True)
class TrustedTransactionRendering:
    """Non-agent-authored disclosure of the exact transaction being approved."""

    canonical_digest: str
    signing_digest: str
    amount_minor: int
    currency: str
    merchant_id: str
    destination: str | None
    rail: str
    surface_id: str

    @classmethod
    def from_canonical(cls, canonical: CanonicalTransaction, *, surface_id: str):
        return cls(
            canonical_digest=canonical.canonical_digest,
            signing_digest=canonical.signing_digest(),
            amount_minor=canonical.amount.minor_units,
            currency=canonical.amount.currency,
            merchant_id=canonical.merchant_id,
            destination=canonical.destination,
            rail=canonical.rail.value,
            surface_id=surface_id,
        )

    @property
    def rendering_digest(self) -> str:
        return canonical_hash(self.__dict__)


@dataclass(frozen=True)
class HumanApprovalEvidence:
    """Signed trusted-surface response to a single approval challenge."""

    approver_id: str
    action: str
    canonical_digest: str
    signing_digest: str
    rendering_digest: str
    challenge: str
    approved_at: str
    evidence_verifier_id: str
    proof: str


@dataclass(frozen=True)
class HumanIntentAuthorityProfile:
    """Pinned authority identity, surfaces, approvers, and freshness policy."""

    authority_id: str
    authority_version: str
    trusted_surface_ids: frozenset[str]
    authorized_approvers: frozenset[str]
    evidence_trust_digest: str
    max_approval_age_seconds: int = 120

    @property
    def profile_digest(self) -> str:
        return canonical_hash({
            "authority_id": self.authority_id,
            "authority_version": self.authority_version,
            "trusted_surface_ids": sorted(self.trusted_surface_ids),
            "authorized_approvers": sorted(self.authorized_approvers),
            "evidence_trust_digest": self.evidence_trust_digest,
            "max_approval_age_seconds": self.max_approval_age_seconds,
        })


class HumanApprovalEvidenceVerifier(Protocol):
    """Verifier for proof originating at a trusted user-controlled surface."""

    verifier_id: str

    def verify(self, evidence: HumanApprovalEvidence) -> bool: ...


class ApprovalChallengeStore(Protocol):
    """Atomic accept-once store for trusted-surface approval challenges."""

    def consume(self, challenge: str) -> bool: ...


class HumanIntentReceiptIssuer(Protocol):
    authenticator_id: str
    assurance: ComponentAssurance

    def seal_human_intent(self, receipt: HumanIntentAuthorizationReceipt) -> str: ...


class TrustedIntentAuthority:
    """Verify exact human approval without trusting agent-supplied identity claims."""

    human_name = "Human Intent Authority"
    technical_name = "TrustedIntentAuthority"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, profile: HumanIntentAuthorityProfile,
                 evidence_verifier: HumanApprovalEvidenceVerifier,
                 challenge_store: ApprovalChallengeStore,
                 receipt_issuer: HumanIntentReceiptIssuer,
                 now=utcnow) -> None:
        if (
            not profile.authority_id
            or not profile.trusted_surface_ids
            or not profile.authorized_approvers
            or not profile.evidence_trust_digest
            or profile.max_approval_age_seconds <= 0
        ):
            raise ValueError("complete human-intent authority profile is required")
        self.profile = profile
        self.evidence_verifier = evidence_verifier
        self.challenge_store = challenge_store
        self.receipt_issuer = receipt_issuer
        self.now = now

    def authorize(self, canonical: CanonicalTransaction,
                  rendering: TrustedTransactionRendering,
                  evidence: HumanApprovalEvidence) -> HumanIntentAuthorizationReceipt:
        current_time = self.now()
        try:
            approved_at = datetime.fromisoformat(evidence.approved_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("approval timestamp is invalid") from exc
        if approved_at.tzinfo is None or current_time.tzinfo is None:
            raise ValueError("approval timestamp must include a timezone")
        age = (current_time - approved_at).total_seconds()
        bindings = (
            rendering.surface_id in self.profile.trusted_surface_ids,
            rendering.canonical_digest == canonical.canonical_digest,
            rendering.signing_digest == canonical.signing_digest(),
            evidence.action == "approve",
            evidence.approver_id in self.profile.authorized_approvers,
            evidence.canonical_digest == canonical.canonical_digest,
            evidence.signing_digest == canonical.signing_digest(),
            evidence.rendering_digest == rendering.rendering_digest,
            evidence.evidence_verifier_id == self.evidence_verifier.verifier_id,
            0 <= age <= self.profile.max_approval_age_seconds,
            self.evidence_verifier.verify(evidence) is True,
        )
        if not all(bindings):
            raise ValueError("approval is stale, untrusted, or not exactly transaction-bound")
        if not self.challenge_store.consume(evidence.challenge):
            raise ValueError("approval challenge is missing or already consumed")
        receipt = HumanIntentAuthorizationReceipt(
            approval_id="hap_" + canonical_hash({
                "profile": self.profile.profile_digest,
                "approver": evidence.approver_id,
                "signing_digest": canonical.signing_digest(),
                "challenge": evidence.challenge,
            })[:32],
            approver_id=evidence.approver_id,
            canonical_digest=canonical.canonical_digest,
            signing_digest=canonical.signing_digest(),
            rendering_digest=rendering.rendering_digest,
            authority_id=self.profile.authority_id,
            approved_at=approved_at.isoformat(),
            expires_at=(approved_at + timedelta(
                seconds=self.profile.max_approval_age_seconds
            )).isoformat(),
            authenticator_id=self.receipt_issuer.authenticator_id,
            proof="",
            authority_profile_digest=self.profile.profile_digest,
        )
        receipt = replace(receipt, proof=self.receipt_issuer.seal_human_intent(receipt))
        if not receipt.proof:
            raise RuntimeError("human-intent receipt issuer returned no proof")
        return receipt


class InMemoryTestApprovalChallengeStore:
    """TEST ONLY challenge store; production requires durable atomic consumption."""

    def __init__(self, challenges: set[str]) -> None:
        self._challenges = set(challenges)
        self._lock = threading.Lock()

    def consume(self, challenge: str) -> bool:
        with self._lock:
            if challenge not in self._challenges:
                return False
            self._challenges.remove(challenge)
            return True


class InProcessHMACTestHumanApprovalVerifier:
    """TEST ONLY trusted-surface proof verifier."""

    verifier_id = "human-approval-hmac-test"

    def __init__(self, key: bytes = b"human-approval-test-key") -> None:
        self._key = key

    @staticmethod
    def values(evidence: HumanApprovalEvidence) -> str:
        return "|".join((
            evidence.approver_id,
            evidence.action,
            evidence.canonical_digest,
            evidence.signing_digest,
            evidence.rendering_digest,
            evidence.challenge,
            evidence.approved_at,
            evidence.evidence_verifier_id,
        ))

    def seal(self, evidence: HumanApprovalEvidence) -> str:
        return hmac.new(
            self._key, self.values(evidence).encode(), hashlib.sha256
        ).hexdigest()

    def verify(self, evidence: HumanApprovalEvidence) -> bool:
        return hmac.compare_digest(self.seal(evidence), evidence.proof)
