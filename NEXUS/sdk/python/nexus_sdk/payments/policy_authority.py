"""Policy Authority: deterministic evaluation and authenticated decision receipts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from nexus_sdk.payments.execution_plane import ComponentAssurance
from nexus_sdk.payments.firewall import PaymentVerdict, TransactionFirewall
from nexus_sdk.payments.key_guardian import PolicyAuthorizationReceipt
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    PaymentDecision,
    RuntimeMeasurement,
    TransactionIntent,
    canonical_hash,
    utcnow,
)

__all__ = [
    "DeterministicPolicyAuthority",
    "PolicyAuthorityDecision",
    "PolicyDefinition",
    "PolicyReceiptIssuer",
]


@dataclass(frozen=True)
class PolicyDefinition:
    """Immutable identity for the exact deterministic rules and configuration."""

    policy_id: str
    ruleset_version: str
    configuration_digest: str
    evaluator_id: str

    @property
    def policy_digest(self) -> str:
        return canonical_hash({
            "policy_id": self.policy_id,
            "ruleset_version": self.ruleset_version,
            "configuration_digest": self.configuration_digest,
            "evaluator_id": self.evaluator_id,
        })


class PolicyReceiptIssuer(Protocol):
    """Protected proof issuer whose verification key is trusted by Key Guardian."""

    authenticator_id: str
    assurance: ComponentAssurance

    def seal_policy(self, receipt: PolicyAuthorizationReceipt) -> str: ...


@dataclass(frozen=True)
class PolicyAuthorityDecision:
    """Inspectable outcome; only ALLOW outcomes contain signing authority."""

    verdict: PaymentVerdict
    policy_digest: str
    canonical: CanonicalTransaction | None = None
    receipt: PolicyAuthorizationReceipt | None = None

    @property
    def authorized(self) -> bool:
        return (
            self.verdict.decision is PaymentDecision.ALLOW
            and self.canonical is not None
            and self.receipt is not None
        )


class DeterministicPolicyAuthority:
    """Independent policy decision and receipt-issuance boundary."""

    human_name = "Policy Authority"
    technical_name = "DeterministicPolicyAuthority"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, *, firewall: TransactionFirewall,
                 definition: PolicyDefinition,
                 receipt_issuer: PolicyReceiptIssuer) -> None:
        if firewall.policy_id != definition.policy_id:
            raise ValueError("firewall and policy definition identifiers must match")
        if not definition.configuration_digest or not receipt_issuer.authenticator_id:
            raise ValueError("policy configuration and receipt issuer identity are required")
        self.firewall = firewall
        self.definition = definition
        self.receipt_issuer = receipt_issuer

    def evaluate(self, intent: TransactionIntent, *,
                 runtime: RuntimeMeasurement | None,
                 expected_runtime_baseline: str | None = None,
                 hear_satisfied_by: str | None = None,
                 now: datetime | None = None) -> PolicyAuthorityDecision:
        evaluated_at = now or utcnow()
        verdict = self.firewall.evaluate(
            intent,
            runtime=runtime,
            expected_runtime_baseline=expected_runtime_baseline,
            hear_satisfied_by=hear_satisfied_by,
            now=evaluated_at,
        )
        if verdict.decision is not PaymentDecision.ALLOW:
            return PolicyAuthorityDecision(verdict, self.definition.policy_digest)
        if runtime is None or not runtime.runtime_measurement_id:
            raise RuntimeError("an ALLOW verdict without a runtime identity cannot be authorized")
        grant = self.firewall.graph.get(intent.authority_grant_id)
        if grant is None or not grant.delegation_chain_id or not intent.idempotency_key:
            raise RuntimeError("an ALLOW verdict without complete authority binding is invalid")

        decided_at = evaluated_at.isoformat()
        canonical = CanonicalTransaction(
            transaction_intent_id=intent.transaction_intent_id,
            authority_grant_id=grant.authority_grant_id,
            delegation_chain_id=grant.delegation_chain_id,
            principal_id=grant.principal_id,
            policy_id=self.definition.policy_id,
            runtime_measurement_id=runtime.runtime_measurement_id,
            revocation_epoch=grant.revocation_epoch,
            canonical_digest=intent.canonical_digest(),
            amount=intent.amount,
            merchant_id=intent.merchant_id,
            destination=intent.destination,
            rail=intent.rail,
            idempotency_key=intent.idempotency_key,
            decided_at=decided_at,
        )
        decision_id = "dec_" + canonical_hash({
            "evaluator_id": self.definition.evaluator_id,
            "policy_digest": self.definition.policy_digest,
            "signing_digest": canonical.signing_digest(),
            "decision": verdict.decision.value,
            "reason_codes": verdict.codes,
        })[:32]
        verdict = replace(verdict, decision_id=decision_id, evaluated_at=decided_at)
        receipt = PolicyAuthorizationReceipt(
            decision_id=decision_id,
            decision=PaymentDecision.ALLOW,
            canonical_digest=canonical.canonical_digest,
            signing_digest=canonical.signing_digest(),
            policy_id=self.definition.policy_id,
            evaluated_at=decided_at,
            authenticator_id=self.receipt_issuer.authenticator_id,
            proof="",
            policy_digest=self.definition.policy_digest,
        )
        receipt = replace(receipt, proof=self.receipt_issuer.seal_policy(receipt))
        if not receipt.proof:
            raise RuntimeError("policy receipt issuer returned no proof")
        return PolicyAuthorityDecision(
            verdict=verdict,
            policy_digest=self.definition.policy_digest,
            canonical=canonical,
            receipt=receipt,
        )
