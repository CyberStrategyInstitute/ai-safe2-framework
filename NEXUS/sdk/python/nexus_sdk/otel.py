"""
nexus_sdk/otel.py
NEXUS OpenTelemetry-Native NOR Export v0.3

Translates NEXUS Output Receipts (NOR) to OpenTelemetry span attributes with
OCSF (Open Cybersecurity Schema Framework) event mappings. Contributes NOR
fields as OTel semantic conventions so enterprise SIEM infrastructure (Splunk,
Elastic, Datadog) receives NEXUS audit trails through existing pipelines with
zero custom integration work.

This closes the gap ACS analysis identified: NOR is cryptographically superior
to ACS's OpenTelemetry traces but requires custom SIEM integration. This module
removes that barrier without degrading NOR's non-repudiation properties.

Design:
    NEXUS NOR = cryptographic audit chain (non-repudiation, PQC-ready)
    OTel export = operational observability (SIEM-native, no custom pipeline)
    Together    = forensic-grade audit WITH operational visibility

PRODUCTION:
    pip install opentelemetry-sdk opentelemetry-exporter-otlp
    Configure OTEL_EXPORTER_OTLP_ENDPOINT for your SIEM collector.

TESTING:
    InMemoryNORExporter captures spans for test assertions.
    No OTel SDK required in test mode.

Reference: OpenTelemetry Semantic Conventions v1.24, OCSF v1.0, NEXUS-A2A v0.3
AI SAFE2 v3.0: A2.5, A2.6, CP.10 (HEAR audit requirement)
"""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ── OCSF Event Classes ────────────────────────────────────────────────────────

class OCSFEventClass(int, Enum):
    """
    OCSF v1.0 event class IDs for NEXUS agent security events.
    These map NOR events to the SIEM taxonomy that enterprise SOC teams use.
    """
    AUTHENTICATION_ACTIVITY = 3002   # Agent identity assertion, enrollment
    AUTHORIZATION_ACTIVITY  = 3003   # Tool call allow/deny/modify verdicts
    DATA_ACTIVITY           = 4003   # Memory read/write operations
    API_ACTIVITY            = 6003   # Tool invocations, MCP calls
    DETECTION_FINDING       = 2004   # Memory poisoning, drift detection alerts
    INCIDENT_FINDING        = 2005   # Kill switch activations, swarm anomalies
    POLICY_VIOLATION        = 6002   # Scope overflow, delegation violations


# ── NOR Record ────────────────────────────────────────────────────────────────

@dataclass
class NEXUSOutputReceipt:
    """
    NEXUS Output Receipt (NOR): cryptographic audit record for every agent action.

    Every allowed NEXUS tool call, memory write, and delegation event generates
    a NOR. The NOR chain provides non-repudiation at the protocol level - not
    as an application feature that can be disabled.

    Fields:
        receipt_id:         Unique identifier for this NOR
        agent_did:          DID of the agent that performed the action
        spiffe_id:          SPIFFE workload identity (process-level binding)
        action_type:        What was done (tool_call, memory_write, delegate, etc.)
        action_detail:      Tool name, memory zone, performative, etc.
        outcome:            allow|deny|modify
        guardian_verdict:   Guardian step_id and nor_fingerprint if evaluated
        delegation_depth:   Depth in delegation chain at time of action
        vcc_id:             VCC governing this action
        joulework_cost:     JW cost of this action
        reasoning_hash:     SHA-256 of agent reasoning chain (if provided)
        cael_envelope_hash: Hash of the originating CAEL envelope
        signature:          ML-DSA-65 stub (production: real PQC signature)
    """
    agent_did: str
    action_type: str
    action_detail: str
    outcome: str  # allow|deny|modify

    receipt_id: str = field(default_factory=lambda: f"nor_{uuid.uuid4().hex}")
    spiffe_id: Optional[str] = None
    guardian_step_id: Optional[str] = None
    guardian_nor_fingerprint: Optional[str] = None
    delegation_depth: int = 0
    vcc_id: Optional[str] = None
    joulework_cost: Optional[int] = None
    reasoning_hash: Optional[str] = None
    cael_envelope_hash: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Populated after signing
    signature: Optional[str] = None
    receipt_hash: Optional[str] = None

    def compute_receipt_hash(self) -> str:
        """Compute SHA-256 of canonical NOR payload (pre-signature)."""
        payload = {
            "receipt_id": self.receipt_id,
            "agent_did": self.agent_did,
            "action_type": self.action_type,
            "action_detail": self.action_detail,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
            "delegation_depth": self.delegation_depth,
            "vcc_id": self.vcc_id,
        }
        canonical = json.dumps(payload, sort_keys=True)
        self.receipt_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self.receipt_hash

    def sign(self) -> "NEXUSOutputReceipt":
        """
        Attach ML-DSA-65 signature over NOR payload.
        PRODUCTION: Replace stub with actual ML-DSA-65 via liboqs.
        TESTING: SHA-256 stub preserves signing contract.
        """
        self.compute_receipt_hash()
        # PRODUCTION: self.signature = mldsa65_sign(private_key, receipt_hash)
        self.signature = f"nor-stub-{self.receipt_hash[:32]}"
        return self

    def to_dict(self) -> dict:
        return {k: v for k, v in {
            "receipt_id": self.receipt_id,
            "agent_did": self.agent_did,
            "spiffe_id": self.spiffe_id,
            "action_type": self.action_type,
            "action_detail": self.action_detail,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
            "guardian_step_id": self.guardian_step_id,
            "guardian_nor_fingerprint": self.guardian_nor_fingerprint,
            "delegation_depth": self.delegation_depth,
            "vcc_id": self.vcc_id,
            "joulework_cost": self.joulework_cost,
            "reasoning_hash": self.reasoning_hash,
            "cael_envelope_hash": self.cael_envelope_hash,
            "session_id": self.session_id,
            "receipt_hash": self.receipt_hash,
            "signature": self.signature,
        }.items() if v is not None}


