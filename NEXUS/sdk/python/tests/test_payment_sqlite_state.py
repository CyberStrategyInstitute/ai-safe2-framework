"""Concurrency and restart tests for the Gateway State Vault."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from nexus_sdk.payments.execution_plane import ExecutionRecord, ExecutionState, ReplayDecision
from nexus_sdk.payments.sqlite_state import (
    ExposureCeilingExceededError,
    SQLiteGatewayStateStore,
    StateConflictError,
)


def record(number: int = 1) -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=f"exec-{number}",
        transaction_intent_id=f"intent-{number}",
        canonical_digest=f"sha256:canonical-{number}",
        idempotency_key=f"idem-{number}",
        authority_grant_id="grant-child",
        revocation_epoch=4,
    )


def persist_accepted(store: SQLiteGatewayStateStore, initial: ExecutionRecord) -> ExecutionRecord:
    store.create(initial)
    accepted = initial.transition(ExecutionState.POLICY_ACCEPTED)
    assert store.compare_and_swap(expected=initial, updated=accepted)
    return accepted


def test_replay_decisions_survive_restart(tmp_path):
    path = tmp_path / "gateway.db"
    first = SQLiteGatewayStateStore(path)
    assert first.consume(namespace="payment", key="nonce-1", digest="sha256:a") is ReplayDecision.ACCEPTED

    restored = SQLiteGatewayStateStore(path)
    assert restored.consume(namespace="payment", key="nonce-1", digest="sha256:a") is ReplayDecision.IDEMPOTENT
    assert restored.consume(namespace="payment", key="nonce-1", digest="sha256:b") is ReplayDecision.CONFLICT


def test_concurrent_replay_consumption_has_one_winner(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")

    def consume_once():
        return store.consume(namespace="payment", key="nonce-1", digest="sha256:a")

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: consume_once(), range(20)))
    assert results.count(ReplayDecision.ACCEPTED) == 1
    assert results.count(ReplayDecision.IDEMPOTENT) == 19


def test_execution_compare_and_swap_rejects_stale_writer(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    initial = record()
    store.create(initial)
    accepted = initial.transition(ExecutionState.POLICY_ACCEPTED)
    assert store.compare_and_swap(expected=initial, updated=accepted) is True
    failed = initial.transition(ExecutionState.FAILED)
    assert store.compare_and_swap(expected=initial, updated=failed) is False
    assert store.get(initial.execution_id) == accepted


def test_execution_and_idempotency_keys_are_unique(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    initial = record()
    store.create(initial)
    with pytest.raises(StateConflictError):
        store.create(initial)
    same_idempotency = ExecutionRecord(
        execution_id="exec-2",
        transaction_intent_id="intent-2",
        canonical_digest="sha256:other",
        idempotency_key=initial.idempotency_key,
        authority_grant_id="grant-child",
        revocation_epoch=4,
    )
    with pytest.raises(StateConflictError):
        store.create(same_idempotency)


def test_concurrent_reservations_cannot_exceed_aggregate_ceiling(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    records = tuple(persist_accepted(store, record(number)) for number in (1, 2))

    def reserve(item):
        try:
            return store.reserve(
                item,
                amount_minor=60,
                currency="USD",
                ceilings_minor={"grant-root": 100, "grant-child": 100},
            )
        except ExposureCeilingExceededError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        reservations = list(executor.map(reserve, records))
    assert sum(value is not None for value in reservations) == 1


def test_committed_exposure_cannot_be_released(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    initial = persist_accepted(store, record())
    reservation_id = store.reserve(
        initial,
        amount_minor=50,
        currency="USD",
        ceilings_minor={"grant-root": 100},
    )
    store.commit(reservation_id, settlement_id="settlement-1")
    with pytest.raises(StateConflictError):
        store.release(reservation_id, reason="unsafe rollback")


def test_reservation_requires_persisted_policy_accepted_record(tmp_path):
    store = SQLiteGatewayStateStore(tmp_path / "gateway.db")
    proposed = record()
    store.create(proposed)
    with pytest.raises(StateConflictError, match="policy acceptance"):
        store.reserve(
            proposed,
            amount_minor=50,
            currency="USD",
            ceilings_minor={"grant-root": 100},
        )


def test_revocation_epoch_is_monotonic_and_durable(tmp_path):
    path = tmp_path / "gateway.db"
    store = SQLiteGatewayStateStore(path)
    assert store.current_revocation_epoch("principal-1") == 0
    assert store.advance_revocation_epoch("principal-1") == 1
    assert store.advance_revocation_epoch("principal-1") == 2
    restored = SQLiteGatewayStateStore(path)
    assert restored.current_revocation_epoch("principal-1") == 2
