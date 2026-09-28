"""Key Guardian: isolated credential-release contracts and reference verifier.

The agent-facing process constructs a bound release envelope.  A separately
deployed guardian independently verifies that envelope before invoking a
non-exportable signing backend.  No interface in this module returns key
material or accepts arbitrary bytes from an agent.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn, Protocol

from nexus_sdk.payments.broker import BrokerRefusal, SignedAuthorization
from nexus_sdk.payments.execution_plane import (
    ComponentAssurance,
    CredentialReleaseStateStore,
    ExecutionRecord,
    ExecutionState,
    ReplayDecision,
)
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    PaymentDecision,
    PaymentReasonCode,
    utcnow,
)

__all__ = [
    "CredentialReleaseEnvelope",
    "HumanIntentAuthorizationReceipt",
    "InProcessHMACTestBackend",
    "KeyGuardianClient",
    "KeyGuardianTransport",
    "NullKeyGuardianTransport",
    "PolicyAuthorizationReceipt",
    "ProtectedSigningBackend",
    "ReceiptAuthenticator",
    "InProcessHMACReceiptAuthenticator",
    "ReferenceKeyGuardianService",
    "RuntimeAuthorizationReceipt",
]


@dataclass(frozen=True)
class PolicyAuthorizationReceipt:
    """Deterministic policy evidence bound to one canonical intent."""

    decision_id: str
    decision: PaymentDecision
    canonical_digest: str
    signing_digest: str
    policy_id: str
    evaluated_at: str
    authenticator_id: str
    proof: str
    policy_digest: str = ""
    human_approval_required: bool = False


@dataclass(frozen=True)
class HumanIntentAuthorizationReceipt:
    """Authenticated proof that the trusted surface captured exact approval."""

    approval_id: str
    approver_id: str
    canonical_digest: str
    signing_digest: str
    rendering_digest: str
    authority_id: str
    approved_at: str
    expires_at: str
    authenticator_id: str
    proof: str
    authority_profile_digest: str = ""


@dataclass(frozen=True)
class RuntimeAuthorizationReceipt:
    """Independent runtime-verifier evidence bound to one canonical intent."""

    runtime_measurement_id: str
    canonical_digest: str
    signing_digest: str
    verifier_id: str
    accepted: bool
    verified_at: str
    authenticator_id: str
    proof: str
    verifier_profile_digest: str = ""


@dataclass(frozen=True)
class CredentialReleaseEnvelope:
    """The only request a Key Guardian transport may accept."""

    execution: ExecutionRecord
    canonical: CanonicalTransaction
    policy: PolicyAuthorizationReceipt
    runtime: RuntimeAuthorizationReceipt
    observed_revocation_epoch: int
    human_intent: HumanIntentAuthorizationReceipt | None = None


class ProtectedSigningBackend(Protocol):
    """Non-exportable signing backend owned by the guardian process."""

    signer_id: str
    key_id: str
    algorithm: str
    assurance: ComponentAssurance

    def sign_digest(self, digest: str) -> str: ...


class ReceiptAuthenticator(Protocol):
    """Guardian-owned verifier for policy and runtime receipt proofs."""

    assurance: ComponentAssurance

    def verify_policy(self, receipt: PolicyAuthorizationReceipt) -> bool: ...
    def verify_runtime(self, receipt: RuntimeAuthorizationReceipt) -> bool: ...
    def verify_human_intent(self, receipt: HumanIntentAuthorizationReceipt) -> bool: ...


class KeyGuardianTransport(Protocol):
    """Transport to a separately deployed guardian trust boundary."""

    assurance: ComponentAssurance

    def release(self, envelope: CredentialReleaseEnvelope) -> SignedAuthorization: ...


class NullKeyGuardianTransport:
    """Fail-closed default for deployments with no isolated guardian."""

    assurance = ComponentAssurance.UNBOUND

    def release(self, envelope: CredentialReleaseEnvelope) -> SignedAuthorization:
        raise BrokerRefusal(
            PaymentReasonCode.FAIL_CLOSED_DEFAULT,
            "no isolated Key Guardian transport is configured",
        )


class KeyGuardianClient:
    """Agent-side client; contains no key and performs no signing."""

    human_name = "Key Guardian"
    technical_name = "KeyGuardianClient"

    def __init__(self, transport: KeyGuardianTransport | None = None) -> None:
        self.transport = transport or NullKeyGuardianTransport()

    @property
    def assurance(self) -> ComponentAssurance:
        return self.transport.assurance

    def release(self, envelope: CredentialReleaseEnvelope) -> SignedAuthorization:
        return self.transport.release(envelope)


class ReferenceKeyGuardianService:
    """Signer-side reference verifier.

    This service is suitable for conformance and boundary testing.  Deployment
    assurance additionally requires a separate process, authenticated transport,
    a protected backend, and durable idempotent authorization retrieval.
    """

    human_name = "Key Guardian Service"
    technical_name = "ReferenceKeyGuardianService"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, backend: ProtectedSigningBackend,
                 state_store: CredentialReleaseStateStore,
                 receipt_authenticator: ReceiptAuthenticator,
                 trusted_policy_digests: Mapping[str, str],
                 trusted_runtime_verifier_digests: Mapping[str, str],
                 trusted_human_authority_digests: Mapping[str, str],
                 revocation_epoch: Callable[[str], int],
                 now: Callable[[], datetime] = utcnow,
                 max_receipt_age_seconds: int = 120) -> None:
        self.backend = backend
        self.state_store = state_store
        self.receipt_authenticator = receipt_authenticator
        self.trusted_policy_digests = dict(trusted_policy_digests)
        self.trusted_runtime_verifier_digests = dict(trusted_runtime_verifier_digests)
        self.trusted_human_authority_digests = dict(trusted_human_authority_digests)
        self.revocation_epoch = revocation_epoch
        self.now = now
        self.max_receipt_age_seconds = max_receipt_age_seconds

    @staticmethod
    def _refuse(code: PaymentReasonCode, detail: str) -> NoReturn:
        raise BrokerRefusal(code, detail)

    def _verify(self, envelope: CredentialReleaseEnvelope) -> str:
        execution = envelope.execution
        canonical = envelope.canonical
        policy = envelope.policy
        runtime = envelope.runtime
        signing_digest = canonical.signing_digest()

        try:
            policy_time = datetime.fromisoformat(policy.evaluated_at)
            runtime_time = datetime.fromisoformat(runtime.verified_at)
            current_time = self.now()
            policy_age = (current_time - policy_time).total_seconds()
            runtime_age = (current_time - runtime_time).total_seconds()
        except (TypeError, ValueError):
            self._refuse(PaymentReasonCode.FAIL_CLOSED_DEFAULT, "receipt timestamp is invalid")
        if (
            policy_time.tzinfo is None
            or runtime_time.tzinfo is None
            or current_time.tzinfo is None
            or policy_age < 0
            or runtime_age < 0
            or policy_age > self.max_receipt_age_seconds
            or runtime_age > self.max_receipt_age_seconds
            or policy_time > runtime_time
        ):
            self._refuse(PaymentReasonCode.FAIL_CLOSED_DEFAULT, "receipt is stale or out of order")

        persisted = self.state_store.get(execution.execution_id)
        if persisted != execution:
            self._refuse(
                PaymentReasonCode.EXPOSURE_RESERVATION_FAILED,
                "credential release state cannot be reproduced from durable storage",
            )
        if execution.state is not ExecutionState.RESERVED or not execution.reservation_id:
            self._refuse(
                PaymentReasonCode.EXPOSURE_RESERVATION_FAILED,
                "credential release requires a durable exposure reservation",
            )
        bindings = (
            execution.transaction_intent_id == canonical.transaction_intent_id,
            execution.canonical_digest == canonical.canonical_digest,
            execution.idempotency_key == canonical.idempotency_key,
            execution.authority_grant_id == canonical.authority_grant_id,
            execution.revocation_epoch == canonical.revocation_epoch,
        )
        if not all(bindings):
            self._refuse(
                PaymentReasonCode.INTENT_BINDING_MISSING,
                "execution record does not bind the canonical transaction",
            )
        if self.receipt_authenticator.verify_policy(policy) is not True or (
            policy.decision is not PaymentDecision.ALLOW
            or not policy.decision_id
            or policy.canonical_digest != canonical.canonical_digest
            or policy.signing_digest != signing_digest
            or policy.policy_id != canonical.policy_id
            or self.trusted_policy_digests.get(policy.policy_id) != policy.policy_digest
        ):
            self._refuse(
                PaymentReasonCode.FAIL_CLOSED_DEFAULT,
                "policy receipt does not authorize the canonical transaction",
            )
        if self.receipt_authenticator.verify_runtime(runtime) is not True or (
            runtime.accepted is not True
            or not runtime.verifier_id
            or runtime.runtime_measurement_id != canonical.runtime_measurement_id
            or runtime.canonical_digest != canonical.canonical_digest
            or runtime.signing_digest != signing_digest
            or self.trusted_runtime_verifier_digests.get(runtime.verifier_id)
            != runtime.verifier_profile_digest
        ):
            self._refuse(
                PaymentReasonCode.ATTESTATION_VERIFICATION_FAILED,
                "runtime receipt does not authorize the canonical transaction",
            )
        human = envelope.human_intent
        if policy.human_approval_required:
            if human is None:
                self._refuse(
                    PaymentReasonCode.HEAR_REQUIRED,
                    "fresh trusted-surface approval is required",
                )
            try:
                approved_time = datetime.fromisoformat(human.approved_at)
                expires_time = datetime.fromisoformat(human.expires_at)
            except (TypeError, ValueError):
                self._refuse(PaymentReasonCode.HEAR_REQUIRED, "human approval time is invalid")
            if (
                approved_time.tzinfo is None
                or expires_time.tzinfo is None
                or approved_time > current_time
                or current_time > expires_time
                or self.receipt_authenticator.verify_human_intent(human) is not True
                or human.canonical_digest != canonical.canonical_digest
                or human.signing_digest != signing_digest
                or not human.approver_id
                or not human.rendering_digest
                or self.trusted_human_authority_digests.get(human.authority_id)
                != human.authority_profile_digest
            ):
                self._refuse(
                    PaymentReasonCode.HEAR_REQUIRED,
                    "human approval is stale, untrusted, or not transaction-bound",
                )
        authoritative_epoch = self.revocation_epoch(canonical.principal_id)
        if (
            envelope.observed_revocation_epoch != authoritative_epoch
            or canonical.revocation_epoch != authoritative_epoch
        ):
            self._refuse(
                PaymentReasonCode.STALE_REVOCATION_EPOCH,
                "revocation epoch changed or could not be reproduced at the guardian",
            )
        replay = self.state_store.consume_reserved_release(
            execution=execution,
            namespace="key-guardian",
            key=canonical.idempotency_key,
            digest=signing_digest,
        )
        if replay is None:
            self._refuse(
                PaymentReasonCode.EXPOSURE_RESERVATION_FAILED,
                "exposure reservation is missing, released, committed, or changed",
            )
        if replay is not ReplayDecision.ACCEPTED:
            self._refuse(
                PaymentReasonCode.REPLAY_DETECTED,
                f"credential release replay result was {replay.value}",
            )
        return signing_digest

    def release(self, envelope: CredentialReleaseEnvelope) -> SignedAuthorization:
        signing_digest = self._verify(envelope)
        signature = self.backend.sign_digest(signing_digest)
        if not isinstance(signature, str) or not signature:
            self._refuse(PaymentReasonCode.FAIL_CLOSED_DEFAULT, "signing backend returned no proof")
        return SignedAuthorization(
            transaction_intent_id=envelope.canonical.transaction_intent_id,
            signing_digest=signing_digest,
            signature=signature,
            algorithm=self.backend.algorithm,
            key_id=self.backend.key_id,
            signer_id=self.backend.signer_id,
            decision_id=envelope.policy.decision_id,
            revocation_epoch=envelope.canonical.revocation_epoch,
            runtime_measurement_id=envelope.canonical.runtime_measurement_id,
        )


class InProcessHMACTestBackend:
    """TEST ONLY backend. Key material remains in process and is not deployable."""

    signer_id = "key-guardian-test"
    key_id = "test-key-1"
    algorithm = "HMAC-SHA256-TEST"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, key: bytes = b"key-guardian-test-key-material") -> None:
        self._key = key

    def sign_digest(self, digest: str) -> str:
        return hmac.new(self._key, digest.encode(), hashlib.sha256).hexdigest()

    def verify(self, authorization: SignedAuthorization) -> bool:
        expected = self.sign_digest(authorization.signing_digest)
        return hmac.compare_digest(expected, authorization.signature)


class InProcessHMACReceiptAuthenticator:
    """TEST ONLY receipt authenticator; production trust roots stay outside the agent."""

    assurance = ComponentAssurance.REFERENCE
    authenticator_id = "receipt-authenticator-test"

    def __init__(self, key: bytes = b"receipt-authenticator-test-key") -> None:
        self._key = key

    def _proof(self, values: dict) -> str:
        payload = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _policy_values(receipt: PolicyAuthorizationReceipt) -> dict:
        return {
            "decision_id": receipt.decision_id,
            "decision": receipt.decision.value,
            "canonical_digest": receipt.canonical_digest,
            "signing_digest": receipt.signing_digest,
            "policy_id": receipt.policy_id,
            "evaluated_at": receipt.evaluated_at,
            "authenticator_id": receipt.authenticator_id,
            "policy_digest": receipt.policy_digest,
            "human_approval_required": receipt.human_approval_required,
        }

    @staticmethod
    def _runtime_values(receipt: RuntimeAuthorizationReceipt) -> dict:
        return {
            "runtime_measurement_id": receipt.runtime_measurement_id,
            "canonical_digest": receipt.canonical_digest,
            "signing_digest": receipt.signing_digest,
            "verifier_id": receipt.verifier_id,
            "accepted": receipt.accepted,
            "verified_at": receipt.verified_at,
            "authenticator_id": receipt.authenticator_id,
            "verifier_profile_digest": receipt.verifier_profile_digest,
        }

    @staticmethod
    def _human_values(receipt: HumanIntentAuthorizationReceipt) -> dict:
        return {
            "approval_id": receipt.approval_id,
            "approver_id": receipt.approver_id,
            "canonical_digest": receipt.canonical_digest,
            "signing_digest": receipt.signing_digest,
            "rendering_digest": receipt.rendering_digest,
            "authority_id": receipt.authority_id,
            "approved_at": receipt.approved_at,
            "expires_at": receipt.expires_at,
            "authenticator_id": receipt.authenticator_id,
            "authority_profile_digest": receipt.authority_profile_digest,
        }

    def seal_policy(self, receipt: PolicyAuthorizationReceipt) -> str:
        return self._proof(self._policy_values(receipt))

    def seal_runtime(self, receipt: RuntimeAuthorizationReceipt) -> str:
        return self._proof(self._runtime_values(receipt))

    def seal_human_intent(self, receipt: HumanIntentAuthorizationReceipt) -> str:
        return self._proof(self._human_values(receipt))

    def verify_policy(self, receipt: PolicyAuthorizationReceipt) -> bool:
        if receipt.authenticator_id != self.authenticator_id:
            return False
        return hmac.compare_digest(self.seal_policy(receipt), receipt.proof)

    def verify_runtime(self, receipt: RuntimeAuthorizationReceipt) -> bool:
        if receipt.authenticator_id != self.authenticator_id:
            return False
        return hmac.compare_digest(self.seal_runtime(receipt), receipt.proof)

    def verify_human_intent(self, receipt: HumanIntentAuthorizationReceipt) -> bool:
        if receipt.authenticator_id != self.authenticator_id:
            return False
        return hmac.compare_digest(self.seal_human_intent(receipt), receipt.proof)
