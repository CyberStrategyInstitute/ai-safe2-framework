"""
AI SAFE2 MCP Server — Main Application
Dual-transport: stdio (local, security-verified) or streamable-http (HTTPS via Caddy, bearer auth).

Security fixes applied (v3.0.1):
  RISK-0: _get_tier() now reads from ContextVar (context.py) — fixes broken
          _current_request = None pattern that silently downgraded all HTTP Pro
          users to free tier.
  RISK-1: All tool return values pass through sanitize_output() before being
          returned to LLM clients. Defends against supply-chain injection via
          poisoned control data.
  RISK-2: verify_stdio_security() runs at STDIO startup — source integrity hash
          + command/path allowlist + install path verification.
  RISK-3: Per-tier token bucket rate limiting applied in BearerAuthMiddleware.
          Rate limit headers (X-RateLimit-*) attached to all responses.

Usage:
  stdio (local):        MCP_TRANSPORT=stdio python -m mcp_server.app
  HTTP (behind Caddy):  MCP_TRANSPORT=streamable-http python -m mcp_server.app
"""
from __future__ import annotations

import sys

import structlog
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp_server.auth import BearerAuthMiddleware, verify_stdio_security
from mcp_server.config import (
    HOST,
    LOG_FORMAT,
    LOG_LEVEL,
    PORT,
    SERVER_DESCRIPTION,
    SERVER_NAME,
    SERVER_VERSION,
    TRANSPORT,
)
from mcp_server.context import get_tier
from mcp_server.controls_db import get_db
from mcp_server.prompts.registry import get_prompt, list_prompts
from mcp_server.resources.registry import get_resource, list_resources
from mcp_server.sanitize import sanitize_output
from mcp_server.tools.classify_agent import classify_agent
from mcp_server.tools.code_review import review_code
from mcp_server.tools.compliance_mapping import map_to_frameworks
from mcp_server.tools.control_lookup import control_lookup
from mcp_server.tools.risk_scoring import calculate_risk_score

# ── Logging ───────────────────────────────────────────────────────────────────
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(__import__("logging"), LOG_LEVEL, 20)
    ),
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        (
            structlog.processors.JSONRenderer()
            if LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer()
        ),
    ],
)
log = structlog.get_logger()

# ── MCP Server ────────────────────────────────────────────────────────────────
mcp = FastMCP(f"{SERVER_NAME} v{SERVER_VERSION}")

# ── Tier resolution (RISK-0 FIX) ─────────────────────────────────────────────
# Reads from ContextVar set by BearerAuthMiddleware.
# Replaces the broken `_current_request: Request | None = None` global that
# caused all HTTP-transport tool calls to silently fall back to "free" tier.

def _get_tier() -> str:
    return get_tier()


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Search and retrieve AI SAFE2 v3.0 controls by keyword, pillar, priority, "
        "compliance framework, ACT tier, or exact control ID. "
        "Free tier: 30 controls max. Pro tier: 500 controls max, all 32 frameworks. "
        "Example IDs: 'S1.5', 'CP.10', 'F3.2', 'P1.T1.10'."
    )
)
def lookup_control(
    query: str = "",
    control_id: str = "",
    pillar: str = "",
    priority: str = "",
    framework: str = "",
    version_added: str = "",
    act_tier: str = "",
    include_cross_pillar: bool = True,
) -> dict:
    """Look up AI SAFE2 v3.0 controls."""
    tier = _get_tier()
    log.info("tool.lookup_control", query=query, control_id=control_id, tier=tier)
    result = control_lookup(
        query=query, control_id=control_id, pillar=pillar, priority=priority,
        framework=framework, version_added=version_added, act_tier=act_tier,
        include_cross_pillar=include_cross_pillar, tier=tier,
    )
    return sanitize_output(result, "lookup_control")  # RISK-1 FIX


@mcp.tool(
    description=(
        "Calculate the AI SAFE2 v3.0 Combined Risk Score: "
        "CVSS_Base + ((100 - Pillar_Score) / 10) + (AAF / 10). "
        "Free tier: basic formula (no AAF). "
        "Pro tier: full formula with OWASP AIVSS v0.8 Agentic Amplification Factor. "
        "AAF factors: autonomy_level, tool_access_breadth, natural_language_reliance, "
        "context_persistence, behavioral_determinism, decision_opacity, state_retention, "
        "dynamic_identity, multi_agent_interactions, self_modification. "
        "Each factor: 0=architecturally prevented, 5=governed, 10=uncontrolled."
    )
)
def risk_score(
    cvss_base: float,
    pillar_score: float,
    aaf_factors: dict | None = None,
) -> dict:
    """Calculate AI SAFE2 v3.0 Combined Risk Score."""
    tier = _get_tier()
    log.info("tool.risk_score", cvss_base=cvss_base, pillar_score=pillar_score, tier=tier)
    result = calculate_risk_score(
        cvss_base=cvss_base, pillar_score=pillar_score,
        aaf_factors=aaf_factors, tier=tier,
    )
    return sanitize_output(result, "risk_score")  # RISK-1 FIX


