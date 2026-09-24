"""
nexus_sdk/payments/objects.py
CP.5.APAY protocol-independent object model.

DESIGN RULE (AI SAFE2 protocol-independence):
    Controls bind to framework-owned constructs, never to protocol-owned
    sessions or vendor tokens. AP2 mandates, x402 payment payloads, Visa TAP
    signatures, Mastercard Agentic Tokens and KYA-OS delegations are all
    *adapters onto* these objects. None of them are the object of record.

The seven canonical identifiers:
    principal_id            who is ultimately accountable (human or org)
    authority_grant_id      the framework-owned mandate
    delegation_chain_id     lineage root for the authority tree
    runtime_measurement_id  what workload is executing right now
    policy_id               which deterministic ruleset decided
    transaction_intent_id   what this specific movement of value is for
    revocation_epoch        monotonic counter; stale epoch == no authority

Reference: NEXUS-A2A v0.4, AI SAFE2 v3.1 CP.4 / CP.5 / CP.9 / CP.10
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Optional

__all__ = [
    "AssuranceLevel",
    "ConsequenceClass",
    "PaymentRail",
    "SettlementFinality",
    "PaymentDecision",
    "PaymentReasonCode",
    "Money",
    "PrincipalBinding",
    "RuntimeMeasurement",
    "AuthorityConstraints",
    "AuthorityGrant",
    "TransactionIntent",
    "CanonicalTransaction",
    "canonical_hash",
    "utcnow",
    "parse_ts",
]


# ── Time helpers ──────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_ts(value: str | datetime | None) -> Optional[datetime]:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def canonical_hash(payload: Any) -> str:
    """SHA-256 over canonical JSON. The single hashing rule for all APAY objects.

    Canonicalization: sorted keys, no insignificant whitespace, Decimal rendered
    as its exact string form. Two systems computing this over the same logical
    object MUST produce the same digest, or transaction binding is meaningless.
    """
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


# ── Enumerations ──────────────────────────────────────────────────────────────

class AssuranceLevel(int, Enum):
    """Minimum assurance of the execution path. Ordered; higher is stronger.

    This is the anti-downgrade axis (APAY-14). A grant declares its floor; any
    path offering less is refused rather than silently accepted. An agent that
    can fall back to guest checkout has no controls at all.
    """
    NONE = 0              # anonymous / guest checkout / static bearer
    BEARER = 1            # long-lived shared secret, no proof of possession
    SIGNED_REQUEST = 2    # HTTP Message Signatures (Web Bot Auth / Visa TAP class)
    MANDATE_BOUND = 3     # signed mandate bound to a specific cart (AP2 class)
    RUNTIME_BOUND = 4     # mandate + fresh workload measurement (CP.5.APAY floor)

    @classmethod
    def coerce(cls, value: "AssuranceLevel | int | str") -> "AssuranceLevel":
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[str(value).upper()]


class ConsequenceClass(str, Enum):
    """Impact tier of a value movement. Drives HEAR requirements (APAY-01/CP.10)."""
    ROUTINE = "routine"            # bounded, reversible, low value
    MATERIAL = "material"          # meaningful spend or a new counterparty
    CONSEQUENTIAL = "consequential"  # irreversible rail, high value, or novel destination
    CRITICAL = "critical"          # treasury movement, key rotation, account control


class PaymentRail(str, Enum):
    CARD_NETWORK = "card_network"
    BANK_TRANSFER = "bank_transfer"
    STABLECOIN = "stablecoin"
    ACCOUNT_BALANCE = "account_balance"
    INVOICE_CREDIT = "invoice_credit"


class SettlementFinality(str, Enum):
    """Whether recourse exists after settlement. Drives consequence classification.

    Native on-chain settlement generally lacks card-style chargebacks. Application
    layers (escrow, lock periods, mediated refunds) can restore recourse above an
    irreversible rail, so finality is a property of the *path*, not the rail alone.
    """
    REVERSIBLE = "reversible"        # chargeback / dispute rights available
    MEDIATED = "mediated"            # escrow, lock period, or contractual remedy
    IRREVERSIBLE = "irreversible"    # no recourse once settled


class PaymentDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"      # requires HEAR / named human authority
    RECONCILE = "reconcile"    # ambiguous state: governed reconciliation, never blind retry


class PaymentReasonCode(str, Enum):
    """Stable machine codes. Adjudicators and dashboards key on these, not prose."""
    # Identity / principal
    NO_PRINCIPAL_BINDING = "NO_PRINCIPAL_BINDING"
    NO_OWNER_OF_RECORD = "NO_OWNER_OF_RECORD"
    # Grant lifecycle
    GRANT_NOT_FOUND = "GRANT_NOT_FOUND"
    GRANT_EXPIRED = "GRANT_EXPIRED"
    GRANT_REVOKED = "GRANT_REVOKED"
    STALE_REVOCATION_EPOCH = "STALE_REVOCATION_EPOCH"
    REVOCATION_STATUS_UNAVAILABLE = "REVOCATION_STATUS_UNAVAILABLE"
    # Delegation
    ATTENUATION_VIOLATION = "ATTENUATION_VIOLATION"
    DELEGATION_DEPTH_EXCEEDED = "DELEGATION_DEPTH_EXCEEDED"
    ORPHANED_GRANT = "ORPHANED_GRANT"
    # Constraints
    AMOUNT_EXCEEDS_GRANT = "AMOUNT_EXCEEDS_GRANT"
    CURRENCY_NOT_PERMITTED = "CURRENCY_NOT_PERMITTED"
    MERCHANT_NOT_PERMITTED = "MERCHANT_NOT_PERMITTED"
    CATEGORY_NOT_PERMITTED = "CATEGORY_NOT_PERMITTED"
    GEOGRAPHY_NOT_PERMITTED = "GEOGRAPHY_NOT_PERMITTED"
    RAIL_NOT_PERMITTED = "RAIL_NOT_PERMITTED"
    RECURRENCE_NOT_PERMITTED = "RECURRENCE_NOT_PERMITTED"
    TRANSACTION_COUNT_EXCEEDED = "TRANSACTION_COUNT_EXCEEDED"
    # Aggregate economics
    AGGREGATE_CEILING_EXCEEDED = "AGGREGATE_CEILING_EXCEEDED"
    WINDOW_CEILING_EXCEEDED = "WINDOW_CEILING_EXCEEDED"
    # Velocity / anomaly
    VELOCITY_ANOMALY = "VELOCITY_ANOMALY"
    MICRO_DRAIN_SUSPECTED = "MICRO_DRAIN_SUSPECTED"
    MERCHANT_DISPERSION_ANOMALY = "MERCHANT_DISPERSION_ANOMALY"
    SPLIT_TRANSACTION_SUSPECTED = "SPLIT_TRANSACTION_SUSPECTED"
    # Runtime
    NO_RUNTIME_MEASUREMENT = "NO_RUNTIME_MEASUREMENT"
    RUNTIME_NOT_ATTESTED = "RUNTIME_NOT_ATTESTED"
    RUNTIME_MEASUREMENT_STALE = "RUNTIME_MEASUREMENT_STALE"
    RUNTIME_BASELINE_MISMATCH = "RUNTIME_BASELINE_MISMATCH"
    # Integrity / continuity
    INTENT_BINDING_MISSING = "INTENT_BINDING_MISSING"
    CART_MUTATED_AFTER_APPROVAL = "CART_MUTATED_AFTER_APPROVAL"
    DESTINATION_SUBSTITUTED = "DESTINATION_SUBSTITUTED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    NONCE_MISSING = "NONCE_MISSING"
    QUOTE_EXPIRED = "QUOTE_EXPIRED"
    # Path
    ASSURANCE_DOWNGRADE = "ASSURANCE_DOWNGRADE"
    FACILITATOR_NOT_TRUSTED = "FACILITATOR_NOT_TRUSTED"
    COUNTERPARTY_UNVERIFIED = "COUNTERPARTY_UNVERIFIED"
    # Human authority
    HEAR_REQUIRED = "HEAR_REQUIRED"
    HUMAN_APPROVAL_UNAVAILABLE = "HUMAN_APPROVAL_UNAVAILABLE"
    SEPARATION_OF_DUTIES_VIOLATION = "SEPARATION_OF_DUTIES_VIOLATION"
    # Semantic
    UNRESOLVED_AMBIGUITY = "UNRESOLVED_AMBIGUITY"
    CONSTRAINT_CONFLICT = "CONSTRAINT_CONFLICT"
    # Fail-safe
    FAIL_CLOSED_DEFAULT = "FAIL_CLOSED_DEFAULT"
    SETTLEMENT_AMBIGUOUS = "SETTLEMENT_AMBIGUOUS"
    EXPOSURE_RESERVATION_FAILED = "EXPOSURE_RESERVATION_FAILED"
    ATTESTATION_VERIFICATION_FAILED = "ATTESTATION_VERIFICATION_FAILED"


# ── Money ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Money:
    """Exact minor-unit money. Never float.

    Floating point in a spend ceiling is a vulnerability, not a rounding quirk:
    accumulated error is exactly the signal a micro-drain attack hides inside.
    """
    minor_units: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not isinstance(self.minor_units, int):
            raise TypeError("Money.minor_units must be int (minor units, e.g. cents)")
        if self.minor_units < 0:
            raise ValueError("Money.minor_units must be non-negative")
        if not self.currency or len(self.currency) > 12:
            raise ValueError("Money.currency must be a short currency code")

    @classmethod
    def parse(cls, value: str | float | Decimal, currency: str = "USD",
              exponent: int = 2) -> "Money":
        """Parse a major-unit amount into exact minor units."""
        try:
            d = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"unparseable amount: {value!r}") from exc
        scaled = d * (Decimal(10) ** exponent)
        if scaled != scaled.to_integral_value():
            raise ValueError(f"amount {value!r} has more precision than {currency} allows")
        return cls(int(scaled), currency)

    def _same(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"currency mismatch: {self.currency} vs {other.currency}; "
                "cross-currency comparison requires an explicit converted ceiling"
            )

    def __add__(self, other: "Money") -> "Money":
        self._same(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def __le__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor_units <= other.minor_units

    def __lt__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor_units < other.minor_units

    def to_dict(self) -> dict:
        return {"minor_units": self.minor_units, "currency": self.currency}

    def __str__(self) -> str:
        return f"{self.minor_units / 100:.2f} {self.currency}"


# ── Principal ─────────────────────────────────────────────────────────────────

@dataclass
class PrincipalBinding:
    """APAY-01. Links a payment-capable agent to accountable humans.

    `owner_of_record` satisfies AISM I-5 and is non-optional: an agent that can
    move money with no named accountable human is refused at registration, not
    at transaction time.
    """
    principal_id: str
    owner_of_record: str
    agent_did: str
    act_tier: int = 2
    hear_authority: Optional[str] = None       # named human interrupt authority (CP.10)
    identity_sources: list[str] = field(default_factory=list)  # entra|kya-os|spiffe|web-bot-auth
    spiffe_id: Optional[str] = None
    verified_at: str = field(default_factory=lambda: utcnow().isoformat())

    def validate(self) -> list[str]:
        v: list[str] = []
        if not self.principal_id:
            v.append(PaymentReasonCode.NO_PRINCIPAL_BINDING.value)
        if not self.owner_of_record:
            v.append(PaymentReasonCode.NO_OWNER_OF_RECORD.value)
        if not self.agent_did:
            v.append(PaymentReasonCode.NO_PRINCIPAL_BINDING.value)
        return v

    def to_dict(self) -> dict:
        return {
            "principal_id": self.principal_id,
            "owner_of_record": self.owner_of_record,
            "agent_did": self.agent_did,
            "act_tier": self.act_tier,
            "hear_authority": self.hear_authority,
            "identity_sources": sorted(self.identity_sources),
            "spiffe_id": self.spiffe_id,
            "verified_at": self.verified_at,
        }


# ── Runtime measurement ───────────────────────────────────────────────────────

@dataclass
class RuntimeMeasurement:
    """APAY-05. What is actually executing, measured, with an expiry.

    Identity answers "which agent arrived". This answers "is that agent still
    the software we approved, right now". A measurement without freshness is a
    claim about the past being used to authorize the present.
    """
    runtime_measurement_id: str = field(default_factory=lambda: f"rtm_{uuid.uuid4().hex[:20]}")
    workload_id: Optional[str] = None            # SPIFFE ID or equivalent instance identity
    attested: bool = False                       # was this produced by a hardware/verified root
    attestation_method: str = "none"             # tpm|tee|sev-snp|tdx|nitro|spiffe-svid|declared
    artifact_digest: Optional[str] = None        # agent image / package digest
    model_id: Optional[str] = None
    prompt_digest: Optional[str] = None
    policy_id: Optional[str] = None
    tool_inventory_digest: Optional[str] = None  # AgBOM chain digest
    memory_baseline_digest: Optional[str] = None
    measured_at: str = field(default_factory=lambda: utcnow().isoformat())
    max_age_seconds: int = 300
    verifier_challenge: Optional[str] = None
    attestation_evidence: Optional[str] = None
    attestation_signer: Optional[str] = None

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        now = now or utcnow()
        measured = parse_ts(self.measured_at)
        assert measured is not None
        return (now - measured).total_seconds()

    def is_fresh(self, now: Optional[datetime] = None) -> bool:
        return self.age_seconds(now) <= self.max_age_seconds

    def baseline_digest(self) -> str:
        """Digest over the fields a baseline pins. Changing any of them is a new runtime."""
        return canonical_hash({
            "artifact_digest": self.artifact_digest,
            "model_id": self.model_id,
            "prompt_digest": self.prompt_digest,
            "policy_id": self.policy_id,
            "tool_inventory_digest": self.tool_inventory_digest,
            "memory_baseline_digest": self.memory_baseline_digest,
        })

    def assurance(self) -> AssuranceLevel:
        if self.attested and self.attestation_method not in {"none", "declared"}:
            return AssuranceLevel.RUNTIME_BOUND
        return AssuranceLevel.MANDATE_BOUND

    def to_dict(self) -> dict:
        return {
            "runtime_measurement_id": self.runtime_measurement_id,
            "workload_id": self.workload_id,
            "attested": self.attested,
            "attestation_method": self.attestation_method,
            "artifact_digest": self.artifact_digest,
            "model_id": self.model_id,
            "prompt_digest": self.prompt_digest,
            "policy_id": self.policy_id,
            "tool_inventory_digest": self.tool_inventory_digest,
            "memory_baseline_digest": self.memory_baseline_digest,
            "measured_at": self.measured_at,
            "max_age_seconds": self.max_age_seconds,
            "verifier_challenge": self.verifier_challenge,
            "attestation_evidence": self.attestation_evidence,
            "attestation_signer": self.attestation_signer,
            "baseline_digest": self.baseline_digest(),
        }


# ── Authority constraints ─────────────────────────────────────────────────────

_UNSET = object()


@dataclass
class AuthorityConstraints:
    """The deterministic, machine-checkable envelope of what may be spent.

    Every field is an attenuation axis. `None` on a set-valued field means
    "unconstrained on this axis" and is treated as the universal set during
    monotonicity checks, which is why a child with `None` under a constrained
    parent is a violation rather than an inheritance.
    """
    max_transaction: Optional[Money] = None
    max_aggregate: Optional[Money] = None
    currencies: Optional[set[str]] = None
    allowed_merchants: Optional[set[str]] = None
    denied_merchants: set[str] = field(default_factory=set)
    allowed_categories: Optional[set[str]] = None
    allowed_geographies: Optional[set[str]] = None
    allowed_rails: Optional[set[PaymentRail]] = None
    allowed_facilitators: Optional[set[str]] = None
    allowed_destinations: Optional[set[str]] = None   # payee/settlement addresses
    min_assurance: AssuranceLevel = AssuranceLevel.RUNTIME_BOUND
    max_finality: SettlementFinality = SettlementFinality.IRREVERSIBLE
    recurrence_allowed: bool = False
    max_transactions: Optional[int] = None
    max_delegation_depth: int = 2
    window_seconds: Optional[int] = None
    window_max: Optional[Money] = None
    not_after: Optional[str] = None
    hear_above: Optional[Money] = None   # spend above this needs named human authority

    # ── Attenuation ──────────────────────────────────────────────────────────

    @staticmethod
    def _subset(child: Optional[set], parent: Optional[set]) -> bool:
        if parent is None:
            return True            # parent unconstrained: anything is narrower or equal
        if child is None:
            return False           # child unconstrained under constrained parent: widening
        return set(child).issubset(set(parent))

    @staticmethod
    def _money_le(child: Optional[Money], parent: Optional[Money]) -> bool:
        if parent is None:
            return True
        if child is None:
            return False
        if child.currency != parent.currency:
            return False
        return child.minor_units <= parent.minor_units

    def attenuation_violations(self, parent: "AuthorityConstraints") -> list[str]:
        """APAY-08. Returns the axes on which this grant widens its parent.

        Empty list means monotonic narrowing holds on every axis.
        """
        v: list[str] = []
        if not self._money_le(self.max_transaction, parent.max_transaction):
            v.append("max_transaction")
        if not self._money_le(self.max_aggregate, parent.max_aggregate):
            v.append("max_aggregate")
        if not self._money_le(self.window_max, parent.window_max):
            v.append("window_max")
        if not self._subset(self.currencies, parent.currencies):
            v.append("currencies")
        if not self._subset(self.allowed_merchants, parent.allowed_merchants):
            v.append("allowed_merchants")
        if not self._subset(self.allowed_categories, parent.allowed_categories):
            v.append("allowed_categories")
        if not self._subset(self.allowed_geographies, parent.allowed_geographies):
            v.append("allowed_geographies")
        if not self._subset(self.allowed_rails, parent.allowed_rails):
            v.append("allowed_rails")
        if not self._subset(self.allowed_facilitators, parent.allowed_facilitators):
            v.append("allowed_facilitators")
        if not self._subset(self.allowed_destinations, parent.allowed_destinations):
            v.append("allowed_destinations")
        # A child may never forget a parent's deny list.
        if not parent.denied_merchants.issubset(self.denied_merchants):
            v.append("denied_merchants")
        # Assurance floor may rise, never fall.
        if int(self.min_assurance) < int(parent.min_assurance):
            v.append("min_assurance")
        # Finality tolerance may tighten, never loosen.
        _order = {
            SettlementFinality.REVERSIBLE: 0,
            SettlementFinality.MEDIATED: 1,
            SettlementFinality.IRREVERSIBLE: 2,
        }
        if _order[self.max_finality] > _order[parent.max_finality]:
            v.append("max_finality")
        if self.recurrence_allowed and not parent.recurrence_allowed:
            v.append("recurrence_allowed")
        if parent.max_transactions is not None:
            if self.max_transactions is None or self.max_transactions > parent.max_transactions:
                v.append("max_transactions")
        if self.max_delegation_depth > max(parent.max_delegation_depth - 1, 0):
            v.append("max_delegation_depth")
        # HEAR threshold may only get stricter (lower), never looser.
        if parent.hear_above is not None:
            if self.hear_above is None or not self._money_le(self.hear_above, parent.hear_above):
                v.append("hear_above")
        # Expiry may only shorten.
        p_exp, c_exp = parse_ts(parent.not_after), parse_ts(self.not_after)
        if p_exp is not None and (c_exp is None or c_exp > p_exp):
            v.append("not_after")
        return v

    def attenuate(self, **overrides: Any) -> "AuthorityConstraints":
        """Produce a child constraint set guaranteed to be narrower or equal.

        Unspecified axes are inherited verbatim; specified axes are intersected
        with the parent rather than replaced, so an attempted widening narrows
        to the parent's bound instead of being accepted.
        """
        child = AuthorityConstraints(
            max_transaction=self.max_transaction,
            max_aggregate=self.max_aggregate,
            currencies=set(self.currencies) if self.currencies is not None else None,
            allowed_merchants=set(self.allowed_merchants) if self.allowed_merchants is not None else None,
            denied_merchants=set(self.denied_merchants),
            allowed_categories=set(self.allowed_categories) if self.allowed_categories is not None else None,
            allowed_geographies=set(self.allowed_geographies) if self.allowed_geographies is not None else None,
            allowed_rails=set(self.allowed_rails) if self.allowed_rails is not None else None,
            allowed_facilitators=set(self.allowed_facilitators) if self.allowed_facilitators is not None else None,
            allowed_destinations=set(self.allowed_destinations) if self.allowed_destinations is not None else None,
            min_assurance=self.min_assurance,
            max_finality=self.max_finality,
            recurrence_allowed=self.recurrence_allowed,
            max_transactions=self.max_transactions,
            max_delegation_depth=max(self.max_delegation_depth - 1, 0),
            window_seconds=self.window_seconds,
            window_max=self.window_max,
            not_after=self.not_after,
            hear_above=self.hear_above,
        )
        for key, value in overrides.items():
            if not hasattr(child, key):
                raise AttributeError(f"unknown constraint axis: {key}")
            setattr(child, key, value)
        # Intersect rather than trust: the result is clamped to this grant.
        child._clamp_to(self)
        return child

    def _clamp_to(self, parent: "AuthorityConstraints") -> None:
        def clamp_money(c: Optional[Money], p: Optional[Money]) -> Optional[Money]:
            if p is None:
                return c
            if c is None or c.currency != p.currency:
                return p
            return c if c.minor_units <= p.minor_units else p

        def clamp_set(c: Optional[set], p: Optional[set]) -> Optional[set]:
            if p is None:
                return c
            return set(p) if c is None else set(c) & set(p)

        self.max_transaction = clamp_money(self.max_transaction, parent.max_transaction)
        self.max_aggregate = clamp_money(self.max_aggregate, parent.max_aggregate)
        self.window_max = clamp_money(self.window_max, parent.window_max)
        self.hear_above = clamp_money(self.hear_above, parent.hear_above)
        self.currencies = clamp_set(self.currencies, parent.currencies)
        self.allowed_merchants = clamp_set(self.allowed_merchants, parent.allowed_merchants)
        self.allowed_categories = clamp_set(self.allowed_categories, parent.allowed_categories)
        self.allowed_geographies = clamp_set(self.allowed_geographies, parent.allowed_geographies)
        self.allowed_rails = clamp_set(self.allowed_rails, parent.allowed_rails)
        self.allowed_facilitators = clamp_set(self.allowed_facilitators, parent.allowed_facilitators)
        self.allowed_destinations = clamp_set(self.allowed_destinations, parent.allowed_destinations)
        self.denied_merchants = set(self.denied_merchants) | set(parent.denied_merchants)
        self.min_assurance = AssuranceLevel(max(int(self.min_assurance), int(parent.min_assurance)))
        _order = {
            SettlementFinality.REVERSIBLE: 0,
            SettlementFinality.MEDIATED: 1,
            SettlementFinality.IRREVERSIBLE: 2,
        }
        if _order[self.max_finality] > _order[parent.max_finality]:
            self.max_finality = parent.max_finality
        self.recurrence_allowed = self.recurrence_allowed and parent.recurrence_allowed
        if parent.max_transactions is not None:
            self.max_transactions = (
                parent.max_transactions if self.max_transactions is None
                else min(self.max_transactions, parent.max_transactions)
            )
        self.max_delegation_depth = min(self.max_delegation_depth,
                                        max(parent.max_delegation_depth - 1, 0))
        p_exp, c_exp = parse_ts(parent.not_after), parse_ts(self.not_after)
        if p_exp is not None and (c_exp is None or c_exp > p_exp):
            self.not_after = parent.not_after

    def to_dict(self) -> dict:
        def s(v: Optional[set]) -> Optional[list]:
            return None if v is None else sorted(str(x.value if isinstance(x, Enum) else x) for x in v)

        return {
            "max_transaction": self.max_transaction.to_dict() if self.max_transaction else None,
            "max_aggregate": self.max_aggregate.to_dict() if self.max_aggregate else None,
            "window_max": self.window_max.to_dict() if self.window_max else None,
            "window_seconds": self.window_seconds,
            "currencies": s(self.currencies),
            "allowed_merchants": s(self.allowed_merchants),
            "denied_merchants": s(self.denied_merchants),
            "allowed_categories": s(self.allowed_categories),
            "allowed_geographies": s(self.allowed_geographies),
            "allowed_rails": s(self.allowed_rails),
            "allowed_facilitators": s(self.allowed_facilitators),
            "allowed_destinations": s(self.allowed_destinations),
            "min_assurance": int(self.min_assurance),
            "max_finality": self.max_finality.value,
            "recurrence_allowed": self.recurrence_allowed,
            "max_transactions": self.max_transactions,
            "max_delegation_depth": self.max_delegation_depth,
            "not_after": self.not_after,
            "hear_above": self.hear_above.to_dict() if self.hear_above else None,
        }


# ── Authority grant ───────────────────────────────────────────────────────────

@dataclass
class AuthorityGrant:
    """The framework-owned mandate. Protocol mandates bind *to* this, not vice versa.

    `instruction_digest` and `normalized_constraints_digest` together satisfy
    APAY-03: the evidence bundle can show both what the principal originally
    said and what deterministic constraints were derived from it, so an
    adjudicator can see where a translation error entered without trusting the
    agent's own account of its reasoning.
    """
    principal_id: str
    constraints: AuthorityConstraints
    authority_grant_id: str = field(default_factory=lambda: f"grant_{uuid.uuid4().hex[:24]}")
    delegation_chain_id: Optional[str] = None
    parent_grant_id: Optional[str] = None
    depth: int = 0
    agent_did: Optional[str] = None
    issued_at: str = field(default_factory=lambda: utcnow().isoformat())
    revocation_epoch: int = 0
    instruction_ref: Optional[str] = None
    instruction_digest: Optional[str] = None
    normalized_constraints_digest: Optional[str] = None
    unresolved_ambiguities: list[str] = field(default_factory=list)
    approved_by: Optional[str] = None            # who approved the rendering (APAY-02)
    approval_surface: Optional[str] = None       # which trusted surface rendered it
    capabilities: set[str] = field(
        default_factory=lambda: {"payment.execute"}
    )  # APAY-07 separation of duties; an explicit empty set carries no authority
    revoked: bool = False

    def __post_init__(self) -> None:
        if self.delegation_chain_id is None:
            self.delegation_chain_id = f"chain_{uuid.uuid4().hex[:20]}"
        if self.normalized_constraints_digest is None:
            self.normalized_constraints_digest = canonical_hash(self.constraints.to_dict())

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if not self.constraints.not_after:
            return False
        return (now or utcnow()) > parse_ts(self.constraints.not_after)  # type: ignore[operator]

    def grant_digest(self) -> str:
        return canonical_hash({
            "authority_grant_id": self.authority_grant_id,
            "principal_id": self.principal_id,
            "delegation_chain_id": self.delegation_chain_id,
            "parent_grant_id": self.parent_grant_id,
            "depth": self.depth,
            "constraints": self.constraints.to_dict(),
            "revocation_epoch": self.revocation_epoch,
            "instruction_digest": self.instruction_digest,
            "capabilities": sorted(self.capabilities),
        })

    def to_dict(self) -> dict:
        return {
            "authority_grant_id": self.authority_grant_id,
            "delegation_chain_id": self.delegation_chain_id,
            "parent_grant_id": self.parent_grant_id,
            "depth": self.depth,
            "principal_id": self.principal_id,
            "agent_did": self.agent_did,
            "issued_at": self.issued_at,
            "revocation_epoch": self.revocation_epoch,
            "revoked": self.revoked,
            "instruction_ref": self.instruction_ref,
            "instruction_digest": self.instruction_digest,
            "normalized_constraints_digest": self.normalized_constraints_digest,
            "unresolved_ambiguities": list(self.unresolved_ambiguities),
            "approved_by": self.approved_by,
            "approval_surface": self.approval_surface,
            "capabilities": sorted(self.capabilities),
            "constraints": self.constraints.to_dict(),
            "grant_digest": self.grant_digest(),
        }


# ── Transaction ───────────────────────────────────────────────────────────────

@dataclass
class TransactionIntent:
    """What the agent proposes to do with value, before any policy runs."""
    authority_grant_id: str
    amount: Money
    merchant_id: str
    transaction_intent_id: str = field(default_factory=lambda: f"txi_{uuid.uuid4().hex[:24]}")
    merchant_verified: bool = False
    merchant_baseline_digest: Optional[str] = None
    destination: Optional[str] = None
    category: Optional[str] = None
    geography: Optional[str] = None
    rail: PaymentRail = PaymentRail.CARD_NETWORK
    finality: SettlementFinality = SettlementFinality.REVERSIBLE
    facilitator: Optional[str] = None
    path_assurance: AssuranceLevel = AssuranceLevel.NONE
    recurring: bool = False
    line_items: list[dict] = field(default_factory=list)
    quote_expires_at: Optional[str] = None
    nonce: Optional[str] = None
    idempotency_key: Optional[str] = None
    approved_cart_digest: Optional[str] = None   # digest shown on the trusted surface
    requested_at: str = field(default_factory=lambda: utcnow().isoformat())
    capability: str = "payment.execute"

    def __post_init__(self) -> None:
        if self.idempotency_key is None:
            self.idempotency_key = f"idem_{canonical_hash(self.canonical_fields())[:32]}"

    def canonical_fields(self) -> dict:
        """The fields that define *this* transaction. Any change is a new transaction.

        This is the TOCTOU boundary (APAY-12). Anything outside this set may
        drift between approval and settlement without re-authorization; anything
        inside it may not.
        """
        return {
            "amount": self.amount.to_dict(),
            "merchant_id": self.merchant_id,
            "destination": self.destination,
            "category": self.category,
            "geography": self.geography,
            "rail": self.rail.value,
            "finality": self.finality.value,
            "facilitator": self.facilitator,
            "path_assurance": int(self.path_assurance),
            "recurring": self.recurring,
            "quote_expires_at": self.quote_expires_at,
            "capability": self.capability,
            "merchant_verified": self.merchant_verified,
            "merchant_baseline_digest": self.merchant_baseline_digest,
            "line_items": sorted(
                json.dumps(li, sort_keys=True, default=str) for li in self.line_items
            ),
        }

    def canonical_digest(self) -> str:
        return canonical_hash(self.canonical_fields())

    def quote_expired(self, now: Optional[datetime] = None) -> bool:
        if not self.quote_expires_at:
            return False
        return (now or utcnow()) > parse_ts(self.quote_expires_at)  # type: ignore[operator]

    def to_dict(self) -> dict:
        return {
            "transaction_intent_id": self.transaction_intent_id,
            "authority_grant_id": self.authority_grant_id,
            "amount": self.amount.to_dict(),
            "merchant_id": self.merchant_id,
            "merchant_verified": self.merchant_verified,
            "merchant_baseline_digest": self.merchant_baseline_digest,
            "destination": self.destination,
            "category": self.category,
            "geography": self.geography,
            "rail": self.rail.value,
            "finality": self.finality.value,
            "facilitator": self.facilitator,
            "path_assurance": int(self.path_assurance),
            "recurring": self.recurring,
            "line_items": self.line_items,
            "quote_expires_at": self.quote_expires_at,
            "nonce": self.nonce,
            "idempotency_key": self.idempotency_key,
            "approved_cart_digest": self.approved_cart_digest,
            "requested_at": self.requested_at,
            "capability": self.capability,
            "canonical_digest": self.canonical_digest(),
        }


@dataclass
class CanonicalTransaction:
    """The only object a credential broker will ever sign (APAY-06 / APAY-16).

    The broker signs this, not the agent's request. If the agent wants different
    terms it must obtain a different policy decision; it cannot reach the signer
    directly, so there is no path from a compromised model to a signature over
    terms the policy engine never saw.
    """
    transaction_intent_id: str
    authority_grant_id: str
    delegation_chain_id: str
    principal_id: str
    policy_id: str
    runtime_measurement_id: str
    revocation_epoch: int
    canonical_digest: str
    amount: Money
    merchant_id: str
    destination: Optional[str]
    rail: PaymentRail
    idempotency_key: str
    decided_at: str = field(default_factory=lambda: utcnow().isoformat())
    finality: SettlementFinality = SettlementFinality.REVERSIBLE

    def to_dict(self) -> dict:
        return {
            "transaction_intent_id": self.transaction_intent_id,
            "authority_grant_id": self.authority_grant_id,
            "delegation_chain_id": self.delegation_chain_id,
            "principal_id": self.principal_id,
            "policy_id": self.policy_id,
            "runtime_measurement_id": self.runtime_measurement_id,
            "revocation_epoch": self.revocation_epoch,
            "canonical_digest": self.canonical_digest,
            "amount": self.amount.to_dict(),
            "merchant_id": self.merchant_id,
            "destination": self.destination,
            "rail": self.rail.value,
            "idempotency_key": self.idempotency_key,
            "decided_at": self.decided_at,
            "finality": self.finality.value,
        }

    def signing_digest(self) -> str:
        return canonical_hash(self.to_dict())
