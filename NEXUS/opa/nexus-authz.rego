# nexus-authz.rego
# NEXUS L3 Core Authorization Policy
# AI SAFE2 v3.1 compatible | NEXUS-A2A v0.3
#
# Deploy: opa run --server --bundle ./opa/
# Query: POST http://localhost:8181/v1/data/nexus/authz/authorize_tool_call
#
# This policy runs outside the agent process. Governance decisions bind to
# verified identity, capability, delegation, policy context, and explicit
# persistence scope rather than a transport session.

package nexus.authz

import future.keywords.in

default allow = false
default mandate_required = false
default deny_reason = ""

# ---------------------------------------------------------------------------
# v3.1 persistence-scope compatibility
# ---------------------------------------------------------------------------

persistence_scope := scope {
    input.persistence_scope
    scope := lower(input.persistence_scope)
}

persistence_scope := "request" {
    not input.persistence_scope
    input.memory_zone in {"SESSION", "SESSION_MEMORY", "request"}
}

persistence_scope := "handle_scoped" {
    not input.persistence_scope
    input.memory_zone in {"CROSS_SESSION", "CROSS_SESSION_MEMORY", "handle_scoped", "cross_session"}
}

persistence_scope := "durable" {
    not input.persistence_scope
    input.memory_zone in {"PERMANENT", "PERMANENT_MEMORY", "durable", "permanent"}
}

persistence_scope := "swarm_shared" {
    not input.persistence_scope
    input.memory_zone in {"SWARM_SHARED", "SWARM_SHARED_MEMORY", "swarm_shared"}
}

requires_memory_mandate {
    persistence_scope in {"durable", "swarm_shared"}
}

# ---------------------------------------------------------------------------
# Primary allow rule
# ---------------------------------------------------------------------------

allow {
    has_valid_capability
    not is_mandate_required_op
    within_delegation_depth_limit
    not is_agent_revoked
    is_valid_context_compartment
    not is_scope_widening
    not memory_mandate_missing
}

# ---------------------------------------------------------------------------
# Mandate handling
# ---------------------------------------------------------------------------

mandate_required {
    input.tool_name in input.vcc_mandate_required
    not valid_mandate_exists
}

mandate_required {
    input.performative == "memory_write"
    requires_memory_mandate
    not valid_mandate_exists
}

valid_mandate_exists {
    input.mandate_id != null
    input.mandate_id != ""
    data.nexus.mandates.active[input.mandate_id]
}

# ---------------------------------------------------------------------------
# Core conditions
# ---------------------------------------------------------------------------

has_valid_capability {
    input.tool_name in input.vcc_capabilities
}

is_mandate_required_op {
    input.tool_name in input.vcc_mandate_required
    not valid_mandate_exists
}

memory_mandate_missing {
    input.performative == "memory_write"
    requires_memory_mandate
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

is_scope_widening {
    some cap in input.requested_new_capabilities
    not cap in input.parent_vcc_capabilities
}

# ---------------------------------------------------------------------------
# Explicit deny reasons
# ---------------------------------------------------------------------------

deny {
    input.context_compartment == "TASK_CONTEXT"
    startswith(input.tool_name, "credential:")
    deny_reason := "TASK_CONTEXT cannot access credential: tools"
}

deny {
    input.performative == "memory_write"
    requires_memory_mandate
    not valid_mandate_exists
    deny_reason := concat("", [persistence_scope, " memory writes require a Memory Mandate"])
}

deny {
    input.performative == "config_change"
    input.act_tier >= 2
    not data.nexus.approvals.config_change[input.agent_id][input.change_hash]
    deny_reason := "ConfigChange requires out-of-band approval for ACT-2+ agents"
}

# ---------------------------------------------------------------------------
# Combined authorization decision
# ---------------------------------------------------------------------------

authorize_tool_call := decision {
    decision := {
        "allow": allow,
        "mandate_required": mandate_required,
        "deny_reason": deny_reason,
        "policy_version": "nexus-authz-v0.3-v31",
        "framework_version": "AI SAFE2 v3.1",
        "decision_timestamp": time.now_ns(),
        "agent_id": input.agent_id,
        "tool_name": input.tool_name,
        "delegation_depth": input.delegation_depth,
        "persistence_scope": persistence_scope,
    }
}
