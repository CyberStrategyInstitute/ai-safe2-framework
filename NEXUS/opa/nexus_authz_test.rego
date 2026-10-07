package nexus.authz_test

import rego.v1

import data.nexus.authz

base := {
	"tool_name": "memory_store",
	"performative": "memory_write",
	"vcc_capabilities": ["memory_store"],
	"vcc_mandate_required": [],
	"delegation_depth": 0,
	"agent_did": "did:nexus:agent:a",
	"context_compartment": "default",
}

# Regression (2026-10-06): a caller-declared persistence_scope of "request" on a
# PERMANENT write used to remove the mandate requirement.
test_declared_request_scope_cannot_downgrade_permanent_write if {
	authz.mandate_required with input as object.union(base, {"memory_zone": "PERMANENT", "persistence_scope": "request"})
	authz.persistence_scope == "durable" with input as object.union(base, {"memory_zone": "PERMANENT", "persistence_scope": "request"})
}

test_most_restrictive_declaration_wins if {
	authz.persistence_scope == "swarm_shared" with input as object.union(base, {"memory_zone": "SWARM_SHARED", "persistence_scope": "durable"})
}

test_unknown_scope_label_fails_closed if {
	authz.mandate_required with input as object.union(base, {"persistence_scope": "bogus"})
	authz.mandate_required with input as object.union(base, {"memory_zone": "weird"})
}

test_consistent_request_scope_needs_no_mandate if {
	not authz.mandate_required with input as object.union(base, {"memory_zone": "SESSION", "persistence_scope": "request"})
}

test_valid_mandate_satisfies_durable_write if {
	not authz.mandate_required with input as object.union(base, {"memory_zone": "PERMANENT", "mandate_id": "M-1"})
		with data.nexus.mandates.active as {"M-1": true}
}

# Regression (2026-10-06): deny reasons were assigned to body-local variables and
# never reached the exported document, so every denial carried an empty reason.
test_denial_reports_its_reason if {
	authz.deny with input as object.union(base, {"memory_zone": "PERMANENT"})
	contains(authz.deny_reason, "durable memory writes require a Memory Mandate") with input as object.union(base, {"memory_zone": "PERMANENT"})
}

call := {
	"agent_id": "did:nexus:agent:a",
	"tool_name": "read_doc",
	"vcc_capabilities": ["read_doc", "credential:vault"],
	"vcc_mandate_required": [],
	"delegation_depth": 1,
	"context_compartment": "TASK_CONTEXT",
	"parent_vcc_capabilities": ["read_doc"],
	"requested_new_capabilities": [],
}

# Regression (2026-10-06): with no persistence declaration the combined decision
# was undefined, so every ordinary tool call returned no decision at all.
test_ordinary_call_has_a_decision if {
	d := authz.authorize_tool_call with input as call
	d.allow == true
	d.persistence_scope == "request"
}

test_decision_defined_when_fields_missing if {
	d := authz.authorize_tool_call with input as object.remove(call, ["delegation_depth", "agent_id"])
	d.allow == false
	contains(d.deny_reason, "delegation depth")
}

test_undeclared_memory_write_needs_mandate if {
	authz.mandate_required with input as object.union(call, {"tool_name": "read_doc", "performative": "memory_write"})
}

# Regression (2026-10-06): explicit deny rules never gated `allow`.
test_explicit_deny_blocks_allow if {
	not authz.allow with input as object.union(call, {"tool_name": "credential:vault"})
	not authz.allow with input as object.union(call, {"performative": "config_change", "act_tier": 2, "change_hash": "h"})
}

test_approved_config_change_allowed if {
	authz.allow with input as object.union(call, {"performative": "config_change", "act_tier": 2, "change_hash": "h"})
		with data.nexus.approvals.config_change as {"did:nexus:agent:a": {"h": true}}
}
