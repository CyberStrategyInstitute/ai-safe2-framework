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

import rego.v1

default allow := false

default mandate_required := false

default deny_reason := ""

# ---------------------------------------------------------------------------
# v3.1 persistence-scope compatibility
# ---------------------------------------------------------------------------

# Persistence scope resolution (fail closed).
# Every declared value is considered and the MOST restrictive wins. Previously a
# caller-supplied persistence_scope of "request" overrode memory_zone "PERMANENT"
# and removed the mandate requirement. An unrecognized value counts as the most
# restrictive scope, so a typo or novel label cannot weaken enforcement.
_scope_rank := {"request": 0, "handle_scoped": 1, "durable": 2, "swarm_shared": 3}

_zone_scope := {
	"SESSION": "request", "SESSION_MEMORY": "request", "request": "request",
	"CROSS_SESSION": "handle_scoped", "CROSS_SESSION_MEMORY": "handle_scoped",
	"handle_scoped": "handle_scoped", "cross_session": "handle_scoped",
	"PERMANENT": "durable", "PERMANENT_MEMORY": "durable", "durable": "durable",
	"permanent": "durable",
	"SWARM_SHARED": "swarm_shared", "SWARM_SHARED_MEMORY": "swarm_shared",
	"swarm_shared": "swarm_shared",
}

_declared_scope_ranks contains rank if {
	declared := lower(input.persistence_scope)
	rank := object.get(_scope_rank, declared, 3)
}

_declared_scope_ranks contains rank if {
	input.memory_zone
	rank := object.get(_scope_rank, object.get(_zone_scope, input.memory_zone, "swarm_shared"), 3)
}

persistence_scope := scope if {
	count(_declared_scope_ranks) > 0
	top := max(_declared_scope_ranks)
	some scope, rank in _scope_rank
	rank == top
}

# No declaration at all. An ordinary tool call is request-scoped. A memory write
# that declares nothing is treated as the most restrictive scope, so omitting the
# field can never be cheaper than declaring it. Without these two rules the
# combined decision below was undefined for every call that carried no scope.
persistence_scope := "request" if {
	count(_declared_scope_ranks) == 0
	not input.performative == "memory_write"
}

persistence_scope := "swarm_shared" if {
	count(_declared_scope_ranks) == 0
	input.performative == "memory_write"
}

requires_memory_mandate if {
	persistence_scope in {"durable", "swarm_shared"}
}

# ---------------------------------------------------------------------------
# Registry-bound ACT tier (AIM v0.3, IETF draft section 3.1.1)
# ---------------------------------------------------------------------------

# The tier an agent operates at is an identity property set by its owner of
# record in the registered AIM (data.nexus.aim.agents[<did>].act_tier). A tier
# in the request is only a claim: it may not exceed the registered tier and can
# never lower it. With no registry entry the declared tier is used, and an
# agent that declares nothing is treated as ACT-4 so tier-gated requirements
# cannot be skipped by omission.
_registered_tier := t if {
	t := data.nexus.aim.agents[input.agent_id].act_tier
	is_number(t)
}

_has_registered_tier if is_number(_registered_tier)

_has_declared_tier if is_number(input.act_tier)

effective_act_tier := _registered_tier if _has_registered_tier

effective_act_tier := input.act_tier if {
	not _has_registered_tier
	_has_declared_tier
}

effective_act_tier := 4 if {
	not _has_registered_tier
	not _has_declared_tier
}

# ---------------------------------------------------------------------------
# Primary allow rule
# ---------------------------------------------------------------------------

allow if {
	has_valid_capability
	not is_mandate_required_op
	within_delegation_depth_limit
	not is_agent_revoked
	is_valid_context_compartment
	not is_scope_widening
	not memory_mandate_missing
	not deny
}

# ---------------------------------------------------------------------------
# Mandate handling
# ---------------------------------------------------------------------------

mandate_required if {
	input.tool_name in input.vcc_mandate_required
	not valid_mandate_exists
}

