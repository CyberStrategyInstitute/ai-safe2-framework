"""
nexus_sdk/payments/gateway.py
The NEXUS Payment Integrity Gateway.

Orchestrates the CP.5.APAY execution sequence and emits the metrics a
conformance claim is measured on.

POSITION IN THE STACK
    This is not a wallet, an identity provider, a payment processor or a rail.
    It sits between an agent and whatever holds spending power - a credential
    provider, an x402 facilitator, a card-token service, a bank API, a
    stablecoin wallet - and decides whether this measured workload may still use
    that authority for this transaction at this moment.

    It is deployable by the spend-side enterprise alone. That is the whole point
    of the beachhead: the organization running agents that spend money already
    controls the runtime, the identity system, the policy and the wallet
    integration, so it can ship this without waiting for merchants, card
    networks or registries to adopt anything.

WHAT THE GATEWAY DOES NOT CLAIM
    It cannot prove the principal meant what they said. It cannot make an
    irreversible rail reversible. It cannot detect a merchant that is authentic
    and malicious. These limits are stated in the threat model rather than
    engineered around with optimistic defaults.
"""

from __future__ import annotations

import threading
from dataclasses import replace
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol

from nexus_sdk.payments.authority import AuthorityGraph, SpendRecord
from nexus_sdk.payments.attestation import AttestationVerifier, NullAttestationVerifier
from nexus_sdk.payments.broker import (
    BrokerRefusal,
    CredentialBroker,
    NullCredentialBroker,
    SignedAuthorization,
)
from nexus_sdk.payments.evidence import DisclosureTier, EvidenceLedger
from nexus_sdk.payments.firewall import PaymentVerdict, TransactionFirewall
from nexus_sdk.payments.user_control import UserControlPolicy
from nexus_sdk.payments.objects import (
    CanonicalTransaction,
    Money,
    PaymentDecision,
    PaymentReasonCode,
    PrincipalBinding,
    RuntimeMeasurement,
    TransactionIntent,
    utcnow,
)

__all__ = [
    "SettlementState",
    "SettlementResult",
    "PaymentOutcome",
    "PaymentIntegrityGateway",
    "GatewayMetrics",
    "HumanApprovalVerifier",
    "NullHumanApprovalVerifier",
]


class SettlementState:
    PENDING = "pending"
    SETTLED = "settled"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"       # timeout or partial: never retried blindly
    RECONCILING = "reconciling"


class HumanApprovalVerifier(Protocol):
    """Verify fresh, intent-bound human approval outside the agent process."""

    def verify(self, intent: TransactionIntent, *, claimed_authority: str,
               expected_authority: str, now: datetime) -> bool: ...


class NullHumanApprovalVerifier:
    """Fail-closed default: a caller-supplied name is not approval proof."""

    def verify(self, intent: TransactionIntent, *, claimed_authority: str,
               expected_authority: str, now: datetime) -> bool:
        return False


@dataclass
class SettlementResult:
    """What the rail reported back. `AMBIGUOUS` is a first-class outcome.

    Most payment integrations model success and failure. The state that actually
    causes duplicate settlement and service-without-payment is the third one:
    a timeout where nobody knows whether value moved. Naming it forces the
    caller to route it into reconciliation instead of retrying.
    """
    state: str
    settlement_id: Optional[str] = None
    settled_amount: Optional[Money] = None
    detail: str = ""
    settled_at: Optional[str] = None


@dataclass
class PaymentOutcome:
    """Everything that happened for one transaction intent."""
    verdict: PaymentVerdict
    authorization: Optional[SignedAuthorization] = None
    settlement: Optional[SettlementResult] = None
    receipt_ids: list[str] = field(default_factory=list)
    transaction_intent_id: str = ""
    reservation_id: Optional[str] = None
    reserved_amount: Optional[Money] = None

    @property
    def authorized(self) -> bool:
        return self.authorization is not None

    @property
    def settled(self) -> bool:
        return bool(self.settlement and self.settlement.state == SettlementState.SETTLED)


