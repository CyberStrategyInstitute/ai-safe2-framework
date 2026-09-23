"""Contracts for the NEXUS Sovereign Payment Gateway.

The execution plane is the production boundary around the existing payment
integrity gateway. This module deliberately defines contracts rather than a
permissive reference backend: process-local state and agent-readable signing
keys must never be mistaken for deployment assurance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "ComponentAssurance", "ExecutionRecord", "ExecutionState",
    "ExecutionTransitionError", "GatewayReadiness", "NEXUSPaymentExecutionPlane",
    "SettlementStateStore", "TransactionalAuthorityStore", "TransactionalReplayStore",
]


class ExecutionState(str, Enum):
    """Monotonic states for one canonical payment execution."""

    PROPOSED = "proposed"
    POLICY_ACCEPTED = "policy_accepted"
    RESERVED = "reserved"
    CREDENTIAL_RELEASED = "credential_released"
    SUBMITTED = "submitted"
    SETTLED = "settled"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"
    RECONCILING = "reconciling"
    RELEASED = "released"
    ESCALATED = "escalated"


_ALLOWED_TRANSITIONS: Mapping[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.PROPOSED: frozenset({ExecutionState.POLICY_ACCEPTED, ExecutionState.FAILED}),
    ExecutionState.POLICY_ACCEPTED: frozenset({ExecutionState.RESERVED, ExecutionState.FAILED}),
    ExecutionState.RESERVED: frozenset({
        ExecutionState.CREDENTIAL_RELEASED, ExecutionState.FAILED, ExecutionState.RELEASED,
    }),
    ExecutionState.CREDENTIAL_RELEASED: frozenset({
        ExecutionState.SUBMITTED, ExecutionState.AMBIGUOUS, ExecutionState.FAILED,
    }),
    ExecutionState.SUBMITTED: frozenset({
        ExecutionState.SETTLED, ExecutionState.AMBIGUOUS, ExecutionState.FAILED,
    }),
    ExecutionState.AMBIGUOUS: frozenset({ExecutionState.RECONCILING}),
    ExecutionState.RECONCILING: frozenset({
        ExecutionState.SETTLED, ExecutionState.RELEASED, ExecutionState.ESCALATED,
    }),
    ExecutionState.SETTLED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.RELEASED: frozenset(),
    ExecutionState.ESCALATED: frozenset(),
}


class ExecutionTransitionError(ValueError):
    """A requested transition would violate the payment state machine."""


@dataclass(frozen=True)
class ExecutionRecord:
    """Durable state shared by policy, signer, rail, and reconciliation workers."""

    execution_id: str
    transaction_intent_id: str
    canonical_digest: str
    idempotency_key: str
    authority_grant_id: str
    revocation_epoch: int
    state: ExecutionState = ExecutionState.PROPOSED
    version: int = 0
    reservation_id: str | None = None
    authorization_id: str | None = None
    settlement_id: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def transition(self, target: ExecutionState, **changes: Any) -> ExecutionRecord:
        """Return the next record or reject an unsafe/non-monotonic transition."""

        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ExecutionTransitionError(
                f"execution cannot transition from {self.state.value} to {target.value}"
            )
        protected = {
            "execution_id", "transaction_intent_id", "canonical_digest", "idempotency_key",
            "authority_grant_id", "revocation_epoch", "state", "version",
        }
        overwritten = protected.intersection(changes)
        if overwritten:
            raise ExecutionTransitionError(
                "immutable execution fields cannot change: " + ", ".join(sorted(overwritten))
            )
        values = dict(self.__dict__)
        values.update(changes)
        values["state"] = target
        values["version"] = self.version + 1
        return ExecutionRecord(**values)


class ComponentAssurance(str, Enum):
    """Evidence level for a component bound to the execution plane."""

    UNBOUND = "unbound"
    REFERENCE = "reference"
    DEPLOYMENT = "deployment"


@runtime_checkable
class TransactionalAuthorityStore(Protocol):
    """Durable authority, reservation, exposure, and revocation boundary."""

    assurance: ComponentAssurance

    def current_revocation_epoch(self, principal_id: str) -> int: ...
    def reserve(self, record: ExecutionRecord, *, amount_minor: int, currency: str) -> str: ...
    def commit(self, reservation_id: str, *, settlement_id: str) -> None: ...
    def release(self, reservation_id: str, *, reason: str) -> None: ...


@runtime_checkable
class TransactionalReplayStore(Protocol):
    """Atomic accept-once boundary for nonces and idempotency keys."""

    assurance: ComponentAssurance

    def consume(self, *, namespace: str, key: str, digest: str) -> bool: ...


@runtime_checkable
class SettlementStateStore(Protocol):
    """Compare-and-swap persistence for payment execution state."""

    assurance: ComponentAssurance

    def create(self, record: ExecutionRecord) -> None: ...
    def get(self, execution_id: str) -> ExecutionRecord | None: ...
    def compare_and_swap(self, *, expected: ExecutionRecord, updated: ExecutionRecord) -> bool: ...


@dataclass(frozen=True)
class GatewayReadiness:
    """Deterministic readiness decision with inspectable missing evidence."""

    ready: bool
    missing: tuple[str, ...]
    reference_only: tuple[str, ...]

    @property
    def reason(self) -> str:
        if self.ready:
            return "all required execution boundaries provide deployment assurance"
        parts = []
        if self.missing:
            parts.append("unbound: " + ", ".join(self.missing))
        if self.reference_only:
            parts.append("reference-only: " + ", ".join(self.reference_only))
        return "; ".join(parts)


class NEXUSPaymentExecutionPlane:
    """Readiness contract for the Sovereign Payment Gateway.

    Authorization orchestration is intentionally added only after durable
    implementations exist. Until every required boundary presents deployment
    assurance, this class reports not ready and must not release credentials.
    """

    human_name = "Sovereign Payment Gateway"
    technical_name = "NEXUSPaymentExecutionPlane"
    profile_version = "CP.5.APAY/0.5-draft"
    required_components = (
        "authority_store", "replay_store", "settlement_store", "policy_engine",
        "credential_broker", "evidence_ledger", "attestation_verifier",
    )

    def __init__(self, **components: object) -> None:
        unknown = set(components).difference(self.required_components)
        if unknown:
            raise TypeError("unknown execution components: " + ", ".join(sorted(unknown)))
        self._components = dict(components)

    def readiness(self) -> GatewayReadiness:
        missing: list[str] = []
        reference_only: list[str] = []
        for name in self.required_components:
            component = self._components.get(name)
            assurance = getattr(component, "assurance", None)
            if component is None or assurance is ComponentAssurance.UNBOUND:
                missing.append(name)
            elif assurance is not ComponentAssurance.DEPLOYMENT:
                reference_only.append(name)
        return GatewayReadiness(
            ready=not missing and not reference_only,
            missing=tuple(missing),
            reference_only=tuple(reference_only),
        )
