"""
nexus_sdk/cael.py
CAEL: Canonical Agent Exchange Layer
The single internal envelope for all NEXUS inter-agent communication.

Design principle: Internal richness, external compatibility.
CAEL carries everything - identity, PQC attestation, JW budget, delegation
provenance, OPA receipts, mandate IDs - then degrades gracefully when
bridging to MCP, A2A, OpenAI tool-calling, or raw REST.

Testing: run pytest tests/test_cael.py -v
Required: No external dependencies for core validation. OPA + SPIRE for production.
"""

from __future__ import annotations
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum


class Performative(str, Enum):
    """NEXUS L5 canonical performatives (APEM Section 9, AI SAFE2 v3.0)."""
    COMMAND = "command"
    OBSERVATION = "observation"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    DELEGATE = "delegate"
    IDENTITY_ASSERTION = "identity_assertion"
    CONFIG_CHANGE = "config_change"
    # L5 specific
    INFORM = "inform"
    REVOKE = "revoke"
    QUARANTINE = "quarantine"         # Swarm dissolution signal
    PERSONAL_ENROLL = "personal_enroll"
    MEMORY_CHECKPOINT = "memory_checkpoint"
    FLEET_REGISTER = "fleet_register"
    HEARTBEAT_MONITOR = "heartbeat_monitor"
    SWARM_DISSOLVE = "swarm_dissolve"


class ContextCompartment(str, Enum):
    """L4 context namespaces enforced by OPA at tool-calling layer."""
    TASK_CONTEXT = "TASK_CONTEXT"             # Untrusted: user inputs, tool results
    CREDENTIAL_SURFACE = "CREDENTIAL_SURFACE" # Zero exposure: system prompt, VCCs
    AGENT_STATE = "AGENT_STATE"               # Governed: cross-session memory


@dataclass
class CAELSender:
    agent_did: str
    spiffe_id: str
    jw_account: Optional[str] = None
    attestation_method: str = "spiffe-svid"
    svid_serial: Optional[str] = None
    signing_key_id: Optional[str] = None


@dataclass
class CAELBudget:
    max_cost_usd: float = 5.00
    max_joulework: int = 50000
    max_tokens: int = 120000
    max_runtime_sec: int = 180
    jw_cost_basis_multiplier: float = 1.3


@dataclass
class CAELPolicy:
    classification: str = "internal"
    jurisdiction: list[str] = field(default_factory=lambda: ["US"])
    approval_mode: str = "human_if_external_write"
    mandate_required: list[str] = field(default_factory=list)
    budget: CAELBudget = field(default_factory=CAELBudget)
    max_sub_delegation_depth: int = 2
    data_residency: Optional[str] = None
    secrets_scope: list[str] = field(default_factory=list)


@dataclass
class CAELDelegation:
    vcc_id: str
    delegation_depth: int = 0
    scope_attenuated: bool = True
    non_escalation: bool = True    # Gateway rejects any attempt to widen scope
    ttl: str = "PT1H"


@dataclass
class CAELMemory:
    context_compartment: ContextCompartment = ContextCompartment.TASK_CONTEXT
    state_ref: Optional[str] = None
    checkpoint_before_write: bool = True


@dataclass
class CAELTrace:
    trace_id: str = field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:20]}")
    span_id: str = field(default_factory=lambda: f"sp_{uuid.uuid4().hex[:8]}")
    causal_chain: list[str] = field(default_factory=list)


@dataclass
class JouleWorkCost:
    estimated_cost_jw: int = 0
    cost_basis_formula: str = ""

    @classmethod
    def compute(cls, token_count: int, complexity: float = 1.0,
                strategic_multiplier: float = 1.3) -> "JouleWorkCost":
        """
        JW cost formula: tokens/1000 * kappa(1.0) * complexity * strategic
        Mirrors ZHC formula: User Price = Worst-case cost * 1.2-1.5 * strategic
        """
        estimated_joules = (token_count / 1000) * 1.0
        jw_cost = int(estimated_joules * 1.0 * complexity * strategic_multiplier)
        return cls(
            estimated_cost_jw=jw_cost,
            cost_basis_formula=f"tokens({token_count}) x kappa(1.0) x complexity({complexity}) x strategic({strategic_multiplier})"
        )


