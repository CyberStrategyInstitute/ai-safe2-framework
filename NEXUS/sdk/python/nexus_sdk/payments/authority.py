"""
nexus_sdk/payments/authority.py
Authority graph, aggregate economic containment, and the revocation plane.

Implements APAY-08 (monotonic delegation), APAY-09 (aggregate ceiling),
APAY-10 (velocity / micro-drain defense) and APAY-13 (revocation effectiveness).

WHY A GRAPH AND NOT A LIST
    Per-transaction limits are the control most agentic payment stacks ship
    with, and they are the one an attacker never has to break. Spend is
    distributed across children, merchants, rails and time until every
    individual check passes. Containment therefore has to be a property of the
    authority *tree*, evaluated at every node, not a property of a transaction.

REVOCATION IS AN EPOCH, NOT A DELETE
    A revocation implemented as "remove the row" races every cache, facilitator
    and child agent in the system. An epoch is a monotonic counter carried in
    every grant and every signed transaction: bumping it invalidates all
    descendants and all cached decisions simultaneously, and a component that
    cannot reach the epoch authority fails closed instead of assuming validity.
"""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from nexus_sdk.payments.objects import (
    AuthorityConstraints,
    AuthorityGrant,
    Money,
    PaymentReasonCode,
    utcnow,
)

__all__ = [
    "SpendRecord",
    "ExposureReservation",
    "AttenuationError",
    "RevocationPlane",
    "AuthorityGraph",
    "VelocityProfile",
]


@dataclass(frozen=True)
class SpendRecord:
    """One committed exposure event against a grant."""
    authority_grant_id: str
    delegation_chain_id: str
    amount: Money
    merchant_id: str
    occurred_at: datetime
    transaction_intent_id: str
    settled: bool = True


@dataclass(frozen=True)
class ExposureReservation:
    """Spend Hold: value authorized but not yet conclusively settled."""
    reservation_id: str
    authority_grant_id: str
    delegation_chain_id: str
    amount: Money
    transaction_intent_id: str
    created_at: datetime


class AttenuationError(ValueError):
    """Raised when a proposed child grant would widen its parent's authority."""

    def __init__(self, axes: list[str]):
        self.axes = axes
        super().__init__(
            "delegation would widen parent authority on: " + ", ".join(axes)
        )


# ── Revocation plane ──────────────────────────────────────────────────────────

class RevocationPlane:
    """APAY-13. One control point that severs an entire authority subtree.

    `current_epoch` is global to a principal. Any grant, cached decision or
    in-flight signed transaction carrying an older epoch is invalid on
    presentation, so revocation does not have to find and delete anything: it
    only has to increment, and everything derived from the old epoch stops
    being authority.

    `available` models the failure mode that matters. When the epoch authority
    cannot be reached, callers must treat status as unknown and fail closed
    (APAY-18). A revocation plane that returns "probably fine" when it is down
    is worse than none, because it manufactures confidence.
    """

    def __init__(self) -> None:
        self._epochs: dict[str, int] = defaultdict(int)
        self._revoked_grants: set[str] = set()
        self._revoked_chains: set[str] = set()
        self._revoked_at: dict[str, datetime] = {}
        self._lock = threading.RLock()
        self.available = True

    def current_epoch(self, principal_id: str) -> int:
        if not self.available:
            raise RuntimeError(PaymentReasonCode.REVOCATION_STATUS_UNAVAILABLE.value)
        with self._lock:
            return self._epochs[principal_id]

    def revoke_principal(self, principal_id: str, *, at: Optional[datetime] = None) -> int:
        """Kill everything under a principal. Returns the new epoch."""
        with self._lock:
            self._epochs[principal_id] += 1
            self._revoked_at[f"principal:{principal_id}"] = at or utcnow()
            return self._epochs[principal_id]

    def revoke_chain(self, delegation_chain_id: str, *, at: Optional[datetime] = None) -> None:
        with self._lock:
            self._revoked_chains.add(delegation_chain_id)
            self._revoked_at[f"chain:{delegation_chain_id}"] = at or utcnow()

    def revoke_grant(self, authority_grant_id: str, *, at: Optional[datetime] = None) -> None:
        with self._lock:
            self._revoked_grants.add(authority_grant_id)
            self._revoked_at[f"grant:{authority_grant_id}"] = at or utcnow()

    def revoked_at(self, key: str) -> Optional[datetime]:
        return self._revoked_at.get(key)

    def status(self, grant: AuthorityGrant) -> Optional[PaymentReasonCode]:
        """None means the grant is live. Any other value is a hard deny."""
        if not self.available:
            return PaymentReasonCode.REVOCATION_STATUS_UNAVAILABLE
        with self._lock:
            if grant.revoked or grant.authority_grant_id in self._revoked_grants:
                return PaymentReasonCode.GRANT_REVOKED
            if grant.delegation_chain_id in self._revoked_chains:
                return PaymentReasonCode.GRANT_REVOKED
            if grant.revocation_epoch < self._epochs[grant.principal_id]:
                return PaymentReasonCode.STALE_REVOCATION_EPOCH
        return None


