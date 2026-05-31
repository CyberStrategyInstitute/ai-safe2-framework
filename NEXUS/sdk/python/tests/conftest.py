"""
conftest.py
Shared pytest fixtures for the NEXUS-A2A test suite.

Fixtures here are available to all tests without explicit import.
"""

import pytest

from nexus_sdk.cael import CAELEnvelope, CAELSender, Performative
from nexus_sdk.memory import MemoryVaccine, MemoryZone
from nexus_sdk.guardian import GuardianPolicy, NEXUSGuardianClient
from nexus_sdk.otel import InMemoryNORExporter
from nexus_sdk.agbom import AgBOMManager


# ---------------------------------------------------------------------------
# Identity fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_did() -> str:
    return "did:nexus:agent:test-agent-001"


@pytest.fixture
def spiffe_id() -> str:
    return "spiffe://nexus.local/agent/test-agent-001"


@pytest.fixture
def owner_did() -> str:
    return "did:nexus:person:test-owner"


@pytest.fixture
def sub_agent_did() -> str:
    return "did:nexus:agent:test-sub-agent-001"


@pytest.fixture
def sub_spiffe_id() -> str:
    return "spiffe://nexus.local/agent/test-sub-agent-001"


# ---------------------------------------------------------------------------
# CAEL fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def personal_sender(agent_did, spiffe_id) -> CAELSender:
    return CAELSender(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        jw_account="did:nexus:jw:test-account",
    )


@pytest.fixture
def basic_envelope(personal_sender, sub_agent_did) -> CAELEnvelope:
    env = CAELEnvelope(
        sender=personal_sender,
        recipient_did=sub_agent_did,
        performative=Performative.COMMAND,
        goal="Test goal",
    )
    env.sign()
    return env


# ---------------------------------------------------------------------------
# Security component fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def permissive_policy() -> GuardianPolicy:
    """Guardian policy with no restrictions -- for baseline tests."""
    return GuardianPolicy()


@pytest.fixture
def strict_policy() -> GuardianPolicy:
    """Guardian policy with path traversal and IMDS blocks active."""
    return GuardianPolicy(
        blocked_argument_patterns=["../", "../../", "169.254.169.254"],
        max_delegation_depth=1,
    )


@pytest.fixture
def inline_guardian(permissive_policy) -> NEXUSGuardianClient:
    return NEXUSGuardianClient(
        inline_policy=permissive_policy,
        fail_mode=NEXUSGuardianClient.FAIL_CLOSED,
    )


@pytest.fixture
def strict_guardian(strict_policy) -> NEXUSGuardianClient:
    return NEXUSGuardianClient(
        inline_policy=strict_policy,
        fail_mode=NEXUSGuardianClient.FAIL_CLOSED,
    )


@pytest.fixture
def memory_vaccine(agent_did) -> MemoryVaccine:
    return MemoryVaccine(
        agent_did=agent_did,
        purpose_declaration="test agent",
        use_stub_embeddings=True,
    )


@pytest.fixture
def nor_exporter() -> InMemoryNORExporter:
    return InMemoryNORExporter()


@pytest.fixture
def agbom_manager(agent_did) -> AgBOMManager:
    return AgBOMManager(agent_did)
