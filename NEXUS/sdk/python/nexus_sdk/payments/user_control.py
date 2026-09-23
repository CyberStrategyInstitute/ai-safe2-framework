"""Human Shield (`UserControlPolicy`): principal-owned payment guardrails."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from nexus_sdk.payments.objects import Money, TransactionIntent, utcnow


@dataclass(frozen=True)
class UserControlDecision:
    allow: bool
    require_confirmation: bool = False
    reasons: tuple[str, ...] = ()


@dataclass
class UserControlPolicy:
    """Human Shield (`UserControlPolicy`).

    These controls belong to the principal and remain independent of merchant,
    network, model, or facilitator policy.
    """
    paused: bool = False
    confirmation_above: Optional[Money] = None
    cooling_off_seconds: int = 0
    approved_payees: set[str] = field(default_factory=set)
    blocked_merchants: set[str] = field(default_factory=set)
    require_confirmation_for_new_payee: bool = True
    last_policy_change_at: datetime = field(default_factory=utcnow)

    def check(self, intent: TransactionIntent, *, confirmed_by: Optional[str] = None,
              now: Optional[datetime] = None) -> UserControlDecision:
        now = now or utcnow()
        reasons: list[str] = []
        if self.paused:
            reasons.append("principal pause is active")
        if intent.merchant_id in self.blocked_merchants:
            reasons.append("merchant blocked by principal")
        if self.cooling_off_seconds and now < self.last_policy_change_at + timedelta(seconds=self.cooling_off_seconds):
            reasons.append("principal policy cooling-off period active")
        confirmation = False
        if self.confirmation_above and self.confirmation_above.currency == intent.amount.currency:
            confirmation = intent.amount.minor_units >= self.confirmation_above.minor_units
        if self.require_confirmation_for_new_payee and intent.destination not in self.approved_payees:
            confirmation = True
        if confirmation and not confirmed_by:
            reasons.append("fresh principal confirmation required")
        hard_deny = self.paused or intent.merchant_id in self.blocked_merchants
        return UserControlDecision(not hard_deny and not reasons, confirmation, tuple(reasons))
