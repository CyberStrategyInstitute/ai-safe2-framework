"""
nexus_sdk/payments/mandate.py
Mandate compiler and trusted rendering surface.

Implements APAY-02 (trusted mandate rendering), APAY-03 (intent translation
evidence) and the semantic-integrity half of APAY-04.

THE PROBLEM THIS SOLVES
    A signature proves a principal approved the object that was placed in front
    of them. It does not prove that object faithfully represented what they
    originally asked for. Between the principal's natural-language objective
    and the signed mandate sits a nondeterministic model that an attacker can
    influence through any untrusted content it read along the way - product
    descriptions, reviews, another agent's replies.

    So the compiler does two things a model must not be trusted to do:
      1. It preserves the original instruction and the constraints derived from
         it as separate, separately hashed artifacts, so a later adjudicator can
         see the translation rather than the model's account of it.
      2. It refuses to silently resolve ambiguity. An instruction that does not
         determine a constraint produces a recorded ambiguity, and a grant
         carrying unresolved ambiguities cannot authorize spend without a human.

    What the compiler deliberately does NOT claim: it cannot verify that the
    principal *meant* what they typed. That problem is not solvable by
    cryptography, and pretending otherwise is how these systems fail. What it
    can do is make the translation inspectable and make unresolved gaps stop
    the transaction instead of being filled in by a model.

TRUSTED SURFACE
    RenderedMandate is what a human actually sees. It is generated from the
    compiled constraints, not from agent-supplied prose, and its digest is
    bound into the grant. If the agent later presents different terms, the
    digest will not match what was approved.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from nexus_sdk.payments.objects import (
    AuthorityConstraints,
    AuthorityGrant,
    ConsequenceClass,
    Money,
    PaymentRail,
    SettlementFinality,
    canonical_hash,
    utcnow,
)

__all__ = [
    "Ambiguity",
    "CompiledMandate",
    "RenderedMandate",
    "MandateCompiler",
    "classify_consequence",
]


@dataclass(frozen=True)
class Ambiguity:
    """A term the instruction did not determine.

    `axis` is the constraint that could not be derived. `resolution` records how
    it was closed, and stays None until a human closes it.
    """
    axis: str
    detail: str
    resolution: Optional[str] = None

    def to_dict(self) -> dict:
        return {"axis": self.axis, "detail": self.detail, "resolution": self.resolution}


@dataclass
class CompiledMandate:
    """The output of translating an instruction into deterministic constraints."""
    instruction: str
    constraints: AuthorityConstraints
    instruction_ref: str = field(default_factory=lambda: f"instr_{uuid.uuid4().hex[:20]}")
    ambiguities: list[Ambiguity] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    compiled_at: str = field(default_factory=lambda: utcnow().isoformat())
    compiler_version: str = "apay-mandate-compiler/0.4"

    @property
    def instruction_digest(self) -> str:
        return canonical_hash({"instruction": self.instruction})

    @property
    def constraints_digest(self) -> str:
        return canonical_hash(self.constraints.to_dict())

    @property
    def unresolved(self) -> list[Ambiguity]:
        return [a for a in self.ambiguities if a.resolution is None]

    def resolve(self, axis: str, resolution: str) -> "CompiledMandate":
        """Close an ambiguity with an explicit human answer."""
        self.ambiguities = [
            Ambiguity(a.axis, a.detail, resolution) if a.axis == axis and a.resolution is None else a
            for a in self.ambiguities
        ]
        return self

    def to_dict(self) -> dict:
        return {
            "instruction_ref": self.instruction_ref,
            "instruction_digest": self.instruction_digest,
            "constraints_digest": self.constraints_digest,
            "constraints": self.constraints.to_dict(),
            "ambiguities": [a.to_dict() for a in self.ambiguities],
            "assumptions": list(self.assumptions),
            "compiled_at": self.compiled_at,
            "compiler_version": self.compiler_version,
        }


@dataclass
class RenderedMandate:
    """APAY-02. What the trusted surface displays, and its binding digest.

    Generated from compiled constraints only. The agent contributes no prose
    here, so a compromised agent cannot shape what the human reads at the moment
    of approval.
    """
    lines: list[str]
    constraints_digest: str
    cart_digest: Optional[str] = None
    surface_id: str = "nexus.trusted-surface.v0.4"
    rendered_at: str = field(default_factory=lambda: utcnow().isoformat())

    @property
    def rendering_digest(self) -> str:
        return canonical_hash({
            "lines": self.lines,
            "constraints_digest": self.constraints_digest,
            "cart_digest": self.cart_digest,
            "surface_id": self.surface_id,
        })

    def to_dict(self) -> dict:
        return {
            "lines": list(self.lines),
            "constraints_digest": self.constraints_digest,
            "cart_digest": self.cart_digest,
            "surface_id": self.surface_id,
            "rendered_at": self.rendered_at,
            "rendering_digest": self.rendering_digest,
        }


def classify_consequence(amount: Money, finality: SettlementFinality,
                         *, novel_destination: bool = False,
                         critical_threshold: Optional[Money] = None) -> ConsequenceClass:
    """Derive the consequence class of a value movement.

    Finality dominates amount. A small irreversible payment to a destination the
    principal has never used is a worse outcome than a larger reversible one,
    because there is no path to undo it.
    """
    if critical_threshold is not None and critical_threshold.currency == amount.currency:
        if amount.minor_units >= critical_threshold.minor_units:
            return ConsequenceClass.CRITICAL
    if finality is SettlementFinality.IRREVERSIBLE:
        return (ConsequenceClass.CRITICAL if novel_destination
                else ConsequenceClass.CONSEQUENTIAL)
    if finality is SettlementFinality.MEDIATED:
        return ConsequenceClass.MATERIAL
    return ConsequenceClass.MATERIAL if novel_destination else ConsequenceClass.ROUTINE


# ── Compiler ──────────────────────────────────────────────────────────────────

_AMOUNT_RE = re.compile(
    r"(?:(?P<sym>[$€£])\s*(?P<v1>[\d,]+(?:\.\d{1,2})?))"
    r"|(?:(?P<v2>[\d,]+(?:\.\d{1,2})?)\s*(?P<code>USD|EUR|GBP|USDC|USDT)\b)",
    re.IGNORECASE,
)
_SYMBOL_CURRENCY = {"$": "USD", "€": "EUR", "£": "GBP"}
_RECURRING_RE = re.compile(
    r"\b(monthly|weekly|daily|recurring|subscription|every\s+(?:month|week|day))\b", re.I)
_UNBOUNDED_RE = re.compile(
    r"\b(whatever|anything|as\s+needed|best\s+price|if\s+necessary|up\s+to\s+you|"
    r"handle\s+it|any\s+amount|as\s+much\s+as)\b", re.I)


class MandateCompiler:
    """Deterministic instruction-to-constraint translation.

    This is intentionally a conservative rule engine, not a model. A model
    compiling its own spending limits is the vulnerability, not the feature: the
    same prompt injection that steers a purchase steers the constraint that was
    supposed to bound it. Anything the rules cannot determine becomes a recorded
    ambiguity that a human must close.

    Deployments will extend the rule set. The invariant to preserve is that the
    compiler is deterministic and its output is reproducible from the instruction
    plus the compiler version, so the evidence bundle can be re-derived by a
    third party.
    """

    def __init__(self, *, default_constraints: Optional[AuthorityConstraints] = None,
                 default_currency: str = "USD") -> None:
        self.default_constraints = default_constraints
        self.default_currency = default_currency

    def compile(self, instruction: str, *,
                explicit: Optional[dict[str, Any]] = None) -> CompiledMandate:
        """Translate an instruction plus explicit operator-supplied bounds.

        `explicit` always wins over anything parsed from prose. Operator-set
        bounds are authority; text extracted from an instruction is a hint.
        """
        explicit = explicit or {}
        ambiguities: list[Ambiguity] = []
        assumptions: list[str] = []

        base = self.default_constraints
        constraints = AuthorityConstraints(
            max_transaction=base.max_transaction if base else None,
            max_aggregate=base.max_aggregate if base else None,
            currencies=set(base.currencies) if base and base.currencies else None,
            allowed_merchants=set(base.allowed_merchants) if base and base.allowed_merchants else None,
            denied_merchants=set(base.denied_merchants) if base else set(),
            allowed_categories=set(base.allowed_categories) if base and base.allowed_categories else None,
            allowed_geographies=set(base.allowed_geographies) if base and base.allowed_geographies else None,
            allowed_rails=set(base.allowed_rails) if base and base.allowed_rails else None,
            allowed_facilitators=set(base.allowed_facilitators) if base and base.allowed_facilitators else None,
            allowed_destinations=set(base.allowed_destinations) if base and base.allowed_destinations else None,
            min_assurance=base.min_assurance if base else AuthorityConstraints().min_assurance,
            max_finality=base.max_finality if base else SettlementFinality.IRREVERSIBLE,
            recurrence_allowed=base.recurrence_allowed if base else False,
            max_transactions=base.max_transactions if base else None,
            max_delegation_depth=base.max_delegation_depth if base else 2,
            window_seconds=base.window_seconds if base else None,
            window_max=base.window_max if base else None,
            not_after=base.not_after if base else None,
            hear_above=base.hear_above if base else None,
        )

        # 1. Amount ceiling.
        parsed_amount = self._parse_amount(instruction)
        if "max_transaction" in explicit:
            constraints.max_transaction = explicit["max_transaction"]
        elif parsed_amount is not None:
            constraints.max_transaction = parsed_amount
            assumptions.append(
                f"interpreted '{parsed_amount}' in the instruction as the per-transaction ceiling"
            )
        elif constraints.max_transaction is None:
            ambiguities.append(Ambiguity(
                "max_transaction",
                "instruction states no spending limit and no default ceiling is configured",
            ))

        # 2. Unbounded language is never resolved into a number.
        if _UNBOUNDED_RE.search(instruction) and "max_transaction" not in explicit:
            ambiguities.append(Ambiguity(
                "max_transaction",
                "instruction contains open-ended spend language; a ceiling must be set explicitly",
            ))

        # 3. Recurrence is opt-in and never inferred into permission.
        if "recurrence_allowed" in explicit:
            constraints.recurrence_allowed = bool(explicit["recurrence_allowed"])
        elif _RECURRING_RE.search(instruction):
            ambiguities.append(Ambiguity(
                "recurrence_allowed",
                "instruction implies a recurring commitment; recurring authority must be granted explicitly",
            ))

        # 4. Everything the operator set explicitly.
        for axis in ("max_aggregate", "currencies", "allowed_merchants", "denied_merchants",
                     "allowed_categories", "allowed_geographies", "allowed_rails",
                     "allowed_facilitators", "allowed_destinations", "min_assurance",
                     "max_finality", "max_transactions", "max_delegation_depth",
                     "window_seconds", "window_max", "not_after", "hear_above"):
            if axis in explicit:
                setattr(constraints, axis, explicit[axis])

        # 5. Counterparty scope.
        if constraints.allowed_merchants is None and "allowed_merchants" not in explicit:
            ambiguities.append(Ambiguity(
                "allowed_merchants",
                "no merchant allow-list; the grant would permit payment to any counterparty",
            ))

        # 6. Currency.
        if constraints.currencies is None:
            constraints.currencies = {
                parsed_amount.currency if parsed_amount else self.default_currency
            }
            assumptions.append(f"defaulted currency scope to {sorted(constraints.currencies)}")

        # 7. Irreversible rails need a destination allow-list or they are unbounded.
        rails = constraints.allowed_rails or set()
        if PaymentRail.STABLECOIN in rails and constraints.allowed_destinations is None:
            ambiguities.append(Ambiguity(
                "allowed_destinations",
                "stablecoin rail permitted with no destination allow-list; "
                "settlement is irreversible and destination substitution would be unrecoverable",
            ))

        return CompiledMandate(
            instruction=instruction,
            constraints=constraints,
            ambiguities=ambiguities,
            assumptions=assumptions,
        )

    def _parse_amount(self, text: str) -> Optional[Money]:
        match = _AMOUNT_RE.search(text)
        if not match:
            return None
        if match.group("v1"):
            raw, currency = match.group("v1"), _SYMBOL_CURRENCY[match.group("sym")]
        else:
            raw, currency = match.group("v2"), match.group("code").upper()
        try:
            return Money.parse(raw.replace(",", ""), currency)
        except ValueError:
            return None

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, mandate: CompiledMandate, *,
               cart_digest: Optional[str] = None) -> RenderedMandate:
        """Produce the human-facing terms from constraints alone.

        Consequence first, then bounds, then what is unresolved. The ordering is
        a control: approval fatigue is a real failure mode, and burying the
        irreversible-rail warning under line items is how broad mandates get
        rubber-stamped.
        """
        c = mandate.constraints
        lines: list[str] = []

        if c.max_finality is SettlementFinality.IRREVERSIBLE:
            lines.append("IRREVERSIBLE SETTLEMENT PERMITTED: payments on this grant cannot be reversed.")
        elif c.max_finality is SettlementFinality.MEDIATED:
            lines.append("Mediated settlement: recourse depends on escrow or contractual remedy, not chargeback.")

        lines.append(f"Per transaction: {c.max_transaction or 'UNBOUNDED'}")
        lines.append(f"Total across this grant and everything it delegates: {c.max_aggregate or 'UNBOUNDED'}")
        if c.window_max and c.window_seconds:
            lines.append(f"Rolling limit: {c.window_max} per {c.window_seconds}s")
        lines.append(
            "Merchants: " + (", ".join(sorted(c.allowed_merchants)) if c.allowed_merchants else "ANY")
        )
        if c.allowed_destinations:
            lines.append("Destinations: " + ", ".join(sorted(c.allowed_destinations)))
        lines.append(
            "Rails: " + (", ".join(sorted(r.value for r in c.allowed_rails)) if c.allowed_rails else "ANY")
        )
        lines.append(f"Recurring charges: {'PERMITTED' if c.recurrence_allowed else 'not permitted'}")
        lines.append(f"Expires: {c.not_after or 'NO EXPIRY'}")
        lines.append(f"Sub-delegation depth: {c.max_delegation_depth}")
        if c.hear_above:
            lines.append(f"Requires named human approval above: {c.hear_above}")

        for amb in mandate.unresolved:
            lines.append(f"UNRESOLVED - {amb.axis}: {amb.detail}")

        return RenderedMandate(
            lines=lines,
            constraints_digest=mandate.constraints_digest,
            cart_digest=cart_digest,
        )

    def issue(self, mandate: CompiledMandate, *, principal_id: str,
              agent_did: Optional[str] = None,
              approved_by: Optional[str] = None,
              rendering: Optional[RenderedMandate] = None,
              capabilities: Optional[set[str]] = None,
              allow_unresolved: bool = False) -> AuthorityGrant:
        """Turn a compiled and approved mandate into an authority grant.

        Refuses to issue while ambiguities are open unless a caller explicitly
        opts out, which exists only so the Challenge Lab can construct the
        unsafe case on purpose.
        """
        if mandate.unresolved and not allow_unresolved:
            raise ValueError(
                "cannot issue a grant with unresolved ambiguities: "
                + ", ".join(a.axis for a in mandate.unresolved)
            )
        return AuthorityGrant(
            principal_id=principal_id,
            constraints=mandate.constraints,
            agent_did=agent_did,
            instruction_ref=mandate.instruction_ref,
            instruction_digest=mandate.instruction_digest,
            normalized_constraints_digest=mandate.constraints_digest,
            unresolved_ambiguities=[a.axis for a in mandate.unresolved],
            approved_by=approved_by,
            approval_surface=rendering.rendering_digest if rendering else None,
            capabilities=set(capabilities or {"payment.execute"}),
        )
