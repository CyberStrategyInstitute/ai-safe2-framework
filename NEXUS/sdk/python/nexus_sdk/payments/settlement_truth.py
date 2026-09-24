"""Settlement Truth Authority: authenticated observation and retry discipline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from nexus_sdk.payments.broker import SignedAuthorization
from nexus_sdk.payments.execution_plane import (
    ComponentAssurance,
    ReplayDecision,
    TransactionalReplayStore,
)
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    PaymentRail,
    SettlementFinality,
    canonical_hash,
    utcnow,
)

__all__ = [
    "AuthoritativeSettlementObserver",
    "RailSettlementEvidence",
    "RetryDirective",
    "SettlementEvidenceVerifier",
    "SettlementObservation",
    "SettlementObserverProfile",
    "SettlementTruth",
]


class SettlementTruth(str, Enum):
    SETTLED = "settled"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"


class RetryDirective(str, Enum):
    NEVER = "never"
    RECONCILE = "reconcile"
    NEW_AUTHORIZATION_REQUIRED = "new_authorization_required"


@dataclass(frozen=True)
class RailSettlementEvidence:
    """Authenticated rail observation bound to the submitted authorization."""

    authorization_id: str
    signing_digest: str
    rail: PaymentRail
    status: str
    settlement_id: str | None
    amount_minor: int
    currency: str
    destination: str | None
    confirmations: int
    finality: SettlementFinality
    observed_at: str
    observer_id: str
    proof: str

    @property
    def evidence_digest(self) -> str:
        values = dict(self.__dict__)
        values["rail"] = self.rail.value
        values["finality"] = self.finality.value
        values.pop("proof")
        return canonical_hash(values)


@dataclass(frozen=True)
class SettlementObserverProfile:
    """Pinned observer identity, rail scope, finality, and freshness rules."""

    observer_id: str
    observer_version: str
    evidence_trust_digest: str
    minimum_confirmations: tuple[tuple[PaymentRail, int], ...]
    max_observation_age_seconds: int = 300

    @property
    def profile_digest(self) -> str:
        return canonical_hash({
            "observer_id": self.observer_id,
            "observer_version": self.observer_version,
            "evidence_trust_digest": self.evidence_trust_digest,
            "minimum_confirmations": sorted(
                (rail.value, count) for rail, count in self.minimum_confirmations
            ),
            "max_observation_age_seconds": self.max_observation_age_seconds,
        })

    def confirmations_for(self, rail: PaymentRail) -> int | None:
        return dict(self.minimum_confirmations).get(rail)


class SettlementEvidenceVerifier(Protocol):
    def verify(self, evidence: RailSettlementEvidence) -> bool: ...


@dataclass(frozen=True)
class SettlementObservation:
    """Durably idempotent truth classification for one authorization."""

    authorization_id: str
    truth: SettlementTruth
    retry: RetryDirective
    evidence_digest: str
    observer_id: str
    observer_profile_digest: str
    observed_at: str
    settlement_id: str | None = None
    reason: str = ""

    @property
    def observation_digest(self) -> str:
        values = dict(self.__dict__)
        values["truth"] = self.truth.value
        values["retry"] = self.retry.value
        return canonical_hash(values)


class AuthoritativeSettlementObserver:
    """Independently classify settlement without trusting agent or callback claims."""

    human_name = "Settlement Truth Authority"
    technical_name = "AuthoritativeSettlementObserver"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, profile: SettlementObserverProfile,
                 evidence_verifier: SettlementEvidenceVerifier,
                 replay_store: TransactionalReplayStore,
                 now=utcnow) -> None:
        if (
            not profile.observer_id
            or not profile.evidence_trust_digest
            or not profile.minimum_confirmations
            or profile.max_observation_age_seconds <= 0
            or any(count < 0 for _, count in profile.minimum_confirmations)
        ):
            raise ValueError("complete settlement observer profile is required")
        self.profile = profile
        self.evidence_verifier = evidence_verifier
        self.replay_store = replay_store
        self.now = now

    def observe(self, canonical: CanonicalTransaction,
                authorization: SignedAuthorization,
                evidence: RailSettlementEvidence) -> SettlementObservation:
        current_time = self.now()
        try:
            observed_at = datetime.fromisoformat(evidence.observed_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("settlement observation timestamp is invalid") from exc
        if observed_at.tzinfo is None or current_time.tzinfo is None:
            raise ValueError("settlement observation timestamp must include a timezone")
        age = (current_time - observed_at).total_seconds()
        minimum_confirmations = self.profile.confirmations_for(canonical.rail)
        bindings = (
            authorization.transaction_intent_id == canonical.transaction_intent_id,
            authorization.signing_digest == canonical.signing_digest(),
            evidence.authorization_id == authorization.authorization_id,
            evidence.signing_digest == authorization.signing_digest,
            evidence.rail is canonical.rail,
            evidence.amount_minor == canonical.amount.minor_units,
            evidence.currency == canonical.amount.currency,
            evidence.destination == canonical.destination,
            evidence.finality is canonical.finality,
            evidence.observer_id == self.profile.observer_id,
            minimum_confirmations is not None,
            0 <= age <= self.profile.max_observation_age_seconds,
            self.evidence_verifier.verify(evidence) is True,
        )
        if not all(bindings):
            raise ValueError("settlement evidence is stale, untrusted, or not authorization-bound")

        truth, retry, reason = self._classify(evidence, minimum_confirmations or 0)
        observation = SettlementObservation(
            authorization_id=authorization.authorization_id,
            truth=truth,
            retry=retry,
            evidence_digest=evidence.evidence_digest,
            observer_id=self.profile.observer_id,
            observer_profile_digest=self.profile.profile_digest,
            observed_at=observed_at.isoformat(),
            settlement_id=evidence.settlement_id,
            reason=reason,
        )
        if observation.truth is not SettlementTruth.AMBIGUOUS:
            replay = self.replay_store.consume(
                namespace="settlement-terminal-truth",
                key=authorization.authorization_id,
                digest=observation.observation_digest,
            )
            if replay is ReplayDecision.CONFLICT:
                raise ValueError("conflicting terminal truth exists for this authorization")
        return observation

    @staticmethod
    def _classify(evidence: RailSettlementEvidence,
                  minimum_confirmations: int) -> tuple[SettlementTruth, RetryDirective, str]:
        if evidence.status == "settled":
            if not evidence.settlement_id:
                return SettlementTruth.AMBIGUOUS, RetryDirective.RECONCILE, "missing settlement id"
            if evidence.confirmations < minimum_confirmations:
                return (
                    SettlementTruth.AMBIGUOUS,
                    RetryDirective.RECONCILE,
                    "settlement has insufficient finality evidence",
                )
            return SettlementTruth.SETTLED, RetryDirective.NEVER, "authoritative settlement observed"
        if evidence.status == "failed" and not evidence.settlement_id:
            return (
                SettlementTruth.FAILED,
                RetryDirective.NEW_AUTHORIZATION_REQUIRED,
                "authoritative failure observed",
            )
        return SettlementTruth.AMBIGUOUS, RetryDirective.RECONCILE, "settlement outcome is uncertain"
