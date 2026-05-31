"""
examples/sovereign_gateway.py
NEXUS Sovereign Gateway: wrap any MCP server with cryptographic governance.

What this example shows:
  - CAEL envelope construction around an MCP tool call
  - Guardian policy enforcement (inline, no external server needed)
  - NOR fingerprint generation and OTel export
  - AgBOM discovery on MCP server connection
  - FAIL_CLOSED vs FAIL_OPEN behavior

Run:
  cd sdk/python
  PYTHONPATH=. python ../../examples/sovereign_gateway.py

Expected output: three tool calls processed, two denied, NOR trace printed.
"""

import json
from nexus_sdk.cael import (
    CAELEnvelope, CAELSender, CAELPolicy, CAELDelegation,
    CAELToolCall, Performative, ContextCompartment, JouleWorkCost,
)
from nexus_sdk.guardian import (
    GuardianPolicy, NEXUSGuardianClient, build_tool_call_step,
)
from nexus_sdk.otel import (
    InMemoryNORExporter, build_tool_call_nor,
    OCSFEventClass, nor_to_otel_attributes,
)
from nexus_sdk.agbom import AgBOMManager

# ============================================================================
# STEP 1: Configure the sovereign gateway policy
# ============================================================================

policy = GuardianPolicy(
    revoked_dids=[],
    max_delegation_depth=2,
    require_reasoning_for_act_tiers=[3, 4],         # HEAR Doctrine for ACT-3/4
    blocked_argument_patterns=["../", "../../"],    # path traversal
)

guardian = NEXUSGuardianClient(
    inline_policy=policy,
    fail_mode=NEXUSGuardianClient.FAIL_CLOSED,
)

print(f"Gateway policy: FAIL_CLOSED, max_depth=2, HEAR Doctrine active for ACT-3/4")
print()

# ============================================================================
# STEP 2: Register MCP server in the AgBOM
# ============================================================================

agbom = AgBOMManager("did:nexus:agent:filesystem-agent-v1")
agbom.discover_mcp_server(
    server_name="filesystem-mcp",
    server_url="http://filesystem-mcp:3000",
    version="1.2.0",
    signed=False,                   # unsigned: supply chain risk flag
)

chain_ok, violations = agbom.verify_chain_integrity()
unsigned = agbom.get_unsigned_components()
print(f"AgBOM v{agbom.current_version}: {agbom.component_count} component(s) registered")
print(f"Unsigned components (supply chain risk): {len(unsigned)}")
print(f"Chain integrity: {'OK' if chain_ok else 'VIOLATED -- ' + str(violations)}")
print()

# ============================================================================
# STEP 3: Process tool calls through the sovereign gateway
# ============================================================================

exporter = InMemoryNORExporter()
agent_did = "did:nexus:agent:filesystem-agent-v1"
agent_spiffe = "spiffe://nexus.local/agent/filesystem-agent-v1"

tool_calls = [
    ("read_file",       {"path": "/tmp/report.txt"},        "legitimate read"),
    ("read_file",       {"path": "../../etc/passwd"},       "path traversal attempt"),
    ("get_credentials", {"service": "aws"},                 "credential tool (out of scope)"),
]

print("Processing tool calls through sovereign gateway:")
print("-" * 60)

for tool_name, args, desc in tool_calls:
    step = build_tool_call_step(
        agent_did=agent_did,
        spiffe_id=agent_spiffe,
        tool_name=tool_name,
        tool_arguments=args,
        act_tier=2,
        reasoning=f"Executing {desc}",
    )
    verdict = guardian.evaluate(step)

    # NOR built regardless of outcome -- denies are the most important audit records
    nor = build_tool_call_nor(
        agent_did=agent_did,
        spiffe_id=agent_spiffe,
        tool_name=tool_name,
        outcome=verdict.decision,
        guardian_step_id=str(step.step_id),
        guardian_nor_fingerprint=verdict.nor_fingerprint,
    )
    exporter.export(nor)

    attrs = nor_to_otel_attributes(nor)
    ocsf_class = attrs.get("ocsf.class_uid")
    severity = attrs.get("ocsf.severity_id")

    status = "OK " if verdict.allowed else "!!!"
    print(f"  [{status}] {tool_name}({json.dumps(args)[:45]})")
    print(f"        verdict:  {verdict.decision.upper()}")
    if not verdict.allowed:
        print(f"        reason:   {verdict.reasoning}")
    print(f"        OCSF:     class_uid={ocsf_class}, severity={severity}")
    print(f"        NOR:      {nor.receipt_id[:16]}...")
    print()

# ============================================================================
# STEP 4: Audit summary
# ============================================================================

print("=" * 60)
print("Audit Summary")
print("=" * 60)
all_spans = exporter.get_spans_for_agent(agent_did)
denied = exporter.get_denied_actions()
violations_ocsf = exporter.get_policy_violations()

print(f"Total NOR records:    {len(all_spans)}")
print(f"Denied actions:       {len(denied)}")
print(f"Policy violations:    {len(violations_ocsf)}")
print(f"  (OCSF 6002 -- POLICY_VIOLATION -- routed to SIEM in production)")
print()
print(f"AgBOM chain head:     {agbom.latest_version_hash[:32]}...")
print(f"AgBOM version:        {agbom.current_version}")
print()
print("In production: NOR spans flow via OTel Collector to SIEM.")
print("               OPA runs as isolated sidecar; agents cannot read policies.")
print("               Reference deployment: docker/docker-compose.yml")
