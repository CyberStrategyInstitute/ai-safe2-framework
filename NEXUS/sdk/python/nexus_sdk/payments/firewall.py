"""
nexus_sdk/payments/firewall.py
The deterministic transaction policy decision point.

Implements APAY-04 (independent constraint evaluation), APAY-11 (freshness and
replay resistance), APAY-12 (transaction continuity), APAY-14 (downgrade
resistance), APAY-15 (counterparty provenance) and APAY-18 (fail-safe response).

ARCHITECTURAL RULE
    No language model participates in this decision. The firewall takes objects
    and returns a verdict by rule evaluation only. This is the difference
    between a control and a suggestion: a policy engine an attacker can talk to
    is a policy engine an attacker can talk out of.

FAIL-CLOSED IS THE DEFAULT PATH, NOT THE ERROR PATH
    Every unknown resolves to DENY or RECONCILE. Missing runtime measurement,
    unreachable revocation authority, an expired quote, an unverified merchant -
    none of these produce "allow with a warning". A control that degrades to
    permissive under load is load-bearing only when nothing is wrong.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from nexus_sdk.payments.authority import AuthorityGraph
from nexus_sdk.payments.objects import (
    AssuranceLevel,
    AuthorityGrant,
    ConsequenceClass,
    Money,
    PaymentDecision,
    PaymentReasonCode,
    RuntimeMeasurement,
    SettlementFinality,
    TransactionIntent,
    utcnow,
)

__all__ = [
    "PaymentVerdict",
    "ReplayLedger",
    "CounterpartyRegistry",
    "TransactionFirewall",
]


# ── Verdict ───────────────────────────────────────────────────────────────────

@dataclass
class PaymentVerdict:
    """The decision, with every reason that produced it.

    All failing rules are reported, not just the first. An operator debugging a
    blocked payment needs the full set; returning one reason at a time turns a
    single misconfiguration into a queue of support tickets.
    """
    decision: PaymentDecision
    transaction_intent_id: str
    reason_codes: list[PaymentReasonCode] = field(default_factory=list)
    reasoning: str = ""
    policy_id: str = "nexus-apay-v0.4"
    consequence: ConsequenceClass = ConsequenceClass.ROUTINE
    evaluated_at: str = field(default_factory=lambda: utcnow().isoformat())
    decision_id: str = field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:20]}")

    @property
    def allowed(self) -> bool:
        return self.decision is PaymentDecision.ALLOW

    @property
    def codes(self) -> list[str]:
        return [c.value for c in self.reason_codes]

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "decision": self.decision.value,
            "transaction_intent_id": self.transaction_intent_id,
            "reason_codes": self.codes,
            "reasoning": self.reasoning,
            "policy_id": self.policy_id,
            "consequence": self.consequence.value,
            "evaluated_at": self.evaluated_at,
        }


# ── Replay ledger ─────────────────────────────────────────────────────────────

class ReplayLedger:
    """APAY-11. Idempotency and nonce single-use enforcement.

    Two distinct jobs share this structure. A nonce may be used exactly once,
    ever. An idempotency key may be *retried*, but a retry must carry the same
    canonical digest: a retry that quietly changed the amount is a replay
    attack wearing a retry's clothes.
    """

    def __init__(self) -> None:
        self._nonces: set[str] = set()
        self._idempotency: dict[str, str] = {}
        self._lock = threading.RLock()

    def check(self, intent: TransactionIntent) -> list[PaymentReasonCode]:
        reasons: list[PaymentReasonCode] = []
        with self._lock:
            if not intent.nonce:
                reasons.append(PaymentReasonCode.NONCE_MISSING)
            elif intent.nonce in self._nonces:
                reasons.append(PaymentReasonCode.REPLAY_DETECTED)
            key = intent.idempotency_key or ""
            prior = self._idempotency.get(key)
            if prior is not None and prior != intent.canonical_digest():
                reasons.append(PaymentReasonCode.REPLAY_DETECTED)
        return reasons

    def commit(self, intent: TransactionIntent) -> None:
        with self._lock:
            if intent.nonce:
                self._nonces.add(intent.nonce)
            if intent.idempotency_key:
                self._idempotency[intent.idempotency_key] = intent.canonical_digest()

    def seen_idempotency_key(self, key: str) -> bool:
        with self._lock:
            return key in self._idempotency


# ── Counterparty registry ─────────────────────────────────────────────────────

class CounterpartyRegistry:
    """APAY-15. Merchant, destination and facilitator baselines.

    Registry entries are baselines, not blessings. A merchant whose catalog
    schema or settlement destination has changed since the baseline was taken
    is treated as unverified until re-baselined, because a valid registry entry
    pointing at a substituted destination is exactly the registry-compromise
    case this is meant to catch.
    """

    def __init__(self) -> None:
        self._merchants: dict[str, str] = {}      # merchant_id -> baseline digest
        self._destinations: dict[str, set[str]] = {}  # merchant_id -> known destinations
        self._facilitators: set[str] = set()
        self._lock = threading.RLock()

    def register_merchant(self, merchant_id: str, baseline_digest: str,
                          destinations: Optional[set[str]] = None) -> None:
        with self._lock:
            self._merchants[merchant_id] = baseline_digest
            self._destinations[merchant_id] = set(destinations or set())

    def trust_facilitator(self, facilitator: str) -> None:
        with self._lock:
            self._facilitators.add(facilitator)

    def check(self, intent: TransactionIntent) -> list[PaymentReasonCode]:
        reasons: list[PaymentReasonCode] = []
        with self._lock:
            baseline = self._merchants.get(intent.merchant_id)
            if baseline is None or not intent.merchant_verified:
                reasons.append(PaymentReasonCode.COUNTERPARTY_UNVERIFIED)
            elif intent.merchant_baseline_digest != baseline:
                reasons.append(PaymentReasonCode.COUNTERPARTY_UNVERIFIED)
            known = self._destinations.get(intent.merchant_id)
            if intent.destination and known and intent.destination not in known:
                reasons.append(PaymentReasonCode.DESTINATION_SUBSTITUTED)
            if intent.facilitator and intent.facilitator not in self._facilitators:
                reasons.append(PaymentReasonCode.FACILITATOR_NOT_TRUSTED)
        return reasons


# ── Firewall ──────────────────────────────────────────────────────────────────

class TransactionFirewall:
    """Deterministic evaluation of one proposed value movement."""

    def __init__(self, graph: AuthorityGraph, *,
                 replay: Optional[ReplayLedger] = None,
                 counterparties: Optional[CounterpartyRegistry] = None,
                 policy_id: str = "nexus-apay-v0.4",
                 critical_threshold: Optional[Money] = None) -> None:
        self.graph = graph
        self.replay = replay or ReplayLedger()
        self.counterparties = counterparties or CounterpartyRegistry()
        self.policy_id = policy_id
        self.critical_threshold = critical_threshold

    def evaluate(self, intent: TransactionIntent, *,
                 runtime: Optional[RuntimeMeasurement] = None,
                 expected_runtime_baseline: Optional[str] = None,
                 hear_satisfied_by: Optional[str] = None,
                 now: Optional[datetime] = None) -> PaymentVerdict:
        now = now or utcnow()
        reasons: list[PaymentReasonCode] = []

        grant = self.graph.get(intent.authority_grant_id)
        if grant is None:
            return self._deny(intent, [PaymentReasonCode.GRANT_NOT_FOUND],
                              "no such authority grant")

        # 1. Revocation and lifecycle. Checked first: nothing else matters if
        #    the authority is dead or its status is unknown.
        revocation_reason = self.graph.revocation.status(grant)
        if revocation_reason is PaymentReasonCode.REVOCATION_STATUS_UNAVAILABLE:
            # Unknown is not the same as revoked. Value must not move, but a
            # human has to resolve the state rather than the caller retrying.
            return PaymentVerdict(
                decision=PaymentDecision.RECONCILE,
                transaction_intent_id=intent.transaction_intent_id,
                reason_codes=[revocation_reason],
                reasoning="revocation authority unreachable; cannot establish that authority is live",
                policy_id=self.policy_id,
            )
        if revocation_reason is not None:
            return self._deny(intent, [revocation_reason],
                              "authority is revoked or its epoch is stale")
        if grant.is_expired(now):
            return self._deny(intent, [PaymentReasonCode.GRANT_EXPIRED], "grant has expired")

        # 2. Lineage re-verification (APAY-08).
        lineage = self.graph.lineage_violations(grant.authority_grant_id)
        if lineage:
            return self._deny(intent, [PaymentReasonCode.ATTENUATION_VIOLATION],
                              "delegation lineage widens authority: " + ", ".join(lineage))
        if grant.constraints.max_delegation_depth < 0:
            reasons.append(PaymentReasonCode.DELEGATION_DEPTH_EXCEEDED)

        # 3. Unresolved semantic ambiguity blocks spend (APAY-03).
        if grant.unresolved_ambiguities:
            return self._deny(
                intent, [PaymentReasonCode.UNRESOLVED_AMBIGUITY],
                "grant carries unresolved constraint ambiguities: "
                + ", ".join(grant.unresolved_ambiguities),
            )

        # 4. Separation of duties (APAY-07).
        if intent.capability not in grant.capabilities:
            reasons.append(PaymentReasonCode.SEPARATION_OF_DUTIES_VIOLATION)

        # 5. Runtime binding (APAY-05).
        reasons.extend(self._runtime_reasons(grant, runtime, expected_runtime_baseline, now))

        # 6. Freshness and replay (APAY-11).
        if intent.quote_expired(now):
            reasons.append(PaymentReasonCode.QUOTE_EXPIRED)
        reasons.extend(self.replay.check(intent))

        # 7. Transaction continuity (APAY-12).
        if intent.approved_cart_digest is None:
            reasons.append(PaymentReasonCode.INTENT_BINDING_MISSING)
        elif intent.approved_cart_digest != intent.canonical_digest():
            reasons.append(PaymentReasonCode.CART_MUTATED_AFTER_APPROVAL)

        # 8. Counterparty provenance (APAY-15).
        reasons.extend(self.counterparties.check(intent))

        # 9. Per-transaction constraints (APAY-04).
        reasons.extend(self._constraint_reasons(grant, intent))

        # 10. Downgrade resistance (APAY-14).
        if int(intent.path_assurance) < int(grant.constraints.min_assurance):
            reasons.append(PaymentReasonCode.ASSURANCE_DOWNGRADE)

        # 11. Aggregate containment and velocity (APAY-09 / APAY-10).
        reasons.extend(self.graph.ceiling_violations(grant, intent.amount, now=now))
        reasons.extend(self.graph.velocity_violations(grant, intent.amount,
                                                      intent.merchant_id, now=now))

        # 12. Consequence classification and HEAR (APAY-01 / CP.10).
        known_destinations = self.counterparties._destinations.get(intent.merchant_id, set())
        novel_destination = bool(intent.destination) and intent.destination not in known_destinations
        consequence = self._consequence(intent, novel_destination)

        hear_required = False
        hear_above = grant.constraints.hear_above
        if hear_above is not None and hear_above.currency == intent.amount.currency:
            hear_required = intent.amount.minor_units >= hear_above.minor_units
        if consequence in (ConsequenceClass.CONSEQUENTIAL, ConsequenceClass.CRITICAL):
            hear_required = True
        if hear_required and not hear_satisfied_by:
            reasons.append(PaymentReasonCode.HEAR_REQUIRED)

        # ── Verdict assembly ────────────────────────────────────────────────
        deduped = list(dict.fromkeys(reasons))
        if not deduped:
            return PaymentVerdict(
                decision=PaymentDecision.ALLOW,
                transaction_intent_id=intent.transaction_intent_id,
                reasoning="all CP.5.APAY constraints satisfied",
                policy_id=self.policy_id,
                consequence=consequence,
            )

        # Ambiguous state escalates to governed reconciliation rather than deny,
        # because a denied-but-possibly-settled transaction still needs a human.
        ambiguous = {
            PaymentReasonCode.REVOCATION_STATUS_UNAVAILABLE,
            PaymentReasonCode.SETTLEMENT_AMBIGUOUS,
        }
        if any(code in ambiguous for code in deduped):
            decision = PaymentDecision.RECONCILE
        elif deduped == [PaymentReasonCode.HEAR_REQUIRED]:
            decision = PaymentDecision.ESCALATE
        else:
            decision = PaymentDecision.DENY

        return PaymentVerdict(
            decision=decision,
            transaction_intent_id=intent.transaction_intent_id,
            reason_codes=deduped,
            reasoning="; ".join(c.value for c in deduped),
            policy_id=self.policy_id,
            consequence=consequence,
        )

    # ── Rule groups ──────────────────────────────────────────────────────────

    def _runtime_reasons(self, grant: AuthorityGrant,
                         runtime: Optional[RuntimeMeasurement],
                         expected_baseline: Optional[str],
                         now: datetime) -> list[PaymentReasonCode]:
        floor = grant.constraints.min_assurance
        if floor < AssuranceLevel.RUNTIME_BOUND:
            return []  # deployment has accepted a lower floor; nothing to check here
        if runtime is None:
            return [PaymentReasonCode.NO_RUNTIME_MEASUREMENT]
        out: list[PaymentReasonCode] = []
        if not runtime.attested or runtime.attestation_method in {"none", "declared"}:
            out.append(PaymentReasonCode.RUNTIME_NOT_ATTESTED)
        if not runtime.is_fresh(now):
            out.append(PaymentReasonCode.RUNTIME_MEASUREMENT_STALE)
        if expected_baseline is not None and runtime.baseline_digest() != expected_baseline:
            out.append(PaymentReasonCode.RUNTIME_BASELINE_MISMATCH)
        return out

    def _constraint_reasons(self, grant: AuthorityGrant,
                            intent: TransactionIntent) -> list[PaymentReasonCode]:
        c = grant.constraints
        out: list[PaymentReasonCode] = []

        if c.max_transaction is not None:
            if c.max_transaction.currency != intent.amount.currency:
                out.append(PaymentReasonCode.CURRENCY_NOT_PERMITTED)
            elif intent.amount.minor_units > c.max_transaction.minor_units:
                out.append(PaymentReasonCode.AMOUNT_EXCEEDS_GRANT)
        if c.currencies is not None and intent.amount.currency not in c.currencies:
            out.append(PaymentReasonCode.CURRENCY_NOT_PERMITTED)
        if intent.merchant_id in c.denied_merchants:
            out.append(PaymentReasonCode.MERCHANT_NOT_PERMITTED)
        elif c.allowed_merchants is not None and intent.merchant_id not in c.allowed_merchants:
            out.append(PaymentReasonCode.MERCHANT_NOT_PERMITTED)
        if c.allowed_categories is not None and intent.category not in c.allowed_categories:
            out.append(PaymentReasonCode.CATEGORY_NOT_PERMITTED)
        if c.allowed_geographies is not None and intent.geography not in c.allowed_geographies:
            out.append(PaymentReasonCode.GEOGRAPHY_NOT_PERMITTED)
        if c.allowed_rails is not None and intent.rail not in c.allowed_rails:
            out.append(PaymentReasonCode.RAIL_NOT_PERMITTED)
        if c.allowed_destinations is not None:
            if intent.destination is None or intent.destination not in c.allowed_destinations:
                out.append(PaymentReasonCode.DESTINATION_SUBSTITUTED)
        if c.allowed_facilitators is not None:
            if intent.facilitator is None or intent.facilitator not in c.allowed_facilitators:
                out.append(PaymentReasonCode.FACILITATOR_NOT_TRUSTED)
        if intent.recurring and not c.recurrence_allowed:
            out.append(PaymentReasonCode.RECURRENCE_NOT_PERMITTED)

        order = {
            SettlementFinality.REVERSIBLE: 0,
            SettlementFinality.MEDIATED: 1,
            SettlementFinality.IRREVERSIBLE: 2,
        }
        if order[intent.finality] > order[c.max_finality]:
            out.append(PaymentReasonCode.RAIL_NOT_PERMITTED)
        return out

    def _consequence(self, intent: TransactionIntent,
                     novel_destination: bool) -> ConsequenceClass:
        from nexus_sdk.payments.mandate import classify_consequence
        return classify_consequence(
            intent.amount, intent.finality,
            novel_destination=novel_destination,
            critical_threshold=self.critical_threshold,
        )

    def _deny(self, intent: TransactionIntent, codes: list[PaymentReasonCode],
              reasoning: str) -> PaymentVerdict:
        return PaymentVerdict(
            decision=PaymentDecision.DENY,
            transaction_intent_id=intent.transaction_intent_id,
            reason_codes=codes,
            reasoning=reasoning,
            policy_id=self.policy_id,
        )
