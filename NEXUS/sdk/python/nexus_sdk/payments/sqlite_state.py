"""Crash-durable reference state for the Sovereign Payment Gateway.

SQLite supplies real transactions, uniqueness, and compare-and-swap semantics
for a single-host reference deployment. It is intentionally classified as
REFERENCE assurance: operators still need protected storage, backup, access
control, monitoring, and a deployment-specific availability decision.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Mapping
from pathlib import Path

from nexus_sdk.payments.execution_plane import (
    ComponentAssurance,
    ExecutionRecord,
    ExecutionState,
    ReplayDecision,
)

__all__ = ["ExposureCeilingExceededError", "SQLiteGatewayStateStore", "StateConflictError"]


class StateConflictError(RuntimeError):
    """A durable write conflicts with existing canonical state."""


class ExposureCeilingExceededError(StateConflictError):
    """An atomic reservation would exceed at least one authority ceiling."""


class SQLiteGatewayStateStore:
    """Gateway State Vault (`SQLiteGatewayStateStore`)."""

    human_name = "Gateway State Vault"
    technical_name = "SQLiteGatewayStateStore"
    assurance = ComponentAssurance.REFERENCE

    def __init__(self, path: str | Path, *, busy_timeout_ms: int = 5000) -> None:
        self.path = str(Path(path).resolve())
        self.busy_timeout_ms = busy_timeout_ms
        self._schema_lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms:d}")
        return connection

    def _initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._schema_lock, self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS replay_keys (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    digest TEXT NOT NULL,
                    consumed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (namespace, key)
                );
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    canonical_digest TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    record_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revocation_epochs (
                    principal_id TEXT PRIMARY KEY,
                    epoch INTEGER NOT NULL CHECK (epoch >= 0)
                );
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL UNIQUE,
                    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('reserved', 'committed', 'released')),
                    settlement_id TEXT UNIQUE,
                    release_reason TEXT,
                    FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
                );
                CREATE TABLE IF NOT EXISTS reservation_scopes (
                    reservation_id TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    PRIMARY KEY (reservation_id, scope_id),
                    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
                );
                CREATE INDEX IF NOT EXISTS reservation_scope_lookup
                    ON reservation_scopes(scope_id, reservation_id);
                """
            )

    @staticmethod
    def _encode(record: ExecutionRecord) -> str:
        values = dict(record.__dict__)
        values["state"] = record.state.value
        values["evidence_refs"] = list(record.evidence_refs)
        return json.dumps(values, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(payload: str) -> ExecutionRecord:
        values = json.loads(payload)
        values["state"] = ExecutionState(values["state"])
        values["evidence_refs"] = tuple(values.get("evidence_refs", ()))
        return ExecutionRecord(**values)

    def consume(self, *, namespace: str, key: str, digest: str) -> ReplayDecision:
        if not namespace or not key or not digest:
            raise ValueError("namespace, key, and digest are required")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT digest FROM replay_keys WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO replay_keys(namespace, key, digest) VALUES (?, ?, ?)",
                    (namespace, key, digest),
                )
                connection.commit()
                return ReplayDecision.ACCEPTED
            connection.commit()
            return (
                ReplayDecision.IDEMPOTENT
                if existing["digest"] == digest
                else ReplayDecision.CONFLICT
            )

    def consume_reserved_release(self, *, execution: ExecutionRecord,
                                 namespace: str, key: str,
                                 digest: str) -> ReplayDecision | None:
        """Atomically require an active reservation and consume the release key."""
        if not namespace or not key or not digest:
            raise ValueError("namespace, key, and digest are required")
        if not execution.reservation_id:
            return None
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT e.record_json
                   FROM executions e
                   JOIN reservations r ON r.execution_id = e.execution_id
                   WHERE e.execution_id = ? AND r.reservation_id = ?
                     AND r.status = 'reserved'""",
                (execution.execution_id, execution.reservation_id),
            ).fetchone()
            if row is None or self._decode(row["record_json"]) != execution:
                connection.rollback()
                return None
            existing = connection.execute(
                "SELECT digest FROM replay_keys WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO replay_keys(namespace, key, digest) VALUES (?, ?, ?)",
                    (namespace, key, digest),
                )
                connection.commit()
                return ReplayDecision.ACCEPTED
            connection.commit()
            return (
                ReplayDecision.IDEMPOTENT
                if existing["digest"] == digest
                else ReplayDecision.CONFLICT
            )

    def create(self, record: ExecutionRecord) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """INSERT INTO executions(
                           execution_id, version, canonical_digest, idempotency_key, record_json
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        record.execution_id, record.version, record.canonical_digest,
                        record.idempotency_key, self._encode(record),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise StateConflictError("execution or idempotency key already exists") from exc

    def get(self, execution_id: str) -> ExecutionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM executions WHERE execution_id = ?", (execution_id,)
            ).fetchone()
        return self._decode(row["record_json"]) if row is not None else None

    def compare_and_swap(self, *, expected: ExecutionRecord, updated: ExecutionRecord) -> bool:
        if expected.execution_id != updated.execution_id or updated.version != expected.version + 1:
            raise StateConflictError("compare-and-swap requires the same execution and next version")
        immutable_fields = (
            "transaction_intent_id", "canonical_digest", "idempotency_key",
            "authority_grant_id", "revocation_epoch",
        )
        if any(getattr(expected, name) != getattr(updated, name) for name in immutable_fields):
            raise StateConflictError("compare-and-swap cannot replace canonical execution identity")
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE executions
                   SET version = ?, record_json = ?
                   WHERE execution_id = ? AND version = ? AND canonical_digest = ?""",
                (
                    updated.version, self._encode(updated), expected.execution_id,
                    expected.version, expected.canonical_digest,
                ),
            )
            return cursor.rowcount == 1

    def current_revocation_epoch(self, principal_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT epoch FROM revocation_epochs WHERE principal_id = ?", (principal_id,)
            ).fetchone()
        return int(row["epoch"]) if row is not None else 0

    def advance_revocation_epoch(self, principal_id: str) -> int:
        if not principal_id:
            raise ValueError("principal_id is required")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO revocation_epochs(principal_id, epoch) VALUES (?, 1)
                   ON CONFLICT(principal_id) DO UPDATE SET epoch = epoch + 1""",
                (principal_id,),
            )
            row = connection.execute(
                "SELECT epoch FROM revocation_epochs WHERE principal_id = ?", (principal_id,)
            ).fetchone()
            connection.commit()
        return int(row["epoch"])

    def reserve(self, record: ExecutionRecord, *, amount_minor: int, currency: str,
                ceilings_minor: Mapping[str, int]) -> str:
        if amount_minor < 0 or not currency or not ceilings_minor:
            raise ValueError("non-negative amount, currency, and authority ceilings are required")
        if any(not scope or ceiling < 0 for scope, ceiling in ceilings_minor.items()):
            raise ValueError("authority scope identifiers and ceilings must be valid")
        if record.state is not ExecutionState.POLICY_ACCEPTED:
            raise StateConflictError("exposure can be reserved only after policy acceptance")
        reservation_id = f"res_{uuid.uuid4().hex}"
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            execution = connection.execute(
                "SELECT record_json FROM executions WHERE execution_id = ?",
                (record.execution_id,),
            ).fetchone()
            if execution is None or self._decode(execution["record_json"]) != record:
                connection.rollback()
                raise StateConflictError("reservation requires the persisted canonical execution")
            for scope_id, ceiling in ceilings_minor.items():
                row = connection.execute(
                    """SELECT COALESCE(SUM(r.amount_minor), 0) AS exposure
                       FROM reservations r
                       JOIN reservation_scopes s ON s.reservation_id = r.reservation_id
                       WHERE s.scope_id = ? AND r.currency = ?
                         AND r.status IN ('reserved', 'committed')""",
                    (scope_id, currency),
                ).fetchone()
                if int(row["exposure"]) + amount_minor > ceiling:
                    connection.rollback()
                    raise ExposureCeilingExceededError(
                        f"authority ceiling exceeded for {scope_id}"
                    )
            try:
                connection.execute(
                    """INSERT INTO reservations(
                           reservation_id, execution_id, amount_minor, currency, status
                       ) VALUES (?, ?, ?, ?, 'reserved')""",
                    (reservation_id, record.execution_id, amount_minor, currency),
                )
                connection.executemany(
                    "INSERT INTO reservation_scopes(reservation_id, scope_id) VALUES (?, ?)",
                    [(reservation_id, scope_id) for scope_id in ceilings_minor],
                )
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise StateConflictError("execution already has an exposure reservation") from exc
            connection.commit()
        return reservation_id

    def reserve_execution(self, record: ExecutionRecord, *, amount_minor: int,
                          currency: str,
                          ceilings_minor: Mapping[str, int]) -> ExecutionRecord:
        """Atomically reserve exposure and advance the execution to RESERVED."""
        if amount_minor < 0 or not currency or not ceilings_minor:
            raise ValueError("non-negative amount, currency, and authority ceilings are required")
        if any(not scope or ceiling < 0 for scope, ceiling in ceilings_minor.items()):
            raise ValueError("authority scope identifiers and ceilings must be valid")
        if record.state is not ExecutionState.POLICY_ACCEPTED:
            raise StateConflictError("exposure can be reserved only after policy acceptance")
        reservation_id = f"res_{uuid.uuid4().hex}"
        updated = record.transition(ExecutionState.RESERVED, reservation_id=reservation_id)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if not self._execution_matches(connection, record):
                connection.rollback()
                raise StateConflictError("reservation requires the persisted canonical execution")
            for scope_id, ceiling in ceilings_minor.items():
                row = connection.execute(
                    """SELECT COALESCE(SUM(r.amount_minor), 0) AS exposure
                       FROM reservations r
                       JOIN reservation_scopes s ON s.reservation_id = r.reservation_id
                       WHERE s.scope_id = ? AND r.currency = ?
                         AND r.status IN ('reserved', 'committed')""",
                    (scope_id, currency),
                ).fetchone()
                if int(row["exposure"]) + amount_minor > ceiling:
                    connection.rollback()
                    raise ExposureCeilingExceededError(
                        f"authority ceiling exceeded for {scope_id}"
                    )
            try:
                connection.execute(
                    """INSERT INTO reservations(
                           reservation_id, execution_id, amount_minor, currency, status
                       ) VALUES (?, ?, ?, ?, 'reserved')""",
                    (reservation_id, record.execution_id, amount_minor, currency),
                )
                connection.executemany(
                    "INSERT INTO reservation_scopes(reservation_id, scope_id) VALUES (?, ?)",
                    [(reservation_id, scope_id) for scope_id in ceilings_minor],
                )
                self._replace_execution(connection, record, updated)
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise StateConflictError("execution already has an exposure reservation") from exc
            connection.commit()
        return updated

    def commit(self, reservation_id: str, *, settlement_id: str) -> None:
        if not settlement_id:
            raise ValueError("settlement_id is required")
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """UPDATE reservations SET status = 'committed', settlement_id = ?
                       WHERE reservation_id = ? AND status = 'reserved'""",
                    (settlement_id, reservation_id),
                )
                if cursor.rowcount != 1:
                    raise StateConflictError("reservation is missing or no longer reservable")
        except sqlite3.IntegrityError as exc:
            raise StateConflictError("settlement identifier is already committed") from exc

    def release(self, reservation_id: str, *, reason: str) -> None:
        if not reason:
            raise ValueError("release reason is required")
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE reservations SET status = 'released', release_reason = ?
                   WHERE reservation_id = ? AND status = 'reserved'""",
                (reason, reservation_id),
            )
            if cursor.rowcount != 1:
                raise StateConflictError("reservation is missing or cannot be released")

    def settle_execution(self, *, expected: ExecutionRecord,
                         updated: ExecutionRecord) -> bool:
        """Atomically commit exposure and record authoritative settlement."""
        if (
            updated.state is not ExecutionState.SETTLED
            or not updated.settlement_id
            or not expected.reservation_id
        ):
            raise StateConflictError("settlement requires bound execution and settlement ids")
        self._validate_atomic_transition(expected, updated)
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                if not self._execution_matches(connection, expected):
                    connection.rollback()
                    return False
                reservation = connection.execute(
                    """UPDATE reservations
                       SET status = 'committed', settlement_id = ?
                       WHERE reservation_id = ? AND execution_id = ?
                         AND status = 'reserved'""",
                    (updated.settlement_id, expected.reservation_id, expected.execution_id),
                )
                if reservation.rowcount != 1:
                    connection.rollback()
                    return False
                self._replace_execution(connection, expected, updated)
                connection.commit()
                return True
        except sqlite3.IntegrityError as exc:
            raise StateConflictError("settlement identifier is already committed") from exc

    def release_execution(self, *, expected: ExecutionRecord,
                          updated: ExecutionRecord, reason: str) -> bool:
        """Atomically release held exposure and record a terminal non-settlement."""
        if (
            updated.state not in {ExecutionState.FAILED, ExecutionState.RELEASED}
            or not expected.reservation_id
            or not reason
        ):
            raise StateConflictError("release requires a terminal state, reservation, and reason")
        self._validate_atomic_transition(expected, updated)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if not self._execution_matches(connection, expected):
                connection.rollback()
                return False
            reservation = connection.execute(
                """UPDATE reservations
                   SET status = 'released', release_reason = ?
                   WHERE reservation_id = ? AND execution_id = ?
                     AND status = 'reserved'""",
                (reason, expected.reservation_id, expected.execution_id),
            )
            if reservation.rowcount != 1:
                connection.rollback()
                return False
            self._replace_execution(connection, expected, updated)
            connection.commit()
            return True

    @staticmethod
    def _validate_atomic_transition(expected: ExecutionRecord,
                                    updated: ExecutionRecord) -> None:
        if expected.execution_id != updated.execution_id or updated.version != expected.version + 1:
            raise StateConflictError("atomic transition requires the same execution and next version")
        immutable_fields = (
            "transaction_intent_id", "canonical_digest", "idempotency_key",
            "authority_grant_id", "revocation_epoch",
        )
        if any(getattr(expected, name) != getattr(updated, name) for name in immutable_fields):
            raise StateConflictError("atomic transition cannot replace canonical execution identity")

    def _execution_matches(self, connection: sqlite3.Connection,
                           expected: ExecutionRecord) -> bool:
        row = connection.execute(
            "SELECT record_json FROM executions WHERE execution_id = ? AND version = ?",
            (expected.execution_id, expected.version),
        ).fetchone()
        return row is not None and self._decode(row["record_json"]) == expected

    def _replace_execution(self, connection: sqlite3.Connection,
                           expected: ExecutionRecord,
                           updated: ExecutionRecord) -> None:
        cursor = connection.execute(
            """UPDATE executions SET version = ?, record_json = ?
               WHERE execution_id = ? AND version = ? AND canonical_digest = ?""",
            (
                updated.version, self._encode(updated), expected.execution_id,
                expected.version, expected.canonical_digest,
            ),
        )
        if cursor.rowcount != 1:
            raise StateConflictError("execution changed during atomic transition")
