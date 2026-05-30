package hsr.subagent_scope

# =============================================================================
# Subagent Scope & Capability Inheritance Policy — Hermes Sovereign Runtime
# AI SAFE² v3.0 | Cyber Strategy Institute
#
# Hermes supports delegated subagent orchestration. Each subagent spawn is a
# capability delegation event. This policy enforces:
# - Least-privilege: subagents get only what they explicitly need
# - Memory isolation: subagents cannot read parent memory
# - Depth limits: no recursive subagent spawning
# - Attestation: all inter-agent calls must be signed
# =============================================================================

import future.keywords.if
import future.keywords.in

default allow_spawn := false
default allow_inter_agent_call := false

# ---------------------------------------------------------------------------
# SPAWN AUTHORIZATION
# ---------------------------------------------------------------------------

allow_spawn if {
    valid_spawn_request
    not exceeds_depth_limit
    not inherits_forbidden_tools
    not exceeds_active_limit
    operator_approved_or_low_risk
}

valid_spawn_request if {
    input.subagent.requested_tools != null
    count(input.subagent.requested_tools) > 0
    count(input.subagent.requested_tools) <= 5   # Max 5 tools per subagent
    input.subagent.scope_declaration != ""
    input.subagent.owner_agent_id != ""
}

exceeds_depth_limit if {
    # Prevent subagents spawning subagents (depth limit = 1)
    input.parent.is_subagent == true
}

inherits_forbidden_tools if {
    forbidden := {"terminal", "install_plugin", "spawn_subagent", "cron_create",
                  "pip_install", "git_push", "execute_skill"}
    some tool in input.subagent.requested_tools
    tool in forbidden
}

exceeds_active_limit if {
    input.context.active_subagent_count >= 5
}

operator_approved_or_low_risk if {
    input.context.operator_approved == true
}

operator_approved_or_low_risk if {
    low_risk_tools_only
}

low_risk_tools_only if {
    low_risk := {"read_file", "web_search", "memory_search", "web_fetch", "list_directory"}
    count({t | t := input.subagent.requested_tools[_]; not t in low_risk}) == 0
}

# ---------------------------------------------------------------------------
# INTER-AGENT CALL AUTHORIZATION
# ---------------------------------------------------------------------------

allow_inter_agent_call if {
    valid_attestation
    not kill_switch_active
    caller_in_trust_registry
    request_within_scope
}

valid_attestation if {
    input.attestation.algorithm == "HMAC-SHA256"
    input.attestation.signature != ""
    input.attestation.timestamp > time.now_ns() - (30 * 1000000000)  # 30-second freshness
}

kill_switch_active if {
    input.context.kill_switch == true
}

caller_in_trust_registry if {
    input.caller.agent_id in data.trust_registry.approved_agents
}

request_within_scope if {
    # Verify the requested action is within the subagent's declared scope
    input.requested_tool in input.caller.approved_tools
}

# ---------------------------------------------------------------------------
# MEMORY ISOLATION ENFORCEMENT
# ---------------------------------------------------------------------------

# Subagents are NEVER allowed to read parent agent memory
deny_memory_access if {
    input.request_type == "memory_read"
    input.requester.is_subagent == true
    input.target_memory.owner != input.requester.agent_id
}

# Subagents can only write to their isolated workspace
deny_write_access if {
    input.request_type == "memory_write"
    input.requester.is_subagent == true
    not startswith(input.target_path, input.requester.workspace_root)
}

# ---------------------------------------------------------------------------
# CAPABILITY DELTA REPORTING
# Report what tools the subagent is being denied vs requested
# ---------------------------------------------------------------------------

denied_tools[tool] if {
    tool := input.subagent.requested_tools[_]
    forbidden := {"terminal", "install_plugin", "spawn_subagent", "cron_create"}
    tool in forbidden
}

# ---------------------------------------------------------------------------
# AUDIT METADATA
# ---------------------------------------------------------------------------

policy_version := "1.0.0"
framework := "AI SAFE² v3.0"
pillar := "P1-Sanitize-Isolate"
cross_pillar := "CP.9-Agent-Replication-Governance"