# ── OTel Attribute Mapping ─────────────────────────────────────────────────────

# NEXUS NOR -> OpenTelemetry span attribute names (semantic convention proposal)
# Prefix: nexus.nor.* (to be submitted as IETF/OTel upstream contribution)
NEXUS_NOR_OTEL_ATTRIBUTES = {
    "receipt_id":               "nexus.nor.receipt_id",
    "agent_did":                "nexus.nor.agent_did",
    "spiffe_id":                "nexus.nor.spiffe_id",
    "action_type":              "nexus.nor.action_type",
    "action_detail":            "nexus.nor.action_detail",
    "outcome":                  "nexus.nor.outcome",
    "guardian_step_id":         "nexus.nor.guardian.step_id",
    "guardian_nor_fingerprint": "nexus.nor.guardian.fingerprint",
    "delegation_depth":         "nexus.nor.delegation_depth",
    "vcc_id":                   "nexus.nor.vcc_id",
    "joulework_cost":           "nexus.nor.joulework_cost",
    "reasoning_hash":           "nexus.nor.reasoning_hash",
    "cael_envelope_hash":       "nexus.nor.cael_envelope_hash",
    "session_id":               "nexus.nor.session_id",
    "receipt_hash":             "nexus.nor.receipt_hash",
    # OCSF standard fields (compatible with existing SIEM semantic conventions)
    "ocsf_class_uid":           "ocsf.class_uid",
    "ocsf_activity_id":         "ocsf.activity_id",
    "ocsf_severity_id":         "ocsf.severity_id",
}

def nor_to_otel_attributes(nor: NEXUSOutputReceipt,
                            ocsf_class: Optional[OCSFEventClass] = None) -> dict[str, Any]:
    """
    Map NOR fields to OpenTelemetry span attributes.
    Adds OCSF event classification for SIEM integration.

    These attributes allow Splunk/Elastic/Datadog to:
      - Group by nexus.nor.agent_did (per-agent audit trail)
      - Alert on nexus.nor.outcome = deny (policy violations)
      - Dashboard nexus.nor.delegation_depth (trust chain depth)
      - Correlate nexus.nor.cael_envelope_hash (end-to-end message tracing)
    """
    attrs: dict[str, Any] = {}
    nor_dict = nor.to_dict()

    for field_name, otel_name in NEXUS_NOR_OTEL_ATTRIBUTES.items():
        if field_name in nor_dict:
            attrs[otel_name] = nor_dict[field_name]

    # OCSF event classification
    # deny outcome always maps to POLICY_VIOLATION regardless of action_type;
    # a denied tool_call is a policy enforcement event, not an API activity event.
    if ocsf_class:
        attrs["ocsf.class_uid"] = ocsf_class.value
    elif nor.outcome == "deny":
        attrs["ocsf.class_uid"] = OCSFEventClass.POLICY_VIOLATION.value
    elif nor.action_type == "tool_call":
        attrs["ocsf.class_uid"] = OCSFEventClass.API_ACTIVITY.value
    elif nor.action_type in ("memory_write", "memory_read"):
        attrs["ocsf.class_uid"] = OCSFEventClass.DATA_ACTIVITY.value
    elif nor.action_type == "identity_assertion":
        attrs["ocsf.class_uid"] = OCSFEventClass.AUTHENTICATION_ACTIVITY.value

    # OCSF severity mapping
    if nor.outcome == "allow":
        attrs["ocsf.severity_id"] = 1  # Informational
    elif nor.outcome == "modify":
        attrs["ocsf.severity_id"] = 2  # Low
    elif nor.outcome == "deny":
        attrs["ocsf.severity_id"] = 4  # High

    # OpenTelemetry standard span status
    attrs["span.status"] = "OK" if nor.outcome == "allow" else "ERROR"
    attrs["span.name"] = f"nexus.{nor.action_type}"

    return attrs


# ── In-Memory NOR Exporter (Test Mode) ────────────────────────────────────────

