"""
nexus_sdk/memory.py
NEXUS L4 Memory Governance: Memory Vaccine and persistence-scope management.

AI SAFE2 v3.1 uses protocol-independent persistence scopes:
  request       effect ends with the current request/interaction
  handle_scoped effect persists through an explicitly governed state handle
  durable       effect survives request/handle lifecycle
  swarm_shared  durable state shared across governed agents

Legacy NEXUS v0.3 zone names and serialized values remain accepted for the
v3.1 migration window, but new evidence emits the canonical vocabulary.

Reference: AI SAFE2 v3.1 S1.5, S1.6, M4.4, A2.5, A2.6, CP.5.MCP.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class MemoryZone(str, Enum):
    """Canonical v3.1 persistence scopes with v0.3 attribute aliases."""

    REQUEST = "request"
    HANDLE_SCOPED = "handle_scoped"
    DURABLE = "durable"
    SWARM_SHARED = "swarm_shared"

    # Source-compatible aliases for existing NEXUS callers.
    SESSION = "request"
    CROSS_SESSION = "handle_scoped"
    PERMANENT = "durable"

    @classmethod
    def _missing_(cls, value: object):
        """Accept legacy serialized NEXUS memory-zone values."""
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower().replace("-", "_")
        legacy = {
            "session": cls.REQUEST,
            "session_memory": cls.REQUEST,
            "cross_session": cls.HANDLE_SCOPED,
            "cross_session_memory": cls.HANDLE_SCOPED,
            "permanent": cls.DURABLE,
            "permanent_memory": cls.DURABLE,
            "swarm_shared_memory": cls.SWARM_SHARED,
        }
        return legacy.get(normalized)

    @property
    def requires_drift_check(self) -> bool:
        return self is not MemoryZone.REQUEST

    @property
    def requires_mandate(self) -> bool:
        return self in (MemoryZone.DURABLE, MemoryZone.SWARM_SHARED)


class MemoryWriteResult(str, Enum):
    ALLOWED = "allowed"
    BLOCKED_DRIFT = "blocked_drift"
    BLOCKED_NO_MANDATE = "blocked_no_mandate"
    BLOCKED_NO_PROVENANCE = "blocked_no_provenance"


@dataclass
class Provenance:
    owner_did: str
    timestamp: str
    session_id: str
    mandate_id: Optional[str]
    embedding_hash: str
    drift_score: float

    @property
    def state_handle_id(self) -> str:
        """Canonical v3.1 name for the legacy session_id field."""
        return self.session_id


@dataclass
class MemoryWriteDecision:
    result: MemoryWriteResult
    allowed: bool
    provenance: Optional[Provenance] = None
    drift_score: Optional[float] = None
    threshold: Optional[float] = None
    action: Optional[str] = None
    alert: Optional[str] = None


class MemoryVaccine:
    """Validate governed memory writes before they reach persistent state."""

    def __init__(
        self,
        agent_did: str,
        purpose_declaration: str,
        drift_threshold: float = 0.30,
        use_stub_embeddings: bool = False,
    ):
        self.agent_did = agent_did
        self.purpose_declaration = purpose_declaration
        self.drift_threshold = drift_threshold
        self._use_stub = use_stub_embeddings
        self._state_handle_id = str(uuid.uuid4())
        # Compatibility alias for existing callers and old evidence consumers.
        self._session_id = self._state_handle_id
        self._checkpoint_log: list[dict] = []

        if use_stub_embeddings:
            self._baseline_hash = hashlib.sha256(purpose_declaration.encode()).hexdigest()
        else:
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np

                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._baseline_embedding = self._model.encode(purpose_declaration)
                self._np = np
            except ImportError as exc:
                raise ImportError(
                    "sentence_transformers required for production mode.\n"
                    "pip install sentence-transformers\n"
                    "Or use use_stub_embeddings=True for testing."
                ) from exc

    def _compute_cosine_distance(self, content: str) -> float:
        if self._use_stub:
            if "POISON" in content.upper():
                return 0.45
            if "DRIFT_HIGH" in content.upper():
                return 0.35
            if "DRIFT_LOW" in content.upper():
                return 0.15
            return 0.05

        content_embedding = self._model.encode(content)
        np = self._np
        cosine_sim = np.dot(self._baseline_embedding, content_embedding) / (
            np.linalg.norm(self._baseline_embedding)
            * np.linalg.norm(content_embedding)
        )
        return float(1 - cosine_sim)

    def validate_write(
        self,
        content: str,
        zone: MemoryZone,
        owner_did: str,
        mandate_id: Optional[str] = None,
    ) -> MemoryWriteDecision:
        """Validate a proposed write using canonical v3.1 persistence semantics."""
        zone = MemoryZone(zone)

        if zone.requires_mandate and not mandate_id:
            return MemoryWriteDecision(
                result=MemoryWriteResult.BLOCKED_NO_MANDATE,
                allowed=False,
                action="HARD_BRAKE",
                alert=f"{zone.value} memory write attempted without mandate_id",
            )

        if zone is MemoryZone.REQUEST:
            provenance = self._build_provenance(content, owner_did, mandate_id, 0.0)
            return MemoryWriteDecision(
                result=MemoryWriteResult.ALLOWED,
                allowed=True,
                provenance=provenance,
                drift_score=0.0,
            )

        drift_score = self._compute_cosine_distance(content)
        if drift_score > self.drift_threshold:
            self._log_blocked_write(content, owner_did, drift_score, zone)
            return MemoryWriteDecision(
                result=MemoryWriteResult.BLOCKED_DRIFT,
                allowed=False,
                drift_score=drift_score,
                threshold=self.drift_threshold,
                action="HARD_BRAKE",
                alert=(
                    "MEMORY_POISONING_DETECTED: "
                    f"scope={zone.value} drift_score={drift_score:.3f} "
                    f"> threshold={self.drift_threshold}"
                ),
            )

        provenance = self._build_provenance(content, owner_did, mandate_id, drift_score)
        return MemoryWriteDecision(
            result=MemoryWriteResult.ALLOWED,
            allowed=True,
            provenance=provenance,
            drift_score=drift_score,
        )

    def _build_provenance(
        self,
        content: str,
        owner_did: str,
        mandate_id: Optional[str],
        drift_score: float,
    ) -> Provenance:
        return Provenance(
            owner_did=owner_did,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._state_handle_id,
            mandate_id=mandate_id,
            embedding_hash=hashlib.sha256(content.encode()).hexdigest(),
            drift_score=drift_score,
        )

    def _log_blocked_write(
        self,
        content: str,
        owner_did: str,
        drift_score: float,
        zone: MemoryZone,
    ) -> None:
        self._checkpoint_log.append({
            "event": "MEMORY_WRITE_BLOCKED",
            "owner_did": owner_did,
            "persistence_scope": zone.value,
            "drift_score": drift_score,
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def create_checkpoint(self) -> dict:
        """Generate a state checkpoint for durable governed memory."""
        checkpoint = {
            "checkpoint_id": f"ckpt_{uuid.uuid4().hex[:16]}",
            "agent_did": self.agent_did,
            "state_handle_id": self._state_handle_id,
            # Compatibility field retained during v3.1 migration.
            "session_id": self._session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purpose_hash": hashlib.sha256(self.purpose_declaration.encode()).hexdigest(),
            "drift_threshold": self.drift_threshold,
            "blocked_write_count": len([
                event
                for event in self._checkpoint_log
                if event["event"] == "MEMORY_WRITE_BLOCKED"
            ]),
            "signature_stub": "REPLACE_WITH_MLDSA65",
        }
        self._checkpoint_log.append({
            "event": "CHECKPOINT_CREATED",
            "checkpoint_id": checkpoint["checkpoint_id"],
            "timestamp": checkpoint["timestamp"],
        })
        return checkpoint

    def get_incident_log(self) -> list[dict]:
        """Return incident and checkpoint events for this state handle."""
        return list(self._checkpoint_log)

    def to_acs_guardian_context(
        self,
        content: str,
        zone: MemoryZone,
        owner_did: str,
        decision: "MemoryWriteDecision",
    ) -> dict:
        """Export memory context for Guardian evaluation."""
        zone = MemoryZone(zone)
        provenance_dict: dict = {
            "source_did": owner_did,
            "persistence_scope": zone.value,
            # Legacy bridge field retained while Guardian schemas migrate.
            "zone": zone.value,
        }
        if decision.drift_score is not None:
            provenance_dict["drift_score"] = round(decision.drift_score, 4)
        if decision.provenance:
            provenance_dict["embedding_hash"] = decision.provenance.embedding_hash
            provenance_dict["state_handle_id"] = decision.provenance.state_handle_id
            provenance_dict["session_id"] = decision.provenance.session_id
            provenance_dict["mandate_id"] = decision.provenance.mandate_id

        if self._checkpoint_log:
            latest_checkpoint = max(
                (
                    event
                    for event in self._checkpoint_log
                    if event.get("event") == "CHECKPOINT_CREATED"
                ),
                key=lambda event: event.get("timestamp", ""),
                default=None,
            )
            if latest_checkpoint:
                provenance_dict["checkpoint_timestamp"] = latest_checkpoint["timestamp"]

        return provenance_dict

    def validate_write_with_guardian(
        self,
        content: str,
        zone: "MemoryZone",
        owner_did: str,
        mandate_id: Optional[str] = None,
    ) -> tuple["MemoryWriteDecision", dict]:
        decision = self.validate_write(content, zone, owner_did, mandate_id)
        guardian_ctx = self.to_acs_guardian_context(content, zone, owner_did, decision)
        return decision, guardian_ctx


class JouleWorkAccount:
    """L5 economic primitive for bounded agent resource accounting."""

    def __init__(
        self,
        agent_did: str,
        initial_balance_jw: int = 0,
        base_rate_per_period: int = 5000,
        efficiency_floor: float = 0.85,
        circuit_break_on_negative: bool = True,
    ):
        self.agent_did = agent_did
        self.balance_jw = initial_balance_jw
        self.base_rate_per_period = base_rate_per_period
        self.efficiency_floor = efficiency_floor
        self.circuit_break_on_negative = circuit_break_on_negative
        self._period_start = time.time()
        self._period_jw_earned = 0
        self._period_jw_spent = 0
        self._transfer_log: list[dict] = []

    @property
    def efficiency_ratio(self) -> float:
        if self._period_jw_spent == 0:
            return 1.0
        return self._period_jw_earned / self._period_jw_spent

    def credit(self, amount_jw: int, source: str = "wage") -> None:
        self.balance_jw += amount_jw
        self._period_jw_earned += amount_jw

    def debit(self, amount_jw: int) -> dict:
        self._period_jw_spent += amount_jw
        self.balance_jw -= amount_jw

        if self.circuit_break_on_negative and self.balance_jw < 0:
            return {
                "status": "CIRCUIT_BREAK",
                "reason": "NEGATIVE_BALANCE",
                "balance_jw": self.balance_jw,
            }

        if self._period_jw_spent > 0 and self._period_jw_earned > 0:
            if self.efficiency_ratio < self.efficiency_floor:
                return {
                    "status": "CIRCUIT_BREAK",
                    "reason": "EFFICIENCY_BELOW_FLOOR",
                    "eta": self.efficiency_ratio,
                    "floor": self.efficiency_floor,
                }

        return {
            "status": "OK",
            "balance_jw": self.balance_jw,
            "eta": self.efficiency_ratio,
        }

    def transfer_to(self, recipient_did: str, amount_jw: int, service: str) -> dict:
        if amount_jw > self.balance_jw:
            return {
                "error": "INSUFFICIENT_JW_BALANCE",
                "balance_jw": self.balance_jw,
                "requested": amount_jw,
            }
        self.balance_jw -= amount_jw
        transfer = {
            "transfer_id": f"xfr_{uuid.uuid4().hex[:16]}",
            "from_did": self.agent_did,
            "to_did": recipient_did,
            "amount_jw": amount_jw,
            "service": service,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._transfer_log.append(transfer)
        return transfer

    def pay_period_wage(self) -> dict:
        self.credit(self.base_rate_per_period, source="period_wage")
        return {
            "wage_event": "PERIOD_WAGE",
            "agent_did": self.agent_did,
            "amount_jw": self.base_rate_per_period,
            "new_balance": self.balance_jw,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
