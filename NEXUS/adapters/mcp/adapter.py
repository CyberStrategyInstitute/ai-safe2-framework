"""
NEXUS MCP Adapter - agent-to-tool plane enforcement.

STATUS: INTERFACE SKELETON. NOT PRODUCTION-READY. DO NOT DEPLOY.

One step is implemented and tested: authorize_tool_call, the NEXUS tool-call
authorization decision (authz.py, a mirror of opa/nexus-authz.rego ported back
from Agency Check). Every other enforcement method raises NotImplementedError
by design. An incomplete adapter must fail closed, not pass traffic. Do not
replace these with stubs that return success values.

Implements the CP.5.MCP profile for MCP 2026-07-28 (stateless core), with a
legacy adapter for 2025-11-25 during the twelve-month support window.

Reference: 00-cross-pillar/cp5_mcp_server_security.md
"""
from __future__ import annotations

import enum
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


def _load_authz():
    # This directory is not an installed package; load the sibling module either way.
    try:
        from . import authz  # type: ignore[import-not-found]
        return authz
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "nexus_mcp_adapter_authz", Path(__file__).with_name("authz.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # dataclasses resolve their module by name
        spec.loader.exec_module(module)
        return module


_authz = _load_authz()


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
    evidence: dict = field(default_factory=dict)


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

    def authorize_tool_call(self, principal: Principal, grant: CapabilityGrant, body: dict, *,
                            policy_data: Optional[Mapping[str, Any]],
                            mandate_required_tools: frozenset[str] = frozenset(),
                            parent_capabilities: Optional[frozenset[str]] = None,
                            context_compartment: str = "TASK_CONTEXT") -> AdapterResult:
        """NEXUS authorization for one `tools/call`, evaluated as opa/nexus-authz.rego does.

        `principal` must come from establish_trust (verified credential). `_meta`
        NEXUS context is caller-asserted and can only narrow: the delegation depth
        used is the larger of the verified chain and the declared depth.
        `context_compartment` is the compartment the deployment established for
        this call; it defaults to TASK_CONTEXT. A `_meta` compartment that differs
        from it is rejected, so a caller cannot select CREDENTIAL_SURFACE or
        AGENT_STATE to reach credential: tools. Mandates in `policy_data` must be
        bound to the principal, tool and expiry (AUTHZ-DIV-4).
        `policy_data` is the data.nexus subtree. A missing revocation snapshot is
        a HALT, never "not revoked".
        """
        revocation = (policy_data or {}).get("revocation")
        if not isinstance(revocation, Mapping) or not isinstance(revocation.get("agents"), Mapping):
            return AdapterResult(Decision.HALT, "revocation status unavailable")
        if not isinstance(body, Mapping) or body.get("method") != "tools/call":
            return AdapterResult(Decision.REJECT, "not a tools/call request")
        params = body.get("params")
        if not isinstance(params, Mapping) or not isinstance(params.get("name"), str):
            return AdapterResult(Decision.REJECT, "tools/call without a tool name")
        try:
            ctx = _authz.parse_nexus_context(params.get("_meta"))
        except _authz.NexusContextError as exc:
            return AdapterResult(Decision.REJECT, str(exc), findings=[f"malformed:{exc.field}"])

        if ctx.context_compartment != context_compartment:
            return AdapterResult(Decision.REJECT, "asserted context compartment differs from the established one",
                                 findings=["malformed:nexusContextCompartment"])

        granted = sorted(grant.tools)
        decision = _authz.authorize_tool_call({
            "agent_id": principal.id,
            "tool_name": params["name"],
            "vcc_capabilities": granted,
            "vcc_mandate_required": sorted(mandate_required_tools),
            "mandate_id": ctx.mandate_id,
            "delegation_depth": max(len(principal.delegation_chain), ctx.delegation_depth),
            "context_compartment": context_compartment,
            "requested_new_capabilities": list(ctx.requested_capabilities),
            "parent_vcc_capabilities": sorted(parent_capabilities if parent_capabilities is not None else grant.tools),
            "performative": "tool_call",
            "persistence_scope": "request",
        }, policy_data)
        if decision["allow"]:
            return AdapterResult(Decision.ALLOW, evidence=decision)
        return AdapterResult(Decision.REJECT, decision["deny_reason"], evidence=decision)

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