@mcp.tool(
    description=(
        "Map a compliance requirement to AI SAFE2 v3.0 controls across up to 32 frameworks. "
        "Free tier: 5 frameworks (NIST AI RMF, ISO 42001, SOC 2, GDPR, OWASP LLM). "
        "Pro tier: all 32 frameworks. "
        "Example requirements: 'EU AI Act Article 14', 'SOC 2 CC.7.4', "
        "'prompt injection defense', 'human oversight autonomous AI'."
    )
)
def compliance_map(
    requirement: str,
    framework_ids: list | None = None,
) -> dict:
    """Map a compliance requirement to AI SAFE2 v3.0 controls."""
    tier = _get_tier()
    log.info("tool.compliance_map", requirement=requirement, tier=tier)
    result = map_to_frameworks(
        requirement=requirement, framework_ids=framework_ids, tier=tier
    )
    return sanitize_output(result, "compliance_map")  # RISK-1 FIX


@mcp.tool(
    description=(
        "Review code against AI SAFE2 v3.0 security controls. Light version: "
        "provides control taxonomy context and structured findings template for model-based analysis. "
        "No code is executed on the server. "
        "Pro tier only. Returns review_controls context, findings_template, and instructions."
    )
)
def code_review(
    code: str,
    language: str = "python",
    context: str = "",
    focus_pillar: str = "",
) -> dict:
    """Review code against AI SAFE2 v3.0 controls."""
    tier = _get_tier()
    log.info("tool.code_review", language=language, code_len=len(code), tier=tier)
    result = review_code(code=code, language=language, context=context,
                         focus_pillar=focus_pillar, tier=tier)
    # RISK-1 FIX: Highest-priority sanitization target.
    # code_review directly injects control descriptions as LLM reasoning context.
    return sanitize_output(result, "code_review")


@mcp.tool(
    description=(
        "Classify an AI agent by ACT Capability Tier (1-4) and return mandatory controls, "
        "HEAR designation requirements, CP.9 replication governance needs, "
        "and deployment governance evidence package. "
        "Free tier: ACT-1/ACT-2 only. Pro tier: full ACT-1 through ACT-4 with complete requirements."
    )
)
def agent_classify(
    description: str,
    human_review_required: bool = True,
    spawns_sub_agents: bool = False,
    has_persistent_memory: bool = False,
    tool_access: list | None = None,
    operates_unattended: bool = False,
    deployment_environment: str = "",
) -> dict:
    """Classify an AI agent by ACT tier and return governance requirements."""
    tier = _get_tier()
    log.info("tool.agent_classify", spawns_agents=spawns_sub_agents, tier=tier)
    result = classify_agent(
        description=description, human_review_required=human_review_required,
        spawns_sub_agents=spawns_sub_agents, has_persistent_memory=has_persistent_memory,
        tool_access=tool_access, operates_unattended=operates_unattended,
        deployment_environment=deployment_environment, tier=tier,
    )
    return sanitize_output(result, "agent_classify")  # RISK-1 FIX


@mcp.tool(
    description=(
        "Retrieve an AI SAFE2 v3.0 governance resource: policy templates, audit schemas, "
        "HEAR designation forms, quick-start checklists, and reference documents. "
        "Free resources: quick_start_checklist, pillar_overview, act_tier_reference. "
        "Pro resources: governance_policy_template, audit_scorecard_schema, hear_designation_template."
    )
)
def get_governance_resource(resource_name: str = "") -> dict:
    """Retrieve a governance resource or list available resources."""
    tier = _get_tier()
    log.info("tool.get_governance_resource", resource_name=resource_name, tier=tier)
    if not resource_name:
        result = list_resources(tier=tier)
    else:
        result = get_resource(resource_name=resource_name, tier=tier)
    return sanitize_output(result, "get_governance_resource")  # RISK-1 FIX