class InMemoryNORExporter:
    """
    In-memory NOR exporter for testing.
    Captures NOR records + OTel attribute translations without any OTel SDK.

    Usage in tests:
        exporter = InMemoryNORExporter()
        exporter.export(nor)
        assert len(exporter.spans) == 1
        assert exporter.spans[0]["nexus.nor.outcome"] == "allow"
    """

    def __init__(self):
        self.spans: list[dict] = []
        self.receipts: list[NEXUSOutputReceipt] = []

    def export(self, nor: NEXUSOutputReceipt,
               ocsf_class: Optional[OCSFEventClass] = None) -> dict:
        """Export a NOR as OTel span attributes. Returns the attribute dict."""
        nor.sign()
        attrs = nor_to_otel_attributes(nor, ocsf_class)
        self.spans.append(attrs)
        self.receipts.append(nor)
        return attrs

    def get_spans_for_agent(self, agent_did: str) -> list[dict]:
        return [s for s in self.spans if s.get("nexus.nor.agent_did") == agent_did]

    def get_denied_actions(self) -> list[dict]:
        return [s for s in self.spans if s.get("nexus.nor.outcome") == "deny"]

    def get_policy_violations(self) -> list[dict]:
        return [s for s in self.spans
                if s.get("ocsf.class_uid") == OCSFEventClass.POLICY_VIOLATION.value]

    def clear(self):
        self.spans.clear()
        self.receipts.clear()


# ── Production OTel Exporter ──────────────────────────────────────────────────

class NEXUSNORSpan:
    """
    Production OpenTelemetry span wrapper for NOR export.
    PRODUCTION: pip install opentelemetry-sdk opentelemetry-exporter-otlp
    TESTING:    Use InMemoryNORExporter.

    Each NOR becomes a child span of the originating CAEL envelope trace.
    The parent trace_id links all NOR events in a delegation chain together,
    enabling end-to-end forensic reconstruction of multi-agent workflows.
    """

    def __init__(self, service_name: str = "nexus-agent",
                 otlp_endpoint: Optional[str] = None):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self._tracer = None
        self._init_tracer()

    def _init_tracer(self):
        """Initialize OTel tracer with OTLP exporter if available."""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": self.service_name})
            provider = TracerProvider(resource=resource)

            if self.otlp_endpoint:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))

            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer("nexus.nor")
        except ImportError:
            self._tracer = None  # OTel SDK not installed; use InMemoryNORExporter

    def emit(self, nor: NEXUSOutputReceipt,
             parent_trace_id: Optional[str] = None,
             ocsf_class: Optional[OCSFEventClass] = None):
        """
        Emit NOR as an OTel span.
        PRODUCTION: spans flow to your SIEM via OTLP exporter.
        TESTING: no-op if OTel SDK not installed.
        """
        nor.sign()
        attrs = nor_to_otel_attributes(nor, ocsf_class)

        if self._tracer is None:
            return attrs  # Graceful no-op

        with self._tracer.start_as_current_span(
            name=f"nexus.{nor.action_type}",
            attributes=attrs,
        ) as span:
            if nor.outcome == "deny":
                from opentelemetry.trace import StatusCode
                span.set_status(StatusCode.ERROR, "Action denied by Guardian")
        return attrs


# ── NOR Factory ───────────────────────────────────────────────────────────────

def build_tool_call_nor(
    agent_did: str,
    spiffe_id: Optional[str],
    tool_name: str,
    outcome: str,
    vcc_id: Optional[str] = None,
    delegation_depth: int = 0,
    guardian_step_id: Optional[str] = None,
    guardian_nor_fingerprint: Optional[str] = None,
    joulework_cost: Optional[int] = None,
    reasoning_hash: Optional[str] = None,
    cael_envelope_hash: Optional[str] = None,
    session_id: Optional[str] = None,
) -> NEXUSOutputReceipt:
    """
    Build a NOR for a tool call event. The primary NOR event type.

    Include guardian_step_id and guardian_nor_fingerprint when the tool call
    was evaluated by a Guardian - this links the NOR to the Guardian verdict
    for end-to-end forensic reconstruction.
    """
    return NEXUSOutputReceipt(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        action_type="tool_call",
        action_detail=tool_name,
        outcome=outcome,
        guardian_step_id=guardian_step_id,
        guardian_nor_fingerprint=guardian_nor_fingerprint,
        delegation_depth=delegation_depth,
        vcc_id=vcc_id,
        joulework_cost=joulework_cost,
        reasoning_hash=reasoning_hash,
        cael_envelope_hash=cael_envelope_hash,
        session_id=session_id,
    )


def build_memory_nor(
    agent_did: str,
    spiffe_id: Optional[str],
    zone: str,
    outcome: str,
    drift_score: Optional[float] = None,
    session_id: Optional[str] = None,
) -> NEXUSOutputReceipt:
    """Build a NOR for a memory operation event."""
    detail = f"memory_write:{zone}"
    if drift_score is not None:
        detail += f":drift={drift_score:.3f}"
    return NEXUSOutputReceipt(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        action_type="memory_write",
        action_detail=detail,
        outcome=outcome,
        session_id=session_id,
    )