@dataclass
class GatewayMetrics:
    """The engineering metrics CP.5.APAY conformance is reported against.

    Deliberately not fraud-loss or identity-match-rate. Those measure outcomes
    after the fact; these measure whether the controls were actually load-bearing.
    """
    transactions_evaluated: int = 0
    transactions_allowed: int = 0
    transactions_denied: int = 0
    transactions_escalated: int = 0
    transactions_reconciling: int = 0
    runtime_bound_authorizations: int = 0
    downgrade_attempts: int = 0
    downgrade_blocked: int = 0
    replay_attempts_blocked: int = 0
    attenuation_violations_blocked: int = 0
    aggregate_ceiling_blocks: int = 0
    velocity_blocks: int = 0
    hear_escalations: int = 0
    broker_refusals: int = 0
    ambiguous_settlements: int = 0

    def runtime_binding_coverage(self) -> float:
        """Share of authorizations bound to a fresh, accepted runtime measurement."""
        total = self.transactions_allowed
        return (self.runtime_bound_authorizations / total) if total else 0.0

    def downgrade_block_rate(self) -> float:
        return (self.downgrade_blocked / self.downgrade_attempts) if self.downgrade_attempts else 1.0

    def to_dict(self) -> dict:
        return {
            "transactions_evaluated": self.transactions_evaluated,
            "transactions_allowed": self.transactions_allowed,
            "transactions_denied": self.transactions_denied,
            "transactions_escalated": self.transactions_escalated,
            "transactions_reconciling": self.transactions_reconciling,
            "runtime_binding_coverage": round(self.runtime_binding_coverage(), 4),
            "downgrade_block_rate": round(self.downgrade_block_rate(), 4),
            "downgrade_attempts": self.downgrade_attempts,
            "replay_attempts_blocked": self.replay_attempts_blocked,
            "attenuation_violations_blocked": self.attenuation_violations_blocked,
            "aggregate_ceiling_blocks": self.aggregate_ceiling_blocks,
            "velocity_blocks": self.velocity_blocks,
            "hear_escalations": self.hear_escalations,
            "broker_refusals": self.broker_refusals,
            "ambiguous_settlements": self.ambiguous_settlements,
        }


