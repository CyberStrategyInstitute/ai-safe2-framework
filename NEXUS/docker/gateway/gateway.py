"""
gateway.py
NEXUS Sovereign Gateway -- FastAPI application.

Wraps any upstream MCP server or ACS-compatible endpoint with:
  - CAEL envelope governance
  - Guardian policy enforcement (OPA sidecar or inline)
  - NOR fingerprinting and OTel export
  - JouleWork economic accounting
  - AgBOM dynamic component tracking

Configuration via environment variables (see docker/.env.example).

This is a reference implementation scaffold. Production hardening checklist:
  [ ] Replace stub SPIFFE attestation with real SPIRE agent socket
  [ ] Configure production OPA bundle with signed policies
  [ ] Enable mTLS termination at the gateway (not just internal)
  [ ] Set GUARDIAN_FAIL_MODE=FAIL_CLOSED (default, do not override)
  [ ] Configure UPSTREAM_MCP_URLS for your MCP server(s)
  [ ] Review and tune AISM invariant thresholds for your ACT tier profile
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from nexus_sdk.guardian import GuardianPolicy, NEXUSGuardianClient, build_tool_call_step
from nexus_sdk.otel import InMemoryNORExporter, build_tool_call_nor, nor_to_otel_attributes
from nexus_sdk.agbom import AgBOMManager
from nexus_sdk.memory import MemoryVaccine, MemoryZone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
NEXUS_VERSION = os.getenv("NEXUS_VERSION", "0.3.0")
NEXUS_TRUST_DOMAIN = os.getenv("NEXUS_TRUST_DOMAIN", "nexus.local")
OPA_URL = os.getenv("OPA_URL", "http://opa:8181")
GUARDIAN_FAIL_MODE = os.getenv("GUARDIAN_FAIL_MODE", "fail_closed")
UPSTREAM_MCP_URLS = [u.strip() for u in os.getenv("UPSTREAM_MCP_URLS", "").split(",") if u.strip()]

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("nexus.gateway")

# ---------------------------------------------------------------------------
# Gateway state (initialized at startup)
# ---------------------------------------------------------------------------

_guardian: NEXUSGuardianClient | None = None
_agbom: AgBOMManager | None = None
_nor_exporter: InMemoryNORExporter | None = None

GATEWAY_DID = f"did:nexus:gateway:{NEXUS_TRUST_DOMAIN}"
GATEWAY_SPIFFE = f"spiffe://{NEXUS_TRUST_DOMAIN}/nexus-gateway"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _guardian, _agbom, _nor_exporter

    log.info(f"NEXUS Gateway v{NEXUS_VERSION} starting -- trust_domain={NEXUS_TRUST_DOMAIN}")

    # Initialize Guardian (inline policy + OPA sidecar when available)
    policy = GuardianPolicy(
        max_delegation_depth=4,
        require_reasoning_for_act_tiers=[3, 4],
        blocked_argument_patterns=["../", "../../", "169.254.169.254"],
    )
    _guardian = NEXUSGuardianClient(
        guardian_url=OPA_URL,
        inline_policy=policy,
        fail_mode=GUARDIAN_FAIL_MODE,
    )
    log.info(f"Guardian initialized -- fail_mode={GUARDIAN_FAIL_MODE}, opa={OPA_URL}")

    # Initialize AgBOM
    _agbom = AgBOMManager(GATEWAY_DID)
    for url in UPSTREAM_MCP_URLS:
        _agbom.discover_mcp_server(
            server_name=url.split("/")[-1] or "mcp-server",
            server_url=url,
            version="unknown",
            signed=False,
        )
        log.info(f"AgBOM: registered upstream MCP server {url}")

    # Initialize NOR exporter
    _nor_exporter = InMemoryNORExporter()

    log.info(f"Gateway ready -- {len(UPSTREAM_MCP_URLS)} upstream MCP server(s) registered")
    yield

    log.info("Gateway shutting down")
    if _nor_exporter:
        denied = _nor_exporter.get_denied_actions()
        violations = _nor_exporter.get_policy_violations()
        log.info(f"Session audit: {len(denied)} denied actions, {len(violations)} policy violations")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NEXUS Sovereign Gateway",
    description="NEXUS-A2A sovereign gateway wrapping MCP/ACS endpoints",
    version=NEXUS_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)


@app.get("/health")
async def health():
    agbom_version = _agbom.current_version if _agbom else 0
    unsigned = len(_agbom.get_unsigned_components()) if _agbom else 0
    return {
        "status": "ok",
        "version": NEXUS_VERSION,
        "trust_domain": NEXUS_TRUST_DOMAIN,
        "guardian_fail_mode": GUARDIAN_FAIL_MODE,
        "agbom_version": agbom_version,
        "unsigned_components": unsigned,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/v1/tool-call")
async def evaluate_tool_call(request: Request):
    """
    Evaluate a tool call through the NEXUS Guardian.

    Request body:
      {
        "agent_did":    "did:nexus:agent:...",
        "spiffe_id":    "spiffe://nexus.local/...",
        "tool_name":    "read_file",
        "arguments":    {"path": "/tmp/data"},
        "act_tier":     2,
        "reasoning":    "optional reasoning chain"
      }

    Returns:
      {
        "decision":     "allow" | "deny",
        "reasoning":    "...",
        "nor_receipt":  {"receipt_id": "...", "ocsf_class_uid": 6002, ...}
      }
    """
    body = await request.json()

    agent_did = body.get("agent_did", "")
    spiffe_id = body.get("spiffe_id", "")
    tool_name = body.get("tool_name", "")
    arguments = body.get("arguments", {})
    act_tier = body.get("act_tier", 1)
    reasoning = body.get("reasoning")

    if not all([agent_did, tool_name]):
        raise HTTPException(status_code=400, detail="agent_did and tool_name are required")

    step = build_tool_call_step(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        tool_name=tool_name,
        tool_arguments=arguments,
        act_tier=act_tier,
        reasoning=reasoning,
    )

    verdict = _guardian.evaluate(step)

    nor = build_tool_call_nor(
        agent_did=agent_did,
        spiffe_id=spiffe_id,
        tool_name=tool_name,
        outcome=verdict.decision,
        guardian_step_id=str(step.step_id),
        guardian_nor_fingerprint=verdict.nor_fingerprint,
    )
    _nor_exporter.export(nor)
    attrs = nor_to_otel_attributes(nor)

    log.info(
        f"tool_call: agent={agent_did[:30]} tool={tool_name} "
        f"decision={verdict.decision} ocsf={attrs.get('ocsf.class_uid')}"
    )

    return {
        "decision": verdict.decision,
        "reasoning": verdict.reasoning,
        "nor_receipt": {
            "receipt_id": nor.receipt_id,
            "receipt_hash": nor.receipt_hash,
            "ocsf_class_uid": attrs.get("ocsf.class_uid"),
            "ocsf_severity_id": attrs.get("ocsf.severity_id"),
            "timestamp": nor.timestamp,
        }
    }


@app.get("/v1/agbom")
async def get_agbom():
    """Return current AgBOM state for supply chain visibility."""
    if not _agbom:
        raise HTTPException(status_code=503, detail="AgBOM not initialized")
    chain_ok, violations = _agbom.verify_chain_integrity()
    return {
        **_agbom.to_dict(),
        "chain_integrity_ok": chain_ok,
        "chain_violations": violations,
    }


@app.get("/v1/audit")
async def get_audit_summary():
    """Return session audit summary from NOR exporter."""
    if not _nor_exporter:
        raise HTTPException(status_code=503, detail="NOR exporter not initialized")
    denied = _nor_exporter.get_denied_actions()
    violations = _nor_exporter.get_policy_violations()
    return {
        "denied_actions": len(denied),
        "policy_violations": len(violations),
        "note": "Full NOR traces available via OTel Collector at the configured SIEM endpoint.",
    }


if __name__ == "__main__":
    uvicorn.run("gateway:app", host="0.0.0.0", port=8080, log_level=LOG_LEVEL.lower())
