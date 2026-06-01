"""
examples/acs_bridge.py
NEXUS over ACS: connecting a NEXUS agent to an ACS-compatible Guardian.

What this example shows:
  - How NEXUS DID identity maps to ACS string agent.id (backward compatible)
  - Building AOS JSON-RPC 2.0 requests via NEXUSACSBridge
  - Parsing ACS Guardian verdicts into GuardianVerdictResult
  - Memory store request with NEXUS provenance in the nexus: extension block
  - ACS Guardians that do not implement the nexus: namespace simply ignore it

Implements: NEXUS-ACS Bridge Specification v0.1

Run:
  cd sdk/python
  PYTHONPATH=. python ../../examples/acs_bridge.py

Note: ACS Guardian calls are mocked. In production, replace mock_acs_guardian()
with HTTP calls to your Guardian endpoint at the configured guardian_url.
"""

import json
from nexus_sdk.bridges import NEXUSACSBridge
from nexus_sdk.memory import MemoryVaccine, MemoryZone
from nexus_sdk.cael import CAELToolCall

# ============================================================================
# Mock ACS Guardian (replaces real HTTP in this example)
# ============================================================================

def mock_acs_guardian(request: dict) -> dict:
    """
    Simulates an ACS-compatible Guardian endpoint.
    Denies calls to 'delete_file'. Ignores the nexus: extension block.
    """
    method_name = request.get("params", {}).get("action", {}).get("method", "")
    step_id = request.get("params", {}).get("stepId", "unknown")
    if "delete" in method_name.lower():
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "decision": "deny",
                "step_id": step_id,
                "deny_reason": "delete operations not permitted by ACS policy",
                "reason_codes": ["ACS_POLICY_DELETE_BLOCKED"],
            }
        }
    return {
        "jsonrpc": "2.0",
        "id": request["id"],
        "result": {"decision": "allow", "step_id": step_id}
    }


# ============================================================================
# STEP 1: Build the bridge
# ============================================================================

bridge = NEXUSACSBridge()

agent_did = "did:nexus:agent:data-processor-v2"
spiffe_id = "spiffe://nexus.local/agent/data-processor-v2"

print("NEXUS-ACS Bridge Demo")
print("=" * 60)
print(f"Agent DID:  {agent_did}")
print(f"SPIFFE ID:  {spiffe_id}")
print()

# ============================================================================
# STEP 2: Tool call requests
# ============================================================================

print("Tool call requests via ACS Guardian:")
print("-" * 60)

tool_calls = [
    ("read_file",   {"path": "/data/input.csv"},  "read operation"),
    ("write_file",  {"path": "/data/output.csv"}, "write operation"),
    ("delete_file", {"path": "/data/temp.csv"},   "delete (should be denied)"),
]

for tool_name, arguments, desc in tool_calls:
    # CAEL tool call dict: agent identity lives in provenance block
    cael_tc = {
        "tool_name": tool_name,
        "arguments": arguments,
        "tool_call_id": f"tc-{tool_name}",
        "provenance": {
            "requested_by_did": agent_did,
            "spiffe_id": spiffe_id,
            "delegation_depth": 0,
        },
    }

    request = bridge.build_tool_call_request(
        cael_tool_call=cael_tc,
        reasoning=f"Processing {desc}",
    )

    # Verify ACS protocol compliance
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "steps/toolCallRequest"

    acs_agent_id = request["params"]["agent"]["id"]       # bare string for ACS compat
    nexus_agent_did = request["params"]["agent"]["agent_did"]  # DID in NEXUS extension

    # nexus: block carries NEXUS-specific fields; ACS-only Guardian ignores it
    nexus_block = request["params"].get("nexus", {})

    response = mock_acs_guardian(request)
    verdict = bridge.parse_verdict(response)

    status = "OK " if verdict["allowed"] else "!!!"
    print(f"  [{status}] {tool_name}: {verdict["decision"].upper()}")
    print(f"        ACS agent.id      = '{acs_agent_id}'")
    print(f"        NEXUS agent_did   = '{nexus_agent_did}'")
    print(f"        nexus: block keys = {list(nexus_block.keys())}")
    if not verdict["allowed"]:
        print(f"        deny_reason       = {verdict.get("reasoning")}")
    print()

# ============================================================================
# STEP 3: Memory store with NEXUS provenance
# ============================================================================

print("Memory store request via ACS Guardian:")
print("-" * 60)

mv = MemoryVaccine(agent_did, "data processing pipeline", use_stub_embeddings=True)
write_decision = mv.validate_write(
    content="processed 1024 records from input.csv, 12 anomalies flagged",
    zone=MemoryZone.CROSS_SESSION,
    owner_did=agent_did,
)
acs_ctx = mv.to_acs_guardian_context(
    content="processed 1024 records from input.csv, 12 anomalies flagged",
    zone=MemoryZone.CROSS_SESSION,
    owner_did=agent_did,
    decision=write_decision,
)

memory_request = bridge.build_memory_store_request(
    content=["processed 1024 records from input.csv, 12 anomalies flagged"],
    agent_did=agent_did,
    provenance_dict=acs_ctx,
)

mem_response = mock_acs_guardian(memory_request)
mem_verdict = bridge.parse_verdict(mem_response)

print(f"  [OK ] memory store: {mem_verdict["decision"].upper()}")
print(f"        zone            = {acs_ctx['zone']}")
print(f"        drift_score     = {acs_ctx.get('drift_score', 'n/a')}")
print(f"        embedding_hash  = {acs_ctx['embedding_hash'][:32]}...")
print()

print("=" * 60)
print("Key properties demonstrated:")
print("  1. NEXUS DID identity is backward-compatible: agent.id = DID string")
print("  2. nexus: extension block is ignored by ACS-only Guardians")
print("  3. Memory writes carry cryptographic provenance through ACS wire format")
print("  4. Bridge produces standard AOS JSON-RPC 2.0 -- no ACS code changes needed")
print("  5. Deny parsing from ACS verdict produces GuardianVerdictResult correctly")