class PaymentIntegrityGateway:
    """In-path enforcement for the agent-to-payment plane."""

    FRAMEWORK_VERSION = "AI SAFE2 v3.1"
    PROFILE_VERSION = "CP.5.APAY/0.4"

    def __init__(self, graph: AuthorityGraph, *,
                 firewall: Optional[TransactionFirewall] = None,
                 broker: Optional[CredentialBroker] = None,
                 ledger: Optional[EvidenceLedger] = None,
                 attestation_verifier: Optional[AttestationVerifier] = None,
                 user_controls: Optional[UserControlPolicy] = None,
                 human_approval_verifier: Optional[HumanApprovalVerifier] = None) -> None:
        self.graph = graph
        self.firewall = firewall or TransactionFirewall(graph)
        # Default refuses to sign. An unconfigured gateway must not move money.
        self.broker = broker or NullCredentialBroker()
        self.ledger = ledger or EvidenceLedger()
        self.attestation_verifier = attestation_verifier or NullAttestationVerifier()
        self.user_controls = user_controls
        self.human_approval_verifier = human_approval_verifier or NullHumanApprovalVerifier()
        self.metrics = GatewayMetrics()
        self._principals: dict[str, PrincipalBinding] = {}
        self._baselines: dict[str, str] = {}   # agent_did -> expected runtime baseline
        self._lock = threading.RLock()

    # ── Registration ─────────────────────────────────────────────────────────

    def register_principal(self, binding: PrincipalBinding) -> PrincipalBinding:
        """APAY-01. Refuses a payment-capable agent with no accountable human."""
        problems = binding.validate()
        if problems:
            raise ValueError("principal binding incomplete: " + ", ".join(problems))
        with self._lock:
            self._principals[binding.agent_did] = binding
        return binding

    def pin_runtime_baseline(self, agent_did: str, baseline_digest: str) -> None:
        """Pin the approved runtime for an agent. Any drift becomes a mismatch."""
        with self._lock:
            self._baselines[agent_did] = baseline_digest

    # ── Main path ────────────────────────────────────────────────────────────

    def authorize(self, intent: TransactionIntent, *,
                  runtime: Optional[RuntimeMeasurement] = None,
                  hear_satisfied_by: Optional[str] = None,
                  now: Optional[datetime] = None) -> PaymentOutcome:
        """Evaluate, and on ALLOW obtain a signature over the canonical object.

        The agent never sees a credential. It receives an outcome, and the
        signature it contains covers only what the policy engine approved.
        """
        now = now or utcnow()
        grant = self.graph.get(intent.authority_grant_id)
        expected_baseline = None
        binding = None
        if grant is not None and grant.agent_did:
            with self._lock:
                expected_baseline = self._baselines.get(grant.agent_did)
                binding = self._principals.get(grant.agent_did)

        if (grant is not None and (
                binding is None
                or binding.principal_id != grant.principal_id
                or binding.agent_did != grant.agent_did)):
            verdict = PaymentVerdict(
                decision=PaymentDecision.DENY,
                transaction_intent_id=intent.transaction_intent_id,
                reason_codes=[PaymentReasonCode.NO_PRINCIPAL_BINDING],
                reasoning="registered principal binding is missing or does not match the grant",
                policy_id=self.firewall.policy_id,
            )
            self._count(verdict, intent)
            outcome = PaymentOutcome(verdict=verdict,
                                     transaction_intent_id=intent.transaction_intent_id)
            receipt = self._write_receipt(intent, verdict, runtime, grant,
                                          authorization=None, settlement=None,
                                          hear_satisfied_by=None)
            outcome.receipt_ids.append(receipt.receipt_id)
            return outcome

        if hear_satisfied_by:
            expected_authority = binding.hear_authority if binding else None
            if (not expected_authority
                    or hear_satisfied_by != expected_authority
                    or not self.human_approval_verifier.verify(
                        intent,
                        claimed_authority=hear_satisfied_by,
                        expected_authority=expected_authority,
                        now=now,
                    )):
                hear_satisfied_by = None

        if runtime is not None and runtime.attested:
            proof = self.attestation_verifier.verify(
                runtime, expected_baseline=expected_baseline, now=now
            )
            if not proof.accepted:
                runtime = replace(runtime, attested=False)

        verdict = self.firewall.evaluate(
            intent,
            runtime=runtime,
            expected_runtime_baseline=expected_baseline,
            hear_satisfied_by=hear_satisfied_by,
            now=now,
        )
        if verdict.allowed and self.user_controls is not None:
            user_decision = self.user_controls.check(
                intent, confirmed_by=hear_satisfied_by, now=now
            )
            if not user_decision.allow:
                hard_deny = any("pause" in r or "blocked" in r for r in user_decision.reasons)
                verdict = PaymentVerdict(
                    decision=PaymentDecision.DENY if hard_deny else PaymentDecision.ESCALATE,
                    transaction_intent_id=intent.transaction_intent_id,
                    reason_codes=[PaymentReasonCode.HEAR_REQUIRED],
                    reasoning="Human Shield: " + "; ".join(user_decision.reasons),
                    policy_id=verdict.policy_id,
                    consequence=verdict.consequence,
                )
        self._count(verdict, intent)

        outcome = PaymentOutcome(verdict=verdict,
                                 transaction_intent_id=intent.transaction_intent_id)

        if not verdict.allowed:
            receipt = self._write_receipt(intent, verdict, runtime, grant,
                                          authorization=None, settlement=None,
                                          hear_satisfied_by=hear_satisfied_by)
            outcome.receipt_ids.append(receipt.receipt_id)
            return outcome

        assert grant is not None  # ALLOW is impossible without a resolved grant

        # Spend Hold: authorization consumes available authority immediately,
        # before any credential is released. This closes the authorized-but-
        # unsettled overspend window.
        try:
            reservation = self.graph.reserve_exposure(
                grant, intent.amount, intent.transaction_intent_id, now=now
            )
            outcome.reservation_id = reservation.reservation_id
            outcome.reserved_amount = reservation.amount
        except ValueError as exc:
            self.metrics.transactions_allowed -= 1
            self.metrics.transactions_denied += 1
            verdict = PaymentVerdict(
                decision=PaymentDecision.DENY,
                transaction_intent_id=intent.transaction_intent_id,
                reason_codes=[PaymentReasonCode.EXPOSURE_RESERVATION_FAILED],
                reasoning=f"spend hold refused: {exc}",
                policy_id=verdict.policy_id,
                consequence=verdict.consequence,
            )
            outcome.verdict = verdict
            receipt = self._write_receipt(intent, verdict, runtime, grant,
                                          authorization=None, settlement=None,
                                          hear_satisfied_by=hear_satisfied_by)
            outcome.receipt_ids.append(receipt.receipt_id)
            return outcome

        canonical = CanonicalTransaction(
            transaction_intent_id=intent.transaction_intent_id,
            authority_grant_id=grant.authority_grant_id,
            delegation_chain_id=grant.delegation_chain_id or "",
            principal_id=grant.principal_id,
            policy_id=verdict.policy_id,
            runtime_measurement_id=runtime.runtime_measurement_id if runtime else "",
            revocation_epoch=grant.revocation_epoch,
            canonical_digest=intent.canonical_digest(),
            amount=intent.amount,
            merchant_id=intent.merchant_id,
            destination=intent.destination,
            rail=intent.rail,
            idempotency_key=intent.idempotency_key or "",
        )

        # Re-read the revocation epoch immediately before signing. This is the
        # revocation race: a decision made microseconds ago is not authority if
        # the kill switch fired in between.
        try:
            epoch_now = self.graph.revocation.current_epoch(grant.principal_id)
        except RuntimeError:
            self.graph.release_reservation(intent.transaction_intent_id)
            epoch_now = None
            verdict = PaymentVerdict(
                decision=PaymentDecision.RECONCILE,
                transaction_intent_id=intent.transaction_intent_id,
                reason_codes=[PaymentReasonCode.REVOCATION_STATUS_UNAVAILABLE],
                reasoning="revocation authority unreachable at credential release",
                policy_id=verdict.policy_id,
                consequence=verdict.consequence,
            )
            outcome.verdict = verdict
            self.metrics.transactions_reconciling += 1
            receipt = self._write_receipt(intent, verdict, runtime, grant,
                                          authorization=None, settlement=None,
                                          hear_satisfied_by=hear_satisfied_by)
            outcome.receipt_ids.append(receipt.receipt_id)
            return outcome

        try:
            authorization = self.broker.sign(
                canonical,
                decision=verdict.decision,
                decision_id=verdict.decision_id,
                revocation_epoch_now=epoch_now,
            )
        except BrokerRefusal as refusal:
            self.graph.release_reservation(intent.transaction_intent_id)
            self.metrics.broker_refusals += 1
            self.metrics.transactions_allowed -= 1
            self.metrics.transactions_denied += 1
            verdict = PaymentVerdict(
                decision=PaymentDecision.DENY,
                transaction_intent_id=intent.transaction_intent_id,
                reason_codes=[refusal.code],
                reasoning=f"credential broker refused: {refusal}",
                policy_id=verdict.policy_id,
                consequence=verdict.consequence,
            )
            outcome.verdict = verdict
            receipt = self._write_receipt(intent, verdict, runtime, grant,
                                          authorization=None, settlement=None,
                                          hear_satisfied_by=hear_satisfied_by)
            outcome.receipt_ids.append(receipt.receipt_id)
            return outcome

        self.firewall.replay.commit(intent)
        if runtime is not None and runtime.attested:
            self.metrics.runtime_bound_authorizations += 1

        outcome.authorization = authorization
        receipt = self._write_receipt(intent, verdict, runtime, grant,
                                      authorization=authorization, settlement=None,
                                      hear_satisfied_by=hear_satisfied_by)
        outcome.receipt_ids.append(receipt.receipt_id)
        return outcome

    def settle(self, outcome: PaymentOutcome, result: SettlementResult, *,
               now: Optional[datetime] = None) -> PaymentOutcome:
        """Record settlement and update exposure atomically (APAY-16 / APAY-18).

        Exposure is committed for SETTLED and for AMBIGUOUS. Counting an
        ambiguous settlement as zero spend is how a timeout becomes free money:
        the ceiling has to assume the value may have moved until reconciliation
        proves it did not.
        """
        now = now or utcnow()
        if outcome.authorization is None:
            raise ValueError("cannot settle an outcome that was never authorized")
        if outcome.settlement is not None:
            if (outcome.settlement.state == result.state
                    and outcome.settlement.settlement_id == result.settlement_id):
                return outcome
            if outcome.settlement.state != SettlementState.AMBIGUOUS:
                raise ValueError("settlement outcome is already terminal")

        intent_id = outcome.transaction_intent_id
        grant_id = None
        for receipt in self.ledger.for_intent(intent_id):
            grant_id = receipt.fields.get("authority_grant_id") or grant_id
        grant = self.graph.get(grant_id) if grant_id else None

        if result.state == SettlementState.AMBIGUOUS:
            self.metrics.ambiguous_settlements += 1

        if grant is not None and result.state == SettlementState.SETTLED:
            amount = result.settled_amount or outcome.reserved_amount
            if amount is None:
                raise ValueError("settled result lacks both amount and spend hold")
            if outcome.reserved_amount is None or amount != outcome.reserved_amount:
                raise ValueError("settled amount does not match the authorized Spend Hold")
            self.graph.record_spend(SpendRecord(
                authority_grant_id=grant.authority_grant_id,
                delegation_chain_id=grant.delegation_chain_id or "",
                amount=amount,
                merchant_id=str(
                    next((r.fields.get("merchant_id")
                          for r in self.ledger.for_intent(intent_id)
                          if r.fields.get("merchant_id")), "unknown")
                ),
                occurred_at=now,
                transaction_intent_id=intent_id,
                settled=True,
            ))
            self.graph.release_reservation(intent_id)
        elif result.state == SettlementState.FAILED:
            self.graph.release_reservation(intent_id)
        # AMBIGUOUS deliberately retains the full Spend Hold. Reconciliation
        # can later convert it to settled spend or release it on proven failure.

        result.settled_at = result.settled_at or now.isoformat()
        outcome.settlement = result

        fields = self._base_fields(grant)
        fields.update({
            "transaction_intent_id": intent_id,
            "decision_id": outcome.verdict.decision_id,
            "decision": outcome.verdict.decision.value,
            "settlement_id": result.settlement_id,
            "settlement_state": result.state,
            "settled_at": result.settled_at,
            "settled_amount": result.settled_amount.to_dict() if result.settled_amount else None,
            "settlement_detail": result.detail,
            "authorization_id": outcome.authorization.authorization_id,
            "signing_digest": outcome.authorization.signing_digest,
        })
        receipt = self.ledger.append(fields)
        outcome.receipt_ids.append(receipt.receipt_id)
        return outcome

    # ── Revocation ───────────────────────────────────────────────────────────

    def revoke_principal(self, principal_id: str, *,
                         reason: str = "operator kill decision",
                         now: Optional[datetime] = None) -> dict:
        """APAY-13. One call severs every grant, descendant and cached decision.

        Returns the measurement inputs for revocation effectiveness time, so a
        deployment reports what actually stopped rather than that an API
        returned 200.
        """
        now = now or utcnow()
        epoch = self.graph.revocation.revoke_principal(principal_id, at=now)
        affected = [g for g in self._all_grants() if g.principal_id == principal_id]
        for grant in affected:
            grant.revoked = True
        self.ledger.append({
            **self._base_fields(None),
            "event": "revocation",
            "principal_id": principal_id,
            "revocation_epoch": epoch,
            "reason": reason,
            "grants_affected": [g.authority_grant_id for g in affected],
            "decided_at": now.isoformat(),
        })
        return {
            "principal_id": principal_id,
            "revocation_epoch": epoch,
            "revoked_at": now.isoformat(),
            "grants_affected": len(affected),
        }

    def exposure_after_revocation(self, principal_id: str,
                                  currency: str = "USD") -> Money:
        """Value that still moved after the kill decision. The metric that counts."""
        moment = self.graph.revocation.revoked_at(f"principal:{principal_id}")
        if moment is None:
            return Money(0, currency)
        return self.graph.exposure_after(moment, currency=currency)

    # ── Evidence ─────────────────────────────────────────────────────────────

    def dispute_bundle(self, transaction_intent_id: str,
                       tier: str = DisclosureTier.ADJUDICATION) -> dict:
        return self.ledger.bundle(transaction_intent_id, tier)

    # ── Internals ────────────────────────────────────────────────────────────

    def _all_grants(self):
        # AuthorityGraph keeps its own lock; this reads through its public API.
        seen: list = []
        for gid in list(self.graph._grants.keys()):  # noqa: SLF001 - same package contract
            grant = self.graph.get(gid)
            if grant is not None:
                seen.append(grant)
        return seen

    def _base_fields(self, grant) -> dict[str, Any]:
        return {
            "framework_version": self.FRAMEWORK_VERSION,
            "profile_version": self.PROFILE_VERSION,
            "authority_grant_id": grant.authority_grant_id if grant else None,
            "delegation_chain_id": grant.delegation_chain_id if grant else None,
            "principal_id": grant.principal_id if grant else None,
        }

    def _count(self, verdict: PaymentVerdict, intent: TransactionIntent) -> None:
        m = self.metrics
        m.transactions_evaluated += 1
        if verdict.decision is PaymentDecision.ALLOW:
            m.transactions_allowed += 1
        elif verdict.decision is PaymentDecision.ESCALATE:
            m.transactions_escalated += 1
            m.hear_escalations += 1
        elif verdict.decision is PaymentDecision.RECONCILE:
            m.transactions_reconciling += 1
        else:
            m.transactions_denied += 1

        grant = self.graph.get(intent.authority_grant_id)
        if grant is not None and int(intent.path_assurance) < int(grant.constraints.min_assurance):
            m.downgrade_attempts += 1
            if PaymentReasonCode.ASSURANCE_DOWNGRADE in verdict.reason_codes:
                m.downgrade_blocked += 1

        codes = set(verdict.reason_codes)
        if PaymentReasonCode.REPLAY_DETECTED in codes:
            m.replay_attempts_blocked += 1
        if PaymentReasonCode.ATTENUATION_VIOLATION in codes:
            m.attenuation_violations_blocked += 1
        if PaymentReasonCode.AGGREGATE_CEILING_EXCEEDED in codes or \
           PaymentReasonCode.WINDOW_CEILING_EXCEEDED in codes:
            m.aggregate_ceiling_blocks += 1
        if codes & {
            PaymentReasonCode.VELOCITY_ANOMALY,
            PaymentReasonCode.MICRO_DRAIN_SUSPECTED,
            PaymentReasonCode.MERCHANT_DISPERSION_ANOMALY,
            PaymentReasonCode.SPLIT_TRANSACTION_SUSPECTED,
        }:
            m.velocity_blocks += 1

    def _write_receipt(self, intent: TransactionIntent, verdict: PaymentVerdict,
                       runtime: Optional[RuntimeMeasurement], grant,
                       *, authorization: Optional[SignedAuthorization],
                       settlement: Optional[SettlementResult],
                       hear_satisfied_by: Optional[str]):
        binding = None
        if grant is not None and grant.agent_did:
            with self._lock:
                binding = self._principals.get(grant.agent_did)

        aggregate_after = None
        if grant is not None:
            try:
                aggregate_after = self.graph.subtree_spend(
                    grant.authority_grant_id, currency=intent.amount.currency
                ).to_dict()
            except Exception:  # exposure reporting must never block a decision
                aggregate_after = None

        fields: dict[str, Any] = {
            **self._base_fields(grant),
            "transaction_intent_id": intent.transaction_intent_id,
            "owner_of_record": binding.owner_of_record if binding else None,
            "agent_did": grant.agent_did if grant else None,
            "act_tier": binding.act_tier if binding else None,
            "consequence_class": verdict.consequence.value,
            "instruction_ref": grant.instruction_ref if grant else None,
            "instruction_digest": grant.instruction_digest if grant else None,
            "normalized_constraints_digest": grant.normalized_constraints_digest if grant else None,
            "approval_surface_digest": grant.approval_surface if grant else None,
            "approved_cart_digest": intent.approved_cart_digest,
            "canonical_digest": intent.canonical_digest(),
            "delegation_lineage": (
                [g.authority_grant_id for g in self.graph.ancestors(grant.authority_grant_id)]
                + [grant.authority_grant_id] if grant else []
            ),
            "attenuation_result": (
                self.graph.lineage_violations(grant.authority_grant_id) or "monotonic"
                if grant else None
            ),
            "runtime_measurement_id": runtime.runtime_measurement_id if runtime else None,
            "runtime_baseline_digest": runtime.baseline_digest() if runtime else None,
            "runtime_attested": runtime.attested if runtime else False,
            "policy_id": verdict.policy_id,
            "decision_id": verdict.decision_id,
            "decision": verdict.decision.value,
            "reason_codes": verdict.codes,
            "merchant_id": intent.merchant_id,
            "merchant_baseline_digest": intent.merchant_baseline_digest,
            "destination": intent.destination,
            "rail": intent.rail.value,
            "facilitator": intent.facilitator,
            "path_assurance": int(intent.path_assurance),
            "amount": intent.amount.to_dict(),
            "aggregate_exposure_after": aggregate_after,
            "revocation_epoch": grant.revocation_epoch if grant else None,
            "idempotency_key": intent.idempotency_key,
            "nonce": intent.nonce,
            "risk_signals": verdict.codes,
            # Never None. An adjudicator must be able to tell "no human was
            # needed" apart from "a human was needed and the record is missing".
            "hear_satisfied_by": (
                hear_satisfied_by if hear_satisfied_by
                else ("required_not_satisfied"
                      if PaymentReasonCode.HEAR_REQUIRED in verdict.reason_codes
                      else "not_required")
            ),
            "decided_at": verdict.evaluated_at,
            "settlement_id": settlement.settlement_id if settlement else None,
            "settlement_state": settlement.state if settlement else SettlementState.PENDING,
            "settled_at": settlement.settled_at if settlement else None,
        }
        if authorization is not None:
            fields["authorization_id"] = authorization.authorization_id
            fields["signing_digest"] = authorization.signing_digest
            fields["signer_id"] = authorization.signer_id
        return self.ledger.append(fields)
