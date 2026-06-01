# nexus-authz.rego
# NEXUS L3 Core Authorization Policy
# Deploy: opa run --server --bundle ./opa/
# Query: POST http://localhost:8181/v1/data/nexus/authz/authorize_tool_call
#
# This policy runs OUTSIDE the agent process.
# The agent cannot read, modify, or override these decisions.
# Even a successfully prompt-injected agent cannot bypass OPA.
#
# Sub-millisecond target: p99 < 0.1ms (per Microsoft Agent Governance Toolkit benchmarks)
# OPA evaluates from a loaded in-memory data snapshot - no network call per decision.

package nexus.authz

import future.keywords.in

default allow = false
default mandate_required = false
default deny_reason = ""

# ── Primary allow rule ────────────────────────────────────────────────────────
# All conditions must be true simultaneously.
allow {
    has_valid_capability
    not is_mandate_required_op
    within_delegation_depth_limit
    not is_agent_revoked
    is_valid_context_compartment
    not is_scope_widening
}

# ── Mandate required (Class-H operations need HEAR signature) ─────────────────
mandate_required {
    input.tool_name in input.vcc_mandate_required
    not valid_mandate_exists
}

valid_mandate_exists {
    input.mandate_id != null
    input.mandate_id != ""
    data.nexus.mandates.active[input.mandate_id]
}

# ── Core condition rules ──────────────────────────────────────────────────────
has_valid_capability {
    input.tool_name in input.vcc_capabilities
}

is_mandate_required_op {
    input.tool_name in input.vcc_mandate_required
    not valid_mandate_exists
}

within_delegation_depth_limit {
    input.delegation_depth <= 4
}

is_agent_revoked {
    data.nexus.revocation.agents[input.agent_id].status == "revoked"
}

is_agent_revoked {
    data.nexus.revocation.agents[input.agent_id].status == "hard_brake"
}

is_valid_context_compartment {
    input.context_compartment in {"TASK_CONTEXT", "CREDENTIAL_SURFACE", "AGENT_STATE"}
}

# Scope widening: requested capabilities exceed parent capabilities
# This enforces the NEXUS monotonic scope narrowing invariant.
is_scope_widening {
    some cap in input.requested_new_capabilities
    not cap in input.parent_vcc_capabilities
}

# ── Context compartment enforcement ──────────────────────────────────────────
# Credential access is blocked from TASK_CONTEXT (L4 requirement)
deny {
    input.context_compartment == "TASK_CONTEXT"
    startswith(input.tool_name, "credential:")
    deny_reason := "TASK_CONTEXT cannot access credential: tools"
}

# AGENT_STATE writes require Memory Mandate
deny {
    input.performative == "memory_write"
    input.memory_zone in {"CROSS_SESSION_MEMORY", "PERMANENT_MEMORY"}
    not valid_mandate_exists
    deny_reason := "Cross-session and permanent memory writes require a Memory Mandate"
}

# CONFIG_CHANGE requires out-of-band approval for ACT-2+ (Section 9 APEM)
deny {
    input.performative == "config_change"
    input.act_tier >= 2
    not data.nexus.approvals.config_change[input.agent_id][input.change_hash]
    deny_reason := "ConfigChange requires out-of-band approval for ACT-2+ agents"
}

# ── Combined authorization decision ──────────────────────────────────────────
# Returns the full decision with audit metadata for NOR chain.
authorize_tool_call := decision {
    decision := {
        "allow": allow,
        "mandate_required": mandate_required,
        "deny_reason": deny_reason,
        "policy_version": "nexus-authz-v0.2",
        "decision_timestamp": time.now_ns(),
        "agent_id": input.agent_id,
        "tool_name": input.tool_name,
        "delegation_depth": input.delegation_depth,
    }
}