@dataclass
class OPAReceipt:
    """Receipt of OPA policy decision - attached to every authorized tool call."""
    policy_version: str = "nexus-authz-v0.2"
    decision: str = "allow"
    decision_timestamp: Optional[str] = None
    deny_reason: Optional[str] = None

    def __post_init__(self):
        if self.decision_timestamp is None:
            self.decision_timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class CAELEnvelope:
    """
    The complete NEXUS CAEL envelope. Transport-agnostic: travels over
    HTTP, SSE, WebSocket, NATS, Kafka, or gRPC. Protocol bridges
    (MCP, A2A, OpenAI, REST) consume the fields they support and
    ignore the rest - NEXUS gateway preserves all for audit.
    """
    sender: CAELSender
    recipient_did: str
    performative: Performative
    goal: str

    # Auto-generated on construction
    spec_version: str = "cael/0.2"
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex}")
    thread_id: str = field(default_factory=lambda: f"thr_{uuid.uuid4().hex}")
    task_id: str = field(default_factory=lambda: f"tsk_{uuid.uuid4().hex}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    parent_message_id: Optional[str] = None
    intent: Optional[str] = None
    priority: str = "normal"

    policy: CAELPolicy = field(default_factory=CAELPolicy)
    delegation: Optional[CAELDelegation] = None
    memory: CAELMemory = field(default_factory=CAELMemory)
    trace: CAELTrace = field(default_factory=CAELTrace)
    joulework: Optional[JouleWorkCost] = None
    opa_auth: Optional[OPAReceipt] = None

    # Protocol bridge hints
    mcp_tool_server: Optional[str] = None
    a2a_peer_url: Optional[str] = None

    # Set after signing
    signature: Optional[dict] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dict for transport or protocol bridge translation."""
        d = {
            "spec_version": self.spec_version,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "sender": asdict(self.sender),
            "recipient": {"agent_did": self.recipient_did},
            "performative": self.performative.value,
            "intent": self.intent,
            "priority": self.priority,
            "policy": asdict(self.policy),
            "memory": {
                "context_compartment": self.memory.context_compartment.value,
                "state_ref": self.memory.state_ref,
                "checkpoint_before_write": self.memory.checkpoint_before_write,
            },
            "trace": asdict(self.trace),
            "content": {"goal": self.goal},
        }
        if self.delegation:
            d["delegation"] = asdict(self.delegation)
        if self.joulework:
            d["joulework"] = asdict(self.joulework)
        if self.opa_auth:
            d["opa_auth"] = asdict(self.opa_auth)
        if self.parent_message_id:
            d["parent_message_id"] = self.parent_message_id
        if self.mcp_tool_server:
            d["protocol_bridges"] = {"mcp_tool_server": self.mcp_tool_server}
        if self.a2a_peer_url:
            d.setdefault("protocol_bridges", {})["a2a_peer"] = self.a2a_peer_url
        if self.signature:
            d["signature"] = self.signature
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def compute_content_hash(self) -> str:
        """SHA-256 over canonical JSON of signed fields (pre-signature)."""
        signed_payload = {
            k: v for k, v in self.to_dict().items()
            if k in {"message_id", "sender", "recipient", "performative",
                     "content", "policy", "timestamp", "delegation"}
        }
        canonical = json.dumps(signed_payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def sign(self, private_key_hex: Optional[str] = None) -> "CAELEnvelope":
        """
        Attach ML-DSA-65 signature (FIPS 204) over signed fields.
        PRODUCTION: Replace with actual ML-DSA-65 via liboqs or equivalent.
        TESTING: Uses SHA-256 over canonical JSON as a functional stub.
        The test suite verifies the signing contract; swap the crypto primitive
        without changing the interface.
        """
        self.content_hash = self.compute_content_hash()
        self.signature = {
            "algorithm": "ML-DSA-65",   # FIPS 204; Ed25519 as classical fallback
            "signed_fields": ["message_id", "sender", "recipient", "performative",
                               "content", "policy", "timestamp"],
            # PRODUCTION: value = mldsa65_sign(private_key, content_hash)
            # TESTING: SHA-256 stub - functional contract preserved
            "value": f"stub-{self.content_hash[:32]}",
            "signed_at": datetime.now(timezone.utc).isoformat(),
        }
        return self

    def verify_signature(self) -> bool:
        """
        Verify ML-DSA-65 signature.
        PRODUCTION: Replace stub with actual ML-DSA-65 verification.
        """
        if not self.signature:
            return False
        expected_hash = self.compute_content_hash()
        # TESTING: Verify the stub contract
        return self.signature.get("value", "").endswith(expected_hash[:32])

    def validate(self) -> list[str]:
        """
        Validate envelope against NEXUS structural requirements.
        Returns list of violations. Empty list = valid.
        """
        violations = []
        if not self.sender.agent_did:
            violations.append("sender.agent_did is required")
        if not self.sender.spiffe_id:
            violations.append("sender.spiffe_id is required (L1/L2 requirement)")
        if self.sender.spiffe_id and not self.sender.spiffe_id.startswith("spiffe://"):
            violations.append("sender.spiffe_id must be a valid SPIFFE URI (must start with spiffe://)")
        if not self.recipient_did:
            violations.append("recipient.agent_did is required")
        if self.delegation and self.delegation.delegation_depth > 4:
            violations.append("delegation_depth exceeds max (4); circuit breaker would fire")
        if not self.signature:
            violations.append("envelope is unsigned; ML-DSA-65 signature required before transmission")
        if self.memory.context_compartment == ContextCompartment.CREDENTIAL_SURFACE:
            # Credential surface should never be in a delegated message
            if self.delegation and self.delegation.delegation_depth > 0:
                violations.append("CREDENTIAL_SURFACE context cannot be in a delegated message")
        return violations


@dataclass
class CAELToolCall:
    """
    CAEL tool-call schema. Adds to standard tool-calling:
    idempotency keys, rollback hints, explicit provenance, JW cost,
    OPA authorization receipt. All fields missing from current standards.
    """
    tool_name: str
    arguments: dict
    requested_by_did: str
    context_compartment: ContextCompartment
    vcc_id: str
    delegation_depth: int = 0
    tool_version: Optional[str] = None
    mcp_server_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    execution_mode: str = "sync"
    max_retries: int = 3
    rollback_enabled: bool = False
    compensating_action: Optional[str] = None
    joulework: Optional[JouleWorkCost] = None
    opa_auth: Optional[OPAReceipt] = None

    tool_call_id: str = field(default_factory=lambda: f"tc_{uuid.uuid4().hex}")

    def __post_init__(self):
        if not self.idempotency_key:
            # Auto-generate idempotency key from tool + args + agent
            key_source = f"{self.requested_by_did}:{self.tool_name}:{json.dumps(self.arguments, sort_keys=True)}"
            self.idempotency_key = f"idem_{hashlib.sha256(key_source.encode()).hexdigest()[:24]}"

    def to_dict(self) -> dict:
        return {
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "mcp_server_url": self.mcp_server_url,
            "idempotency_key": self.idempotency_key,
            "arguments": self.arguments,
            "execution_mode": self.execution_mode,
            "retry_policy": {
                "max_retries": self.max_retries,
                "backoff": "exponential",
                "backoff_base_ms": 200,
            },
            "rollback_hint": {
                "enabled": self.rollback_enabled,
                "compensating_action": self.compensating_action,
            },
            "provenance": {
                "requested_by_did": self.requested_by_did,
                "delegation_depth": self.delegation_depth,
                "vcc_id": self.vcc_id,
                "context_compartment": self.context_compartment.value,
            },
            "joulework": asdict(self.joulework) if self.joulework else None,
            "opa_auth": asdict(self.opa_auth) if self.opa_auth else None,
        }