# ── Velocity ──────────────────────────────────────────────────────────────────

@dataclass
class VelocityProfile:
    """APAY-10 tuning. Defaults are deliberately conservative for ACT-3+ spend.

    These thresholds are policy, not truth. They are exposed so a deployment can
    measure its own false-block cost rather than inheriting numbers from a
    vendor who never saw its traffic.
    """
    window_seconds: int = 3600
    max_transactions_per_window: int = 20
    max_distinct_merchants_per_window: int = 8
    micro_drain_count: int = 10          # N transactions...
    micro_drain_fraction: float = 0.10   # ...each under this fraction of max_transaction
    split_window_seconds: int = 300      # repeated near-limit spend to one merchant
    split_count: int = 3
    split_fraction: float = 0.80


# ── Authority graph ───────────────────────────────────────────────────────────

class AuthorityGraph:
    """The authority tree plus its committed exposure.

    Thread-safe because a payment gateway is concurrent by nature, and a
    check-then-commit race on a spend ceiling is a drain, not a rounding error.
    """

    def __init__(self, revocation: Optional[RevocationPlane] = None,
                 velocity: Optional[VelocityProfile] = None) -> None:
        self.revocation = revocation or RevocationPlane()
        self.velocity = velocity or VelocityProfile()
        self._grants: dict[str, AuthorityGrant] = {}
        self._children: dict[str, list[str]] = defaultdict(list)
        self._spend: dict[str, list[SpendRecord]] = defaultdict(list)
        self._reservations: dict[str, ExposureReservation] = {}
        self._lock = threading.RLock()

    # ── Registration ─────────────────────────────────────────────────────────

    def register_root(self, grant: AuthorityGrant) -> AuthorityGrant:
        with self._lock:
            if grant.parent_grant_id is not None:
                raise ValueError("register_root called with a child grant; use delegate()")
            grant.revocation_epoch = self.revocation.current_epoch(grant.principal_id)
            self._grants[grant.authority_grant_id] = grant
            return grant

    def delegate(self, parent_id: str, *, agent_did: Optional[str] = None,
                 capabilities: Optional[set[str]] = None,
                 **overrides) -> AuthorityGrant:
        """Mint a child grant. Raises AttenuationError rather than clamping silently.

        `attenuate()` clamps, which is the safe behavior for a caller that wants
        a narrower grant. This method additionally *reports* when the caller
        asked for something wider, because silently narrowing a request hides
        an escalation attempt that operators need to see.
        """
        with self._lock:
            parent = self._grants.get(parent_id)
            if parent is None:
                raise KeyError(PaymentReasonCode.GRANT_NOT_FOUND.value)
            # max_delegation_depth is REMAINING sub-delegation budget, not an
            # absolute tree depth. It decrements at every hop, so a grant
            # holding zero cannot mint children regardless of where it sits.
            if parent.constraints.max_delegation_depth < 1:
                raise AttenuationError(["max_delegation_depth"])

            requested = AuthorityConstraints(
                max_transaction=parent.constraints.max_transaction,
                max_aggregate=parent.constraints.max_aggregate,
                currencies=set(parent.constraints.currencies) if parent.constraints.currencies is not None else None,
                allowed_merchants=set(parent.constraints.allowed_merchants) if parent.constraints.allowed_merchants is not None else None,
                denied_merchants=set(parent.constraints.denied_merchants),
                allowed_categories=set(parent.constraints.allowed_categories) if parent.constraints.allowed_categories is not None else None,
                allowed_geographies=set(parent.constraints.allowed_geographies) if parent.constraints.allowed_geographies is not None else None,
                allowed_rails=set(parent.constraints.allowed_rails) if parent.constraints.allowed_rails is not None else None,
                allowed_facilitators=set(parent.constraints.allowed_facilitators) if parent.constraints.allowed_facilitators is not None else None,
                allowed_destinations=set(parent.constraints.allowed_destinations) if parent.constraints.allowed_destinations is not None else None,
                min_assurance=parent.constraints.min_assurance,
                max_finality=parent.constraints.max_finality,
                recurrence_allowed=parent.constraints.recurrence_allowed,
                max_transactions=parent.constraints.max_transactions,
                max_delegation_depth=max(parent.constraints.max_delegation_depth - 1, 0),
                window_seconds=parent.constraints.window_seconds,
                window_max=parent.constraints.window_max,
                not_after=parent.constraints.not_after,
                hear_above=parent.constraints.hear_above,
            )
            for key, value in overrides.items():
                if not hasattr(requested, key):
                    raise AttributeError(f"unknown constraint axis: {key}")
                setattr(requested, key, value)

            violations = requested.attenuation_violations(parent.constraints)
            if violations:
                raise AttenuationError(violations)

            # Capabilities are themselves attenuated (APAY-07).
            child_caps = set(capabilities) if capabilities is not None else set(parent.capabilities)
            if parent.capabilities and not child_caps.issubset(parent.capabilities):
                raise AttenuationError(["capabilities"])

            child = AuthorityGrant(
                principal_id=parent.principal_id,
                constraints=requested,
                delegation_chain_id=parent.delegation_chain_id,
                parent_grant_id=parent.authority_grant_id,
                depth=parent.depth + 1,
                agent_did=agent_did,
                revocation_epoch=parent.revocation_epoch,
                instruction_ref=parent.instruction_ref,
                instruction_digest=parent.instruction_digest,
                approved_by=parent.approved_by,
                approval_surface=parent.approval_surface,
                capabilities=child_caps,
            )
            self._grants[child.authority_grant_id] = child
            self._children[parent.authority_grant_id].append(child.authority_grant_id)
            return child

    # ── Lookup ───────────────────────────────────────────────────────────────

    def get(self, authority_grant_id: str) -> Optional[AuthorityGrant]:
        with self._lock:
            return self._grants.get(authority_grant_id)

    def ancestors(self, authority_grant_id: str) -> list[AuthorityGrant]:
        """Root-first lineage, excluding the grant itself."""
        with self._lock:
            chain: list[AuthorityGrant] = []
            node = self._grants.get(authority_grant_id)
            seen: set[str] = set()
            while node is not None and node.parent_grant_id is not None:
                if node.parent_grant_id in seen:
                    break  # defensive: a cycle is a bug, not an authority path
                seen.add(node.parent_grant_id)
                node = self._grants.get(node.parent_grant_id)
                if node is not None:
                    chain.append(node)
            return list(reversed(chain))

    def descendants(self, authority_grant_id: str) -> list[AuthorityGrant]:
        with self._lock:
            out: list[AuthorityGrant] = []
            stack = list(self._children.get(authority_grant_id, []))
            while stack:
                gid = stack.pop()
                grant = self._grants.get(gid)
                if grant is None:
                    continue
                out.append(grant)
                stack.extend(self._children.get(gid, []))
            return out

    def lineage_violations(self, authority_grant_id: str) -> list[str]:
        """Re-verify attenuation across the whole lineage at execution time.

        Checking attenuation only at mint time trusts that nothing mutated a
        grant afterwards. Re-deriving it per transaction is cheap and closes
        the window where an edited parent silently widens its children.
        """
        with self._lock:
            grant = self._grants.get(authority_grant_id)
            if grant is None:
                return [PaymentReasonCode.GRANT_NOT_FOUND.value]
            if grant.parent_grant_id is not None and grant.parent_grant_id not in self._grants:
                return [PaymentReasonCode.ORPHANED_GRANT.value]
            violations: list[str] = []
            node = grant
            while node.parent_grant_id is not None:
                parent = self._grants[node.parent_grant_id]
                violations.extend(
                    f"{node.authority_grant_id}:{axis}"
                    for axis in node.constraints.attenuation_violations(parent.constraints)
                )
                node = parent
            return violations

    # ── Exposure ─────────────────────────────────────────────────────────────

    def subtree_spend(self, authority_grant_id: str, *,
                      since: Optional[datetime] = None,
                      currency: str = "USD") -> Money:
        """Committed exposure for a grant and every descendant.

        This is what makes per-transaction limits meaningful. A parent's
        aggregate ceiling counts what its children spent, so distributing spend
        across a subtree no longer evades it.
        """
        with self._lock:
            ids = [authority_grant_id] + [g.authority_grant_id
                                          for g in self.descendants(authority_grant_id)]
            total = 0
            for gid in ids:
                for rec in self._spend[gid]:
                    if since is not None and rec.occurred_at < since:
                        continue
                    if rec.amount.currency != currency:
                        continue
                    total += rec.amount.minor_units
            return Money(total, currency)

    def chain_spend(self, delegation_chain_id: str, *,
                    since: Optional[datetime] = None,
                    currency: str = "USD") -> Money:
        with self._lock:
            total = 0
            for records in self._spend.values():
                for rec in records:
                    if rec.delegation_chain_id != delegation_chain_id:
                        continue
                    if since is not None and rec.occurred_at < since:
                        continue
                    if rec.amount.currency != currency:
                        continue
                    total += rec.amount.minor_units
            return Money(total, currency)

    def record_spend(self, record: SpendRecord) -> None:
        with self._lock:
            self._spend[record.authority_grant_id].append(record)

    def reserve_exposure(self, grant: AuthorityGrant, amount: Money,
                         transaction_intent_id: str, *, now: Optional[datetime] = None) -> ExposureReservation:
        """Atomically check every ancestor ceiling and place a Spend Hold."""
        with self._lock:
            violations = self.ceiling_violations(grant, amount, now=now, include_reserved=True)
            if violations:
                raise ValueError(violations[0].value)
            existing = next((r for r in self._reservations.values()
                             if r.transaction_intent_id == transaction_intent_id), None)
            if existing:
                if existing.amount != amount or existing.authority_grant_id != grant.authority_grant_id:
                    raise ValueError(PaymentReasonCode.REPLAY_DETECTED.value)
                return existing
            record = ExposureReservation(
                reservation_id=f"res_{uuid.uuid4().hex[:24]}",
                authority_grant_id=grant.authority_grant_id,
                delegation_chain_id=grant.delegation_chain_id or "",
                amount=amount,
                transaction_intent_id=transaction_intent_id,
                created_at=now or utcnow(),
            )
            self._reservations[record.reservation_id] = record
            return record

    def reservation_for_intent(self, transaction_intent_id: str) -> Optional[ExposureReservation]:
        with self._lock:
            return next((r for r in self._reservations.values()
                         if r.transaction_intent_id == transaction_intent_id), None)

    def release_reservation(self, transaction_intent_id: str) -> None:
        with self._lock:
            doomed = [key for key, value in self._reservations.items()
                      if value.transaction_intent_id == transaction_intent_id]
            for key in doomed:
                del self._reservations[key]

    def reserved_subtree(self, authority_grant_id: str, *, currency: str) -> Money:
        with self._lock:
            ids = {authority_grant_id, *(g.authority_grant_id
                                         for g in self.descendants(authority_grant_id))}
            total = sum(r.amount.minor_units for r in self._reservations.values()
                        if r.authority_grant_id in ids and r.amount.currency == currency)
            return Money(total, currency)

    def subtree_exposure(self, authority_grant_id: str, *, currency: str = "USD") -> Money:
        """Settled spend plus every unresolved Spend Hold in the subtree."""
        spent = self.subtree_spend(authority_grant_id, currency=currency)
        reserved = self.reserved_subtree(authority_grant_id, currency=currency)
        return spent + reserved

    def recent(self, authority_grant_id: str, seconds: int,
               *, now: Optional[datetime] = None,
               include_descendants: bool = True) -> list[SpendRecord]:
        now = now or utcnow()
        cutoff = now - timedelta(seconds=seconds)
        with self._lock:
            ids = [authority_grant_id]
            if include_descendants:
                ids += [g.authority_grant_id for g in self.descendants(authority_grant_id)]
            return [r for gid in ids for r in self._spend[gid] if r.occurred_at >= cutoff]

    # ── Ceiling and velocity evaluation ──────────────────────────────────────

    def ceiling_violations(self, grant: AuthorityGrant, amount: Money,
                           *, now: Optional[datetime] = None,
                           include_reserved: bool = True) -> list[PaymentReasonCode]:
        """APAY-09. Evaluate the proposed amount against every ancestor's ceiling.

        The transaction must fit under the aggregate ceiling of the grant that
        authorizes it *and* every grant above it. A child cannot spend a parent
        past its own limit just because the child's own limit has room.
        """
        now = now or utcnow()
        reasons: list[PaymentReasonCode] = []
        nodes = self.ancestors(grant.authority_grant_id) + [grant]
        for node in nodes:
            c = node.constraints
            if c.max_aggregate is not None and c.max_aggregate.currency == amount.currency:
                committed = self.subtree_spend(node.authority_grant_id,
                                               currency=amount.currency)
                reserved = self.reserved_subtree(node.authority_grant_id, currency=amount.currency)
                held = reserved.minor_units if include_reserved else 0
                if committed.minor_units + held + amount.minor_units > c.max_aggregate.minor_units:
                    reasons.append(PaymentReasonCode.AGGREGATE_CEILING_EXCEEDED)
                    break
        for node in nodes:
            c = node.constraints
            if c.window_max is not None and c.window_seconds:
                if c.window_max.currency != amount.currency:
                    continue
                since = now - timedelta(seconds=c.window_seconds)
                windowed = self.subtree_spend(node.authority_grant_id, since=since,
                                              currency=amount.currency)
                reserved = self.reserved_subtree(node.authority_grant_id, currency=amount.currency)
                held = reserved.minor_units if include_reserved else 0
                if windowed.minor_units + held + amount.minor_units > c.window_max.minor_units:
                    reasons.append(PaymentReasonCode.WINDOW_CEILING_EXCEEDED)
                    break
        for node in nodes:
            if node.constraints.max_transactions is not None:
                count = len(self._spend[node.authority_grant_id]) + sum(
                    len(self._spend[g.authority_grant_id])
                    for g in self.descendants(node.authority_grant_id)
                )
                if include_reserved:
                    ids = {node.authority_grant_id, *(g.authority_grant_id
                                                      for g in self.descendants(node.authority_grant_id))}
                    count += sum(1 for reservation in self._reservations.values()
                                 if reservation.authority_grant_id in ids)
                if count + 1 > node.constraints.max_transactions:
                    reasons.append(PaymentReasonCode.TRANSACTION_COUNT_EXCEEDED)
                    break
        return reasons

    def velocity_violations(self, grant: AuthorityGrant, amount: Money,
                            merchant_id: str,
                            *, now: Optional[datetime] = None) -> list[PaymentReasonCode]:
        """APAY-10. Shape-based detection for spend that each check would pass.

        None of these are fraud on their own. They are the shapes a drain takes
        when every individual transaction is inside policy, which is precisely
        the case per-transaction limits cannot see.
        """
        now = now or utcnow()
        vp = self.velocity
        reasons: list[PaymentReasonCode] = []
        window = self.recent(grant.authority_grant_id, vp.window_seconds, now=now)

        if len(window) + 1 > vp.max_transactions_per_window:
            reasons.append(PaymentReasonCode.VELOCITY_ANOMALY)

        merchants = {r.merchant_id for r in window} | {merchant_id}
        if len(merchants) > vp.max_distinct_merchants_per_window:
            reasons.append(PaymentReasonCode.MERCHANT_DISPERSION_ANOMALY)

        max_tx = grant.constraints.max_transaction
        if max_tx is not None and max_tx.currency == amount.currency and max_tx.minor_units > 0:
            threshold = int(max_tx.minor_units * vp.micro_drain_fraction)
            smalls = [r for r in window
                      if r.amount.currency == amount.currency
                      and r.amount.minor_units <= threshold]
            if amount.minor_units <= threshold and len(smalls) + 1 >= vp.micro_drain_count:
                reasons.append(PaymentReasonCode.MICRO_DRAIN_SUSPECTED)

            split_threshold = int(max_tx.minor_units * vp.split_fraction)
            split_window = self.recent(grant.authority_grant_id, vp.split_window_seconds, now=now)
            near_limit_same_merchant = [
                r for r in split_window
                if r.merchant_id == merchant_id
                and r.amount.currency == amount.currency
                and r.amount.minor_units >= split_threshold
            ]
            if (amount.minor_units >= split_threshold
                    and len(near_limit_same_merchant) + 1 >= vp.split_count):
                reasons.append(PaymentReasonCode.SPLIT_TRANSACTION_SUSPECTED)

        return reasons

    # ── Revocation effectiveness measurement ─────────────────────────────────

    def exposure_after(self, moment: datetime, *,
                       delegation_chain_id: Optional[str] = None,
                       currency: str = "USD") -> Money:
        """Total value that moved after a given instant.

        This is the numerator of the metric that matters: unauthorized exposure
        after revocation. API acknowledgement latency is not revocation; value
        that still moved is.
        """
        with self._lock:
            total = 0
            for records in self._spend.values():
                for rec in records:
                    if rec.occurred_at <= moment:
                        continue
                    if delegation_chain_id and rec.delegation_chain_id != delegation_chain_id:
                        continue
                    if rec.amount.currency != currency:
                        continue
                    total += rec.amount.minor_units
            return Money(total, currency)
