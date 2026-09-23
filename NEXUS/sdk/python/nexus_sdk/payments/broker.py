"""
nexus_sdk/payments/broker.py
Credential broker: isolated signing authority.

Implements APAY-06 (non-exportable signing authority) and the credential-release
half of APAY-05.

THE INVARIANT
    The agent runtime never holds payment key material and never reaches the
    signer directly. The broker accepts one thing - a CanonicalTransaction that
    a deterministic policy engine already approved - and signs exactly that. It
    will not sign an agent-supplied payload, and it re-checks the policy decision
    rather than trusting a caller's assertion that one happened.

    This matters more than the identity layer. Key residency is the difference
    between "an attacker who owns the agent host can propose transactions" and
    "an attacker who owns the agent host can mint valid authorizations". Every
    published agent-payment protocol assumes the signing host is trustworthy;
    none of them require proof of it.

DEFAULT IS REFUSAL
    NullCredentialBroker is the default binding and raises on every call. An
    unconfigured payment path must not move money. Deployments bind an
    HSM, TEE, KMS, managed signer or secure element through this interface.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional

from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    PaymentDecision,
    PaymentReasonCode,
    utcnow,
)

__all__ = [
    "SignedAuthorization",
    "BrokerRefusal",
    "CredentialBroker",
    "NullCredentialBroker",
    "InProcessTestBroker",
]


class BrokerRefusal(RuntimeError):  # noqa: N818 - see docstring
    """The broker declined to sign. Never downgrade this to a warning.

    Named "Refusal" rather than "Error" on purpose, against the usual naming
    convention. This is not a failure to sign; it is a decision not to sign, and
    the distinction governs how callers handle it. Code that treats an "Error"
    as something to retry past is exactly the code that turns a refused payment
    into a completed one.
    """

    def __init__(self, code: PaymentReasonCode, detail: str = ""):
        self.code = code
        super().__init__(f"{code.value}: {detail}" if detail else code.value)


@dataclass
class SignedAuthorization:
    """Proof that an isolated signer authorized one canonical transaction."""
    transaction_intent_id: str
    signing_digest: str
    signature: str
    algorithm: str
    key_id: str
    signer_id: str
    decision_id: str
    revocation_epoch: int
    runtime_measurement_id: str
    signed_at: str = field(default_factory=lambda: utcnow().isoformat())
    authorization_id: str = field(default_factory=lambda: f"auth_{uuid.uuid4().hex[:24]}")

    def to_dict(self) -> dict:
        return {
            "authorization_id": self.authorization_id,
            "transaction_intent_id": self.transaction_intent_id,
            "signing_digest": self.signing_digest,
            "signature": self.signature,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "signer_id": self.signer_id,
            "decision_id": self.decision_id,
            "revocation_epoch": self.revocation_epoch,
            "runtime_measurement_id": self.runtime_measurement_id,
            "signed_at": self.signed_at,
        }


class CredentialBroker(ABC):
    """Interface every signing backend implements.

    Implementations MUST NOT expose key material through any method, MUST sign
    only the CanonicalTransaction passed to them, and MUST refuse when the
    supplied policy decision is anything other than ALLOW.
    """

    signer_id: str = "abstract"
    algorithm: str = "unbound"

    @abstractmethod
    def sign(self, canonical: CanonicalTransaction, *,
             decision: PaymentDecision,
             decision_id: str,
             revocation_epoch_now: Optional[int] = None) -> SignedAuthorization:
        ...

    def _preflight(self, canonical: CanonicalTransaction,
                   decision: PaymentDecision,
                   revocation_epoch_now: Optional[int]) -> None:
        """Checks every implementation runs before touching a key.

        The broker is the last gate before value moves, so it repeats checks
        the firewall already made. Defense in depth here is not redundancy: it
        is the assumption that the caller might be the compromised component.
        """
        if decision is not PaymentDecision.ALLOW:
            raise BrokerRefusal(
                PaymentReasonCode.FAIL_CLOSED_DEFAULT,
                f"policy decision was {decision.value}, not allow",
            )
        if not canonical.canonical_digest:
            raise BrokerRefusal(PaymentReasonCode.INTENT_BINDING_MISSING,
                                "canonical transaction has no bound digest")
        if not canonical.runtime_measurement_id:
            raise BrokerRefusal(PaymentReasonCode.NO_RUNTIME_MEASUREMENT,
                                "credential release requires a runtime measurement reference")
        if revocation_epoch_now is not None and canonical.revocation_epoch < revocation_epoch_now:
            raise BrokerRefusal(PaymentReasonCode.STALE_REVOCATION_EPOCH,
                                "authority was revoked between decision and signing")


class NullCredentialBroker(CredentialBroker):
    """Default binding. Refuses everything.

    Present so that an unconfigured gateway cannot move money. Replacing this
    with a stub that returns a fake signature is the single most damaging
    change anyone can make to this codebase.
    """

    signer_id = "null"
    algorithm = "none"

    def sign(self, canonical: CanonicalTransaction, *,
             decision: PaymentDecision, decision_id: str,
             revocation_epoch_now: Optional[int] = None) -> SignedAuthorization:
        raise BrokerRefusal(
            PaymentReasonCode.FAIL_CLOSED_DEFAULT,
            "no credential broker is bound; configure an HSM, TEE, KMS or managed signer",
        )


class InProcessTestBroker(CredentialBroker):
    """TEST ONLY. HMAC over the canonical digest, key held in this process.

    This exists to exercise the broker contract in the test suite and the
    Challenge Lab. It is NOT an acceptable production binding: the key lives in
    the same memory as the caller, which is exactly the property APAY-06
    forbids. Production bindings put the key somewhere the agent process cannot
    read even when fully compromised.

    `refuse_unless` lets a deployment or an experiment install an additional
    predicate the broker must satisfy before signing.
    """

    signer_id = "in-process-test"
    algorithm = "HMAC-SHA256-TEST"

    def __init__(self, key: Optional[bytes] = None, *, key_id: str = "test-key-1",
                 refuse_unless: Optional[Callable[[CanonicalTransaction], bool]] = None) -> None:
        self._key = key or os.urandom(32)
        self.key_id = key_id
        self._refuse_unless = refuse_unless
        self._signed: dict[str, str] = {}
        self._lock = threading.RLock()

    def sign(self, canonical: CanonicalTransaction, *,
             decision: PaymentDecision, decision_id: str,
             revocation_epoch_now: Optional[int] = None) -> SignedAuthorization:
        self._preflight(canonical, decision, revocation_epoch_now)
        if self._refuse_unless is not None and not self._refuse_unless(canonical):
            raise BrokerRefusal(PaymentReasonCode.FAIL_CLOSED_DEFAULT,
                                "broker-side predicate refused this transaction")

        digest = canonical.signing_digest()
        with self._lock:
            # APAY-16: one canonical transaction, one signature. A second
            # signature over the same idempotency key with a different digest
            # is a double-authorization, not a retry.
            prior = self._signed.get(canonical.idempotency_key)
            if prior is not None and prior != digest:
                raise BrokerRefusal(PaymentReasonCode.REPLAY_DETECTED,
                                    "idempotency key already signed with different terms")
            self._signed[canonical.idempotency_key] = digest

        signature = hmac.new(self._key, digest.encode(), hashlib.sha256).hexdigest()
        return SignedAuthorization(
            transaction_intent_id=canonical.transaction_intent_id,
            signing_digest=digest,
            signature=signature,
            algorithm=self.algorithm,
            key_id=self.key_id,
            signer_id=self.signer_id,
            decision_id=decision_id,
            revocation_epoch=canonical.revocation_epoch,
            runtime_measurement_id=canonical.runtime_measurement_id,
        )

    def verify(self, authorization: SignedAuthorization) -> bool:
        expected = hmac.new(self._key, authorization.signing_digest.encode(),
                            hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, authorization.signature)
