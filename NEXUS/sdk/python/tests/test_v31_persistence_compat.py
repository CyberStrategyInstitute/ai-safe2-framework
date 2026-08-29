"""AI SAFE2 v3.1 persistence-scope compatibility tests for NEXUS v0.3."""
from __future__ import annotations

from nexus_sdk.memory import MemoryVaccine, MemoryZone, MemoryWriteResult


AGENT_DID = "did:web:nexus.local:agents:v31-test"


def _vaccine() -> MemoryVaccine:
    return MemoryVaccine(
        agent_did=AGENT_DID,
        purpose_declaration="Governed v3.1 persistence compatibility test",
        use_stub_embeddings=True,
    )


def test_canonical_persistence_values() -> None:
    assert MemoryZone.REQUEST.value == "request"
    assert MemoryZone.HANDLE_SCOPED.value == "handle_scoped"
    assert MemoryZone.DURABLE.value == "durable"
    assert MemoryZone.SWARM_SHARED.value == "swarm_shared"


def test_source_compatible_enum_aliases() -> None:
    assert MemoryZone.SESSION is MemoryZone.REQUEST
    assert MemoryZone.CROSS_SESSION is MemoryZone.HANDLE_SCOPED
    assert MemoryZone.PERMANENT is MemoryZone.DURABLE


def test_legacy_serialized_values_are_accepted() -> None:
    assert MemoryZone("SESSION_MEMORY") is MemoryZone.REQUEST
    assert MemoryZone("CROSS_SESSION_MEMORY") is MemoryZone.HANDLE_SCOPED
    assert MemoryZone("PERMANENT_MEMORY") is MemoryZone.DURABLE
    assert MemoryZone("SWARM_SHARED_MEMORY") is MemoryZone.SWARM_SHARED


def test_handle_scoped_write_emits_canonical_scope() -> None:
    vaccine = _vaccine()
    decision, context = vaccine.validate_write_with_guardian(
        content="normal governed state",
        zone=MemoryZone.HANDLE_SCOPED,
        owner_did=AGENT_DID,
    )
    assert decision.allowed is True
    assert decision.result == MemoryWriteResult.ALLOWED
    assert context["persistence_scope"] == "handle_scoped"
    assert context["state_handle_id"] == context["session_id"]


def test_durable_write_requires_mandate() -> None:
    vaccine = _vaccine()
    decision = vaccine.validate_write(
        content="durable governed state",
        zone=MemoryZone.DURABLE,
        owner_did=AGENT_DID,
    )
    assert decision.allowed is False
    assert decision.result == MemoryWriteResult.BLOCKED_NO_MANDATE


def test_durable_write_with_mandate_is_allowed() -> None:
    vaccine = _vaccine()
    decision = vaccine.validate_write(
        content="durable governed state",
        zone=MemoryZone.DURABLE,
        owner_did=AGENT_DID,
        mandate_id="mandate-v31-test",
    )
    assert decision.allowed is True
    assert decision.provenance is not None
    assert decision.provenance.state_handle_id == decision.provenance.session_id


def test_checkpoint_has_canonical_and_legacy_identifiers() -> None:
    checkpoint = _vaccine().create_checkpoint()
    assert checkpoint["state_handle_id"]
    assert checkpoint["session_id"] == checkpoint["state_handle_id"]
