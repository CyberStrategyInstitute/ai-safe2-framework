"""
nexus_sdk/payments/opa_input.py
Builds the exact input document opa/nexus-apay.rego evaluates.

WHY THIS EXISTS
    NEXUS now has two enforcement points for the payment plane: the in-process
    TransactionFirewall and the out-of-process OPA policy. Two implementations
    of one rule set drift, and drift in a policy engine is silent - the two
    disagree only on the transactions that matter.

    So neither one owns the contract. Both are fed from this single builder,
    derived from the same objects, and the test suite asserts that every field
    the Rego references is present in what this emits. A field added to the
    policy without a corresponding field here fails the contract test rather
    than failing open in production.

USAGE
    POST the output of build_opa_input(...) to
    /v1/data/nexus/apay/decision, and the credential-release gate to
    /v1/data/nexus/apay/release_credential.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from nexus_sdk.payments.authority import AuthorityGraph
from nexus_sdk.payments.objects import (
    AuthorityGrant,
    PrincipalBinding,
    RuntimeMeasurement,
    TransactionIntent,
    utcnow,
)

__all__ = ["build_opa_input", "OPA_INPUT_FIELDS"]

#: Every top-level key the Rego policy may reference. The contract test in
#: tests/test_apay_opa_contract.py asserts this stays in sync with the policy.
OPA_INPUT_FIELDS: tuple[str, ...] = (
    "now",
    "policy_id",
    "principal",
    "grant",
    "transaction",
    "runtime",
    "expected_runtime_baseline",
    "revocation",
    "attenuation_violations",
    "exposure",
    "velocity",
    "seen_nonces",
    "idempotency_digest",
    "merchant_baseline",
    "known_destinations",
    "hear_satisfied_by",
)


def build_opa_input(
    *,
    graph: AuthorityGraph,
    grant: Optional[AuthorityGrant],
    intent: TransactionIntent,
    principal: Optional[PrincipalBinding] = None,
    runtime: Optional[RuntimeMeasurement] = None,
    expected_runtime_baseline: Optional[str] = None,
    merchant_baseline: Optional[str] = None,
    known_destinations: Optional[set[str]] = None,
    seen_nonces: Optional[set[str]] = None,
    idempotency_digest: Optional[str] = None,
    hear_satisfied_by: Optional[str] = None,
    policy_id: str = "nexus-apay-v0.4",
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Assemble the policy input. Missing inputs are emitted as null, never omitted.

    Omitting a key and emitting null are different to Rego in ways that matter:
    an omitted key makes a rule undefined, which skips it. Emitting null keeps
    the rule evaluable so it can deny. Fail-closed depends on this distinction.
    """
    now = now or utcnow()

    revocation_available = graph.revocation.available
    current_epoch = 0
    if revocation_available and grant is not None:
        try:
            current_epoch = graph.revocation.current_epoch(grant.principal_id)
        except RuntimeError:
            revocation_available = False

    exposure: dict[str, Any] = {
        "subtree_committed_minor_units": 0,
        "window_committed_minor_units": 0,
        "subtree_transaction_count": 0,
    }
    velocity: dict[str, Any] = {
        "window_transaction_count": 0,
        "distinct_merchants_in_window": 0,
        "sub_threshold_count": 0,
        "near_limit_same_merchant_count": 0,
        "max_transactions_per_window": graph.velocity.max_transactions_per_window,
        "max_distinct_merchants": graph.velocity.max_distinct_merchants_per_window,
        "micro_drain_count": graph.velocity.micro_drain_count,
        "split_count": graph.velocity.split_count,
    }
    attenuation: list[str] = []

    if grant is not None:
        currency = intent.amount.currency
        exposure["subtree_committed_minor_units"] = graph.subtree_spend(
            grant.authority_grant_id, currency=currency
        ).minor_units
        if grant.constraints.window_seconds:
            since = now - timedelta(seconds=grant.constraints.window_seconds)
            exposure["window_committed_minor_units"] = graph.subtree_spend(
                grant.authority_grant_id, since=since, currency=currency
            ).minor_units
        exposure["subtree_transaction_count"] = len(
            graph.recent(grant.authority_grant_id, 10 ** 9, now=now)
        )
        attenuation = graph.lineage_violations(grant.authority_grant_id)

        window = graph.recent(grant.authority_grant_id,
                              graph.velocity.window_seconds, now=now)
        velocity["window_transaction_count"] = len(window)
        velocity["distinct_merchants_in_window"] = len(
            {r.merchant_id for r in window} | {intent.merchant_id}
        )
        max_tx = grant.constraints.max_transaction
        if max_tx is not None and max_tx.currency == currency and max_tx.minor_units > 0:
            micro = int(max_tx.minor_units * graph.velocity.micro_drain_fraction)
            velocity["sub_threshold_count"] = sum(
                1 for r in window
                if r.amount.currency == currency and r.amount.minor_units <= micro
            ) + (1 if intent.amount.minor_units <= micro else 0)
            split = int(max_tx.minor_units * graph.velocity.split_fraction)
            split_window = graph.recent(grant.authority_grant_id,
                                        graph.velocity.split_window_seconds, now=now)
            velocity["near_limit_same_merchant_count"] = sum(
                1 for r in split_window
                if r.merchant_id == intent.merchant_id
                and r.amount.currency == currency
                and r.amount.minor_units >= split
            ) + (1 if intent.amount.minor_units >= split else 0)

    runtime_doc: Optional[dict[str, Any]] = None
    if runtime is not None:
        runtime_doc = runtime.to_dict()
        runtime_doc["age_seconds"] = runtime.age_seconds(now)

    return {
        "now": now.isoformat(),
        "policy_id": policy_id,
        "principal": principal.to_dict() if principal else None,
        "grant": grant.to_dict() if grant else None,
        "transaction": intent.to_dict(),
        "runtime": runtime_doc,
        "expected_runtime_baseline": expected_runtime_baseline,
        "revocation": {
            "available": revocation_available,
            "current_epoch": current_epoch,
        },
        "attenuation_violations": attenuation,
        "exposure": exposure,
        "velocity": velocity,
        "seen_nonces": sorted(seen_nonces or set()),
        "idempotency_digest": idempotency_digest,
        "merchant_baseline": merchant_baseline,
        "known_destinations": sorted(known_destinations or set()),
        "hear_satisfied_by": hear_satisfied_by,
    }
