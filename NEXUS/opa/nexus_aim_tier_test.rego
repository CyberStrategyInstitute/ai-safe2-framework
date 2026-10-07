package nexus.aim_tier_test

import rego.v1

import data.nexus.aism
import data.nexus.authz

# Registry-bound ACT tiers (AIM v0.3, IETF draft section 3.1.1). The tier an agent
# operates at comes from its registered AIM, not from the request.

registry := {"required": true, "agents": {
	"did:nexus:agent:low": {"act_tier": 1},
	"did:nexus:agent:high": {"act_tier": 3},
}}

call(agent, extra) := object.union(
	{
		"agent_id": agent,
		"tool_name": "update_config",
		"vcc_capabilities": ["update_config", "read_doc"],
		"vcc_mandate_required": [],
		"delegation_depth": 1,
		"context_compartment": "TASK_CONTEXT",
		"parent_vcc_capabilities": ["update_config", "read_doc"],
		"requested_new_capabilities": [],
	},
	extra,
)

# Regression: omitting act_tier skipped the ACT-2+ config-change approval.
test_config_change_without_declared_tier_needs_approval if {
	not authz.allow with input as call("did:nexus:agent:x", {"performative": "config_change", "change_hash": "h"})
}

test_registered_tier_overrides_a_lower_claim if {
	d := authz.authorize_tool_call with input as call("did:nexus:agent:high", {"performative": "config_change", "act_tier": 1, "change_hash": "h"})
		with data.nexus.aim as registry
	d.allow == false
	d.effective_act_tier == 3
	contains(d.deny_reason, "ConfigChange requires out-of-band approval")
}

test_claim_above_registered_tier_is_denied if {
	d := authz.authorize_tool_call with input as call("did:nexus:agent:low", {"tool_name": "read_doc", "act_tier": 3})
		with data.nexus.aim as registry
	d.allow == false
	contains(d.deny_reason, "exceeds registered ACT tier")
}

test_unregistered_agent_denied_when_registry_required if {
	d := authz.authorize_tool_call with input as call("did:nexus:agent:ghost", {"tool_name": "read_doc", "act_tier": 1})
		with data.nexus.aim as registry
	d.allow == false
	contains(d.deny_reason, "no registered AIM")
}

test_registered_low_tier_ordinary_call_allowed if {
	d := authz.authorize_tool_call with input as call("did:nexus:agent:low", {"tool_name": "read_doc"})
		with data.nexus.aim as registry
	d.allow == true
	d.effective_act_tier == 1
}

test_no_registry_keeps_declared_tier if {
	d := authz.authorize_tool_call with input as call("did:nexus:agent:x", {"tool_name": "read_doc", "act_tier": 1})
	d.allow == true
	d.effective_act_tier == 1
}

aism_agent(did, extra) := {"agent": object.union(
	{
		"did": did,
		"spiffe_id": "spiffe://nexus.local/agent/t",
		"aim_digest": "abc",
		"kill_switch": {},
		"aim": {"oor_contact": "owner@example.org", "oor_designation_date": "2026-10-07", "oor_hear_acknowledged": true},
	},
	extra,
)}

# Regression: an agent that omitted act_tier passed I-4 with no kill path at all.
test_i4_undeclared_tier_requires_kill_path if {
	some msg in aism.violation_i4 with input as aism_agent("did:nexus:agent:x", {})
	contains(msg, "no registered kill pathway")
}

test_i4_uses_registered_tier_not_claim if {
	some msg in aism.violation_i4 with input as aism_agent("did:nexus:agent:high", {"act_tier": 1})
		with data.nexus.aim as registry
	contains(msg, "ACT-3")
}

test_i4_low_registered_tier_needs_no_kill_path if {
	count(aism.violation_i4) == 0 with input as aism_agent("did:nexus:agent:low", {"act_tier": 1})
		with data.nexus.aim as registry
}
