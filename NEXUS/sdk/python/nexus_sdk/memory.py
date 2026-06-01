"""
nexus_sdk/memory.py
NEXUS L4 Memory Governance: Memory Vaccine + 4-Zone Management

The Memory Vaccine is the core defense against memory poisoning attacks.
MINJA achieves >95% injection success in production agents. This module
implements cosine-distance drift detection on every cross-session write.

PRODUCTION requirements:
  - SentenceTransformer model (or equivalent embedding API)
  - pip install sentence-transformers numpy

TESTING (no GPU/model required):
  - Set use_stub_embeddings=True in MemoryVaccine constructor
  - Stub uses random vectors; validates the contract, not the semantics
  - All test assertions pass with the stub; production uses real embeddings

Reference: AI SAFE2 v3.0 S1.5, S1.6, M4.4, A2.5, A2.6
"""

from __future__ import annotations
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class MemoryZone(str, Enum):
    """Four NEXUS memory zones with different provenance and rollback requirements."""
    SESSION = "SESSION_MEMORY"           # Purged on session end; no rollback needed
    CROSS_SESSION = "CROSS_SESSION_MEMORY"  # Rollback to any 24h checkpoint
    PERMANENT = "PERMANENT_MEMORY"       # Principal-level mandate required
    SWARM_SHARED = "SWARM_SHARED_MEMORY" # Quorum required for permanent write


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


@dataclass
class MemoryWriteDecision:
    result: MemoryWriteResult
    allowed: bool
    provenance: Optional[Provenance] = None
    drift_score: Optional[float] = None
    threshold: Optional[float] = None
    action: Optional[str] = None  # "HARD_BRAKE" if blocked
    alert: Optional[str] = None