@mcp.tool(
    description=(
        "Get a reusable AI SAFE2 v3.0 workflow prompt. Available prompts: "
        "security_architecture_review, compliance_gap_analysis, "
        "incident_response_runbook, agent_deployment_checklist. "
        "Leave prompt_name empty to list all available prompts."
    )
)
def get_workflow_prompt(
    prompt_name: str = "",
    arguments: dict | None = None,
) -> dict:
    """Retrieve a reusable AI SAFE2 workflow prompt."""
    log.info("tool.get_workflow_prompt", prompt_name=prompt_name)
    if not prompt_name:
        result = list_prompts()
    else:
        result = get_prompt(prompt_name=prompt_name, arguments=arguments)
    return sanitize_output(result, "get_workflow_prompt")  # RISK-1 FIX


# ── MCP Resources ─────────────────────────────────────────────────────────────

@mcp.resource("aisafe2://controls/summary")
def controls_summary() -> str:
    """AI SAFE2 v3.0 control count and framework summary."""
    db = get_db()
    counts = db.count()
    return (
        f"AI SAFE2 v3.0 Controls Summary\n"
        f"Total: {counts['total']} controls\n"
        f"Pillar controls: {counts['pillar_controls']}\n"
        f"Cross-pillar governance controls: {counts['cross_pillar_controls']}\n"
        f"Compliance frameworks mapped: {counts['frameworks']}\n"
        f"First-in-field: CP.9 Agent Replication Governance, CP.10 HEAR Doctrine, CP.7 Active Defense\n"
    )


@mcp.resource("aisafe2://risk-formula")
def risk_formula() -> str:
    """AI SAFE2 v3.0 risk scoring formula."""
    db = get_db()
    f = db.risk_formula
    return (
        f"AI SAFE2 v3.0 Combined Risk Score Formula\n"
        f"Formula: {f['formula']}\n\n"
        f"Components:\n"
        + "\n".join(f"  {k}: {v}" for k, v in f["components"].items())
        + f"\n\nAAF Factors ({len(f['aaf_factors'])} total):\n"
        + "\n".join(f"  {factor}" for factor in f["aaf_factors"])
        + f"\n\nAAF Values:\n"
        + "\n".join(f"  {k}: {v}" for k, v in f["aaf_values"].items())
    )


# ── MCP Prompts ───────────────────────────────────────────────────────────────

@mcp.prompt()
def architecture_review(system_description: str, environment: str = "cloud") -> str:
    """Start a comprehensive AI SAFE2 v3.0 security architecture review."""
    result = get_prompt(
        "security_architecture_review",
        {"system_description": system_description, "deployment_environment": environment,
         "compliance_requirements": "not specified"},
    )
    return result.get("rendered_prompt", "")


@mcp.prompt()
def deployment_checklist(agent_name: str, act_tier: str) -> str:
    """Generate a deployment readiness checklist for an agent."""
    result = get_prompt(
        "agent_deployment_checklist",
        {"agent_name": agent_name, "act_tier": act_tier, "deployment_date": "TBD"},
    )
    return result.get("rendered_prompt", "")


# ── Health endpoint ───────────────────────────────────────────────────────────

async def health_check(request: Request) -> JSONResponse:
    db = get_db()
    counts = db.count()
    return JSONResponse({
        "status": "healthy",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "transport": TRANSPORT,
        "controls_loaded": counts["total"],
        "frameworks": counts["frameworks"],
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    db = get_db()  # preload and validate controls JSON at startup
    log.info(
        "server.start",
        name=SERVER_NAME,
        version=SERVER_VERSION,
        DESCRIPTION=SERVER_DESCRIPTION,
        transport=TRANSPORT,
        controls=db.count()["total"],
    )

    if TRANSPORT == "stdio":
        # RISK-2 FIX: run security checks before accepting any requests.
        # Verifies command allowlist + install path + source integrity hash.
        # sys.exit(1) on any failure (fail-closed).
        verify_stdio_security()
        log.info("transport.stdio", note="Local mode — security verified, no network exposure")
        mcp.run(transport="stdio")

    elif TRANSPORT == "streamable-http":
        import uvicorn

        mcp_app = mcp.streamable_http_app()

        app = Starlette(
            routes=[
                Route("/health", health_check),
                Route("/mcp", mcp_app),
                Route("/mcp/{path:path}", mcp_app),
            ]
        )
        # BearerAuthMiddleware handles: auth + ContextVar tier (RISK-0) + rate limiting (RISK-3)
        app.add_middleware(BearerAuthMiddleware)

        log.info(
            "transport.http",
            host=HOST,
            port=PORT,
            note=(
                "Binding to localhost only. If not review your deployment infrastructure requirements."
                "Caddy handles TLS termination on the public HTTPS port. "
                "Do NOT expose this port directly."
            ),
        )
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL.lower(),
            access_log=True,
        )

    else:
        log.error("transport.unknown", transport=TRANSPORT)
        sys.exit(1)


if __name__ == "__main__":
    main()
