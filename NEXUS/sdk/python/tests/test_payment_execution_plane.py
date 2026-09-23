"""Security contract tests for the Sovereign Payment Gateway execution plane."""

import pytest
from nexus_sdk.payments.execution_plane import (
    ComponentAssurance,
    ExecutionRecord,
    ExecutionState,
    ExecutionTransitionError,
    NEXUSPaymentExecutionPlane,
)


def record() -> ExecutionRecord:
    return ExecutionRecord(
        execution_id="exec-1",
        transaction_intent_id="intent-1",
        canonical_digest="sha256:canonical",
        idempotency_key="idem-1",
        authority_grant_id="grant-1",
        revocation_epoch=7,
    )


class Component:
    def __init__(self, assurance: ComponentAssurance):
        self.assurance = assurance


def test_execution_follows_monotonic_happy_path():
    current = record()
    for state in (
        ExecutionState.POLICY_ACCEPTED,
        ExecutionState.RESERVED,
        ExecutionState.CREDENTIAL_RELEASED,
        ExecutionState.SUBMITTED,
        ExecutionState.SETTLED,
    ):
        current = current.transition(state)
    assert current.state is ExecutionState.SETTLED
    assert current.version == 5


def test_ambiguous_payment_must_enter_reconciliation():
    current = record().transition(ExecutionState.POLICY_ACCEPTED)
    current = current.transition(ExecutionState.RESERVED)
    current = current.transition(ExecutionState.CREDENTIAL_RELEASED)
    current = current.transition(ExecutionState.AMBIGUOUS)
    with pytest.raises(ExecutionTransitionError):
        current.transition(ExecutionState.RELEASED)
    assert current.transition(ExecutionState.RECONCILING).state is ExecutionState.RECONCILING


def test_terminal_state_cannot_be_reopened():
    failed = record().transition(ExecutionState.FAILED)
    with pytest.raises(ExecutionTransitionError):
        failed.transition(ExecutionState.POLICY_ACCEPTED)


def test_canonical_identity_and_revocation_epoch_are_immutable():
    with pytest.raises(ExecutionTransitionError, match="immutable execution fields"):
        record().transition(ExecutionState.POLICY_ACCEPTED, canonical_digest="sha256:changed")


def test_execution_plane_reports_every_unbound_boundary():
    readiness = NEXUSPaymentExecutionPlane().readiness()
    assert readiness.ready is False
    assert readiness.missing == NEXUSPaymentExecutionPlane.required_components
    assert readiness.reference_only == ()


def test_reference_components_cannot_claim_deployment_readiness():
    components = {
        name: Component(ComponentAssurance.REFERENCE)
        for name in NEXUSPaymentExecutionPlane.required_components
    }
    readiness = NEXUSPaymentExecutionPlane(**components).readiness()
    assert readiness.ready is False
    assert readiness.missing == ()
    assert readiness.reference_only == NEXUSPaymentExecutionPlane.required_components


def test_only_deployment_boundaries_are_ready():
    components = {
        name: Component(ComponentAssurance.DEPLOYMENT)
        for name in NEXUSPaymentExecutionPlane.required_components
    }
    readiness = NEXUSPaymentExecutionPlane(**components).readiness()
    assert readiness.ready is True
    assert readiness.reason == "all required execution boundaries provide deployment assurance"


def test_unknown_component_is_rejected():
    with pytest.raises(TypeError, match="unknown execution components"):
        NEXUSPaymentExecutionPlane(shortcut=Component(ComponentAssurance.DEPLOYMENT))
