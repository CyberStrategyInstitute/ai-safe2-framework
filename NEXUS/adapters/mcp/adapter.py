"""
NEXUS MCP Adapter - agent-to-tool plane enforcement.

STATUS: INTERFACE SKELETON. NOT IMPLEMENTED. NOT TESTED. DO NOT DEPLOY.

Every enforcement method raises NotImplementedError by design. An incomplete
adapter must fail closed, not pass traffic. Do not replace these with stubs that
return success values.

Implements the CP.5.MCP profile for MCP 2026-07-28 (stateless core), with a
legacy adapter for 2025-11-25 during the twelve-month support window.

Reference: 00-cross-pillar/cp5_mcp_server_security.md
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class SpecVersion(str, enum.Enum):
    CURRENT = "2026-07-28"
    LEGACY = "2025-11-25"


class AttestationStrength(str, enum.Enum):
    """AIM v0.3 attestationMethod.strength. Capability-normative, not product-normative."""
    BEARER = "bearer"
    WORKLOAD_ATTESTED = "workload-attested"
    NON_REPUDIABLE = "non-repudiable"


class Decision(str, enum.Enum):
    ALLOW = "allow"
    REJECT = "reject"
    HALT = "halt"


@dataclass(frozen=True)
class Principal:
    id: str
    attestation: AttestationStrength
    claimed_client: Optional[str] = None
    delegation_chain: tuple[str, ...] = ()


@dataclass
class CapabilityGrant:
    tools: frozenset[str] = frozenset()
    extensions: frozenset[str] = frozenset()
    catalog_ttl_cap_ms: int = 900_000
    provenance_baseline: Optional[str] = None


@dataclass
class EconomicCeiling:
    max_tokens: int
    max_spend_minor_units: int
    currency: str = "USD"
    fail_closed: bool = True


@dataclass
class AdapterResult:
    decision: Decision
    reason: str = ""
    findings: list[str] = field(default_factory=list)


class MCPAdapter:
    """In-path enforcement contract for the agent-to-tool plane."""

    def __init__(self, spec_version: SpecVersion = SpecVersion.CURRENT) -> None:
        self.spec_version = spec_version

    def establish_trust(self, credential: Any, act_tier: str) -> Principal:
        raise NotImplementedError("establish_trust: fail closed until implemented")

    def verify_header_body_agreement(self, mcp_method: str, mcp_name: Optional[str], body: dict) -> AdapterResult:
        raise NotImplementedError("verify_header_body_agreement: fail closed until implemented")

    def check_capability(self, principal: Principal, grant: CapabilityGrant, body: dict) -> AdapterResult:
        raise NotImplementedError("check_capability: fail closed until implemented")

    def validate_state_handle(self, principal: Principal, handle: str) -> AdapterResult:
        raise NotImplementedError("validate_state_handle: fail closed until implemented")

    def validate_mrtr_responses(self, principal: Principal, origin_request: dict, input_responses: Any) -> AdapterResult:
        raise NotImplementedError("validate_mrtr_responses: fail closed until implemented")

    def check_economic_ceiling(self, principal: Principal, ceiling: EconomicCeiling) -> AdapterResult:
        raise NotImplementedError("check_economic_ceiling: fail closed until implemented")

    def sanitize_return_path(self, principal: Principal, result: Any) -> Any:
        raise NotImplementedError("sanitize_return_path: fail closed until implemented")

    def clamp_catalog_cache(self, declared_ttl_ms: int, grant: CapabilityGrant) -> int:
        raise NotImplementedError("clamp_catalog_cache: fail closed until implemented")

    def diff_provenance(self, grant: CapabilityGrant, catalog: Any) -> AdapterResult:
        raise NotImplementedError("diff_provenance: fail closed until implemented")

    def mint_state_handle(self, principal: Principal) -> str:
        raise NotImplementedError("mint_state_handle: fail closed until implemented")

    def record(self, principal: Principal, event: dict) -> None:
        raise NotImplementedError("record: fail closed until implemented")


class LegacyMCPAdapter(MCPAdapter):
    """2025-11-25 compatibility adapter for the twelve-month migration window."""

    def __init__(self) -> None:
        super().__init__(spec_version=SpecVersion.LEGACY)