class MemoryVaccine:
    """
    L4 Memory Vaccine: validates every cross-session memory write.

    How it works:
    1. Encodes the proposed memory content as an embedding vector
    2. Computes cosine distance to the agent's purposeDeclaration baseline
    3. If distance > drift_threshold (default 0.30): HARD_BRAKE + alert
    4. If allowed: attaches cryptographic provenance before write

    What a drift score means:
    - 0.00: identical to purpose (safe)
    - 0.15: related but somewhat divergent (monitor)
    - 0.30: threshold (default hard brake trigger)
    - 0.50+: highly divergent - likely poisoning attempt

    MINJA attack pattern: plants semantically distant content in small
    chunks over multiple sessions. Each chunk scores 0.25; cumulative
    effect trains the agent to a new belief. This detector catches
    individual writes; you also need A2.6 corpus diff tracking for
    multi-session cumulative drift.
    """

    def __init__(self, agent_did: str, purpose_declaration: str,
                 drift_threshold: float = 0.30,
                 use_stub_embeddings: bool = False):
        self.agent_did = agent_did
        self.purpose_declaration = purpose_declaration
        self.drift_threshold = drift_threshold
        self._use_stub = use_stub_embeddings
        self._session_id = str(uuid.uuid4())
        self._checkpoint_log: list[dict] = []

        if use_stub_embeddings:
            # Testing mode: deterministic stub embeddings
            # Drift score for stub = 0.0 unless content contains "POISON" keyword
            self._baseline_hash = hashlib.sha256(purpose_declaration.encode()).hexdigest()
        else:
            # Production mode: real sentence embeddings
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._baseline_embedding = self._model.encode(purpose_declaration)
                self._np = np
            except ImportError:
                raise ImportError(
                    "sentence_transformers required for production mode.\n"
                    "pip install sentence-transformers\n"
                    "Or use use_stub_embeddings=True for testing."
                )

    def _compute_cosine_distance(self, content: str) -> float:
        """Compute cosine distance between content and purposeDeclaration baseline."""
        if self._use_stub:
            # Stub: any content with 'POISON' simulates a drift score above threshold
            if "POISON" in content.upper():
                return 0.45  # Simulate detected poisoning
            if "DRIFT_HIGH" in content.upper():
                return 0.35
            if "DRIFT_LOW" in content.upper():
                return 0.15
            return 0.05   # Normal content: low distance
        else:
            content_embedding = self._model.encode(content)
            np = self._np
            cosine_sim = np.dot(self._baseline_embedding, content_embedding) / (
                np.linalg.norm(self._baseline_embedding) *
                np.linalg.norm(content_embedding)
            )
            return float(1 - cosine_sim)

    def validate_write(self, content: str, zone: MemoryZone,
                       owner_did: str, mandate_id: Optional[str] = None) -> MemoryWriteDecision:
        """
        Validates a proposed memory write before it reaches the store.
        Called by the NEXUS gateway before every memory write operation.

        Args:
            content: The proposed memory content
            zone: Which memory zone (SESSION, CROSS_SESSION, PERMANENT, SWARM_SHARED)
            owner_did: DID of the agent requesting the write
            mandate_id: Required for PERMANENT_MEMORY writes

        Returns:
            MemoryWriteDecision with allowed=True/False and provenance if allowed
        """
        # PERMANENT writes require a mandate
        if zone == MemoryZone.PERMANENT and not mandate_id:
            return MemoryWriteDecision(
                result=MemoryWriteResult.BLOCKED_NO_MANDATE,
                allowed=False,
                action="HARD_BRAKE",
                alert="PERMANENT_MEMORY write attempted without mandate_id"
            )

        # SESSION writes don't need drift checking (purged anyway)
        if zone == MemoryZone.SESSION:
            provenance = self._build_provenance(content, owner_did, mandate_id, 0.0)
            return MemoryWriteDecision(
                result=MemoryWriteResult.ALLOWED, allowed=True,
                provenance=provenance, drift_score=0.0
            )

        # Drift detection for CROSS_SESSION, PERMANENT, SWARM_SHARED
        drift_score = self._compute_cosine_distance(content)

        if drift_score > self.drift_threshold:
            # Log the attempt for L6 incident corpus
            self._log_blocked_write(content, owner_did, drift_score)
            return MemoryWriteDecision(
                result=MemoryWriteResult.BLOCKED_DRIFT,
                allowed=False,
                drift_score=drift_score,
                threshold=self.drift_threshold,
                action="HARD_BRAKE",
                alert=f"MEMORY_POISONING_DETECTED: drift_score={drift_score:.3f} > threshold={self.drift_threshold}"
            )

        # Allowed: attach provenance
        provenance = self._build_provenance(content, owner_did, mandate_id, drift_score)
        return MemoryWriteDecision(
            result=MemoryWriteResult.ALLOWED, allowed=True,
            provenance=provenance, drift_score=drift_score
        )

    def _build_provenance(self, content: str, owner_did: str,
                          mandate_id: Optional[str], drift_score: float) -> Provenance:
        embedding_hash = hashlib.sha256(content.encode()).hexdigest()
        return Provenance(
            owner_did=owner_did,
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self._session_id,
            mandate_id=mandate_id,
            embedding_hash=embedding_hash,
            drift_score=drift_score,
        )

    def _log_blocked_write(self, content: str, owner_did: str, drift_score: float):
        """Append to L6 incident corpus feed (production: write to NOR chain)."""
        self._checkpoint_log.append({
            "event": "MEMORY_WRITE_BLOCKED",
            "owner_did": owner_did,
            "drift_score": drift_score,
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def create_checkpoint(self) -> dict:
        """
        Generate a signed 24-hour AGENT_STATE checkpoint.
        Production: sign with ML-DSA-65 and write to L6 incident corpus.
        NEXUS requirement: all cross-session agents checkpoint every 24h.
        """
        checkpoint = {
            "checkpoint_id": f"ckpt_{uuid.uuid4().hex[:16]}",
            "agent_did": self.agent_did,
            "session_id": self._session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purpose_hash": hashlib.sha256(self.purpose_declaration.encode()).hexdigest(),
            "drift_threshold": self.drift_threshold,
            "blocked_write_count": len([e for e in self._checkpoint_log
                                        if e["event"] == "MEMORY_WRITE_BLOCKED"]),
            # PRODUCTION: add ML-DSA-65 signature here
            "signature_stub": "REPLACE_WITH_MLDSA65",
        }
        return checkpoint

    def get_incident_log(self) -> list[dict]:
        """Return the L6 incident feed entries from this session."""
        return list(self._checkpoint_log)


    def to_acs_guardian_context(self, content: str, zone: MemoryZone,
                                  owner_did: str, decision: "MemoryWriteDecision") -> dict:
        """
        Export memory write context in ACS NEXUSMemoryProvenance format.
        Pass this to NEXUSACSBridge.build_memory_store_request() for Guardian evaluation.

        The Guardian receives:
          - zone: which memory zone (PERMANENT requires mandate enforcement)
          - drift_score: enables tighter Guardian-level threshold (0.25 vs 0.30)
          - checkpoint_timestamp: stale checkpoint detection (>48h)
          - source_did: identity of the agent requesting the write

        This is the data ACS's memory hooks cannot compute without NEXUS Vaccine.
        Including it makes memory Guardian policies semantically rich.
        """
        provenance_dict: dict = {
            "source_did": owner_did,
            "zone": zone.value,
        }
        if decision.drift_score is not None:
            provenance_dict["drift_score"] = round(decision.drift_score, 4)
        if decision.provenance:
            provenance_dict["embedding_hash"] = decision.provenance.embedding_hash
            provenance_dict["session_id"] = decision.provenance.session_id
            provenance_dict["mandate_id"] = decision.provenance.mandate_id

        # Include most recent checkpoint timestamp if available
        if self._checkpoint_log:
            latest_checkpoint = max(
                (e for e in self._checkpoint_log if e.get("event") == "CHECKPOINT_CREATED"),
                key=lambda e: e.get("timestamp", ""),
                default=None,
            )
            if latest_checkpoint:
                provenance_dict["checkpoint_timestamp"] = latest_checkpoint["timestamp"]

        return provenance_dict

    def validate_write_with_guardian(self, content: str, zone: "MemoryZone",
                                      owner_did: str,
                                      mandate_id: Optional[str] = None) -> tuple["MemoryWriteDecision", dict]:
        """
        Validate a memory write and return both the Vaccine decision AND
        the ACS Guardian context dict for optional Guardian evaluation.

        Usage:
            vaccine_result, guardian_ctx = vaccine.validate_write_with_guardian(
                content, zone, owner_did
            )
            # Optionally: acs_bridge.build_memory_store_request([content], owner_did, guardian_ctx)
        """
        decision = self.validate_write(content, zone, owner_did, mandate_id)
        guardian_ctx = self.to_acs_guardian_context(content, zone, owner_did, decision)
        return decision, guardian_ctx


class JouleWorkAccount:
    """
    L5 JouleWork economic primitive.
    Every agent maintains a balance. Efficiency below floor triggers circuit break.
    Inter-agent JW transfers enable the ZHC internal micro-economy.
    """

    def __init__(self, agent_did: str, initial_balance_jw: int = 0,
                 base_rate_per_period: int = 5000,
                 efficiency_floor: float = 0.85,
                 circuit_break_on_negative: bool = True):
        self.agent_did = agent_did
        self.balance_jw = initial_balance_jw
        self.base_rate_per_period = base_rate_per_period  # JW per 15-min period
        self.efficiency_floor = efficiency_floor
        self.circuit_break_on_negative = circuit_break_on_negative
        self._period_start = time.time()
        self._period_jw_earned = 0
        self._period_jw_spent = 0
        self._transfer_log: list[dict] = []

    @property
    def efficiency_ratio(self) -> float:
        """eta = JW_output / JW_input. Below floor = circuit break."""
        if self._period_jw_spent == 0:
            return 1.0
        return self._period_jw_earned / self._period_jw_spent

    def credit(self, amount_jw: int, source: str = "wage"):
        """Credit JW to account (wage payment or transfer received)."""
        self.balance_jw += amount_jw
        self._period_jw_earned += amount_jw

    def debit(self, amount_jw: int) -> dict:
        """Debit JW for a task. Returns circuit break status."""
        self._period_jw_spent += amount_jw
        self.balance_jw -= amount_jw

        if self.circuit_break_on_negative and self.balance_jw < 0:
            return {"status": "CIRCUIT_BREAK", "reason": "NEGATIVE_BALANCE",
                    "balance_jw": self.balance_jw}

        # Only check efficiency if we have both spend AND earn data this period
        if self._period_jw_spent > 0 and self._period_jw_earned > 0:
            if self.efficiency_ratio < self.efficiency_floor:
                return {"status": "CIRCUIT_BREAK", "reason": "EFFICIENCY_BELOW_FLOOR",
                        "eta": self.efficiency_ratio, "floor": self.efficiency_floor}

        return {"status": "OK", "balance_jw": self.balance_jw,
                "eta": self.efficiency_ratio}

    def transfer_to(self, recipient_did: str, amount_jw: int, service: str) -> dict:
        """Intra-mesh JW transfer for inter-agent commerce."""
        if amount_jw > self.balance_jw:
            return {"error": "INSUFFICIENT_JW_BALANCE",
                    "balance_jw": self.balance_jw, "requested": amount_jw}
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
        """Pay the base period wage (called every 15 minutes in ZHC deployments)."""
        self.credit(self.base_rate_per_period, source="period_wage")
        return {
            "wage_event": "PERIOD_WAGE",
            "agent_did": self.agent_did,
            "amount_jw": self.base_rate_per_period,
            "new_balance": self.balance_jw,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