mandate_required if {
	input.performative == "memory_write"
	requires_memory_mandate
	not valid_mandate_exists
}

valid_mandate_exists if {
	input.mandate_id != null
	input.mandate_id != ""
	data.nexus.mandates.active[input.mandate_id]
}

# ---------------------------------------------------------------------------
# Core conditions
# ---------------------------------------------------------------------------

has_valid_capability if {
	input.tool_name in input.vcc_capabilities
}

is_mandate_required_op if {
	input.tool_name in input.vcc_mandate_required
	not valid_mandate_exists
}

memory_mandate_missing if {
	input.performative == "memory_write"
	requires_memory_mandate
	not valid_mandate_exists
}

within_delegation_depth_limit if {
	input.delegation_depth <= 4
}

is_agent_revoked if {
	data.nexus.revocation.agents[input.agent_id].status == "revoked"
}

is_agent_revoked if {
	data.nexus.revocation.agents[input.agent_id].status == "hard_brake"
}

is_valid_context_compartment if {
	input.context_compartment in {"TASK_CONTEXT", "CREDENTIAL_SURFACE", "AGENT_STATE"}
}

is_scope_widening if {
	some cap in input.requested_new_capabilities
	not cap in input.parent_vcc_capabilities
}

# ---------------------------------------------------------------------------
# Explicit deny reasons
# ---------------------------------------------------------------------------

# Each matching rule contributes its reason. Previously each rule assigned a
# body-local `deny_reason`, which never set the exported document, so callers
# always received an empty reason (surfaced by `opa check --strict`).
deny_reasons contains "TASK_CONTEXT cannot access credential: tools" if {
	input.context_compartment == "TASK_CONTEXT"
	startswith(input.tool_name, "credential:")
}

deny_reasons contains concat("", [persistence_scope, " memory writes require a Memory Mandate"]) if {
	input.performative == "memory_write"
	requires_memory_mandate
	not valid_mandate_exists
}

deny_reasons contains "ConfigChange requires out-of-band approval for ACT-2+ agents" if {
	input.performative == "config_change"
	effective_act_tier >= 2
	not data.nexus.approvals.config_change[input.agent_id][input.change_hash]
}

deny_reasons contains "agent has no registered AIM (registry required)" if {
	data.nexus.aim.required == true
	not data.nexus.aim.agents[input.agent_id]
}

deny_reasons contains msg if {
	_has_registered_tier
	_has_declared_tier
	input.act_tier > _registered_tier
	msg := sprintf("declared ACT-%v exceeds registered ACT tier %v", [input.act_tier, _registered_tier])
}

deny if count(deny_reasons) > 0

# Reasons for failing a primary allow condition. These do not feed `deny`; they
# exist so a refusal is explainable instead of an empty string.
_unmet contains "tool not in VCC capabilities" if not has_valid_capability

_unmet contains "tool requires an active mandate" if is_mandate_required_op

_unmet contains "delegation depth missing or above 4" if not within_delegation_depth_limit

_unmet contains "agent revoked or under hard brake" if is_agent_revoked

_unmet contains "unrecognized context compartment" if not is_valid_context_compartment

_unmet contains "requested capabilities exceed parent VCC" if is_scope_widening

_all_reasons := deny_reasons | _unmet

deny_reason := concat("; ", sort(_all_reasons)) if {
	not allow
	count(_all_reasons) > 0
}

# ---------------------------------------------------------------------------
# Combined authorization decision
# ---------------------------------------------------------------------------

authorize_tool_call := decision if {
	decision := {
		"allow": allow,
		"mandate_required": mandate_required,
		"deny_reason": deny_reason,
		"policy_version": "nexus-authz-v0.3-v31",
		"framework_version": "AI SAFE2 v3.1",
		"decision_timestamp": time.now_ns(),
		"agent_id": object.get(input, "agent_id", null),
		"tool_name": object.get(input, "tool_name", null),
		"delegation_depth": object.get(input, "delegation_depth", null),
		"persistence_scope": persistence_scope,
		"effective_act_tier": effective_act_tier,
	}
}
