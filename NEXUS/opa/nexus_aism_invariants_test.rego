package nexus.aism_test

import rego.v1

import data.nexus.aism

# Regression (2026-10-06): aism_score used `|` on arrays and the whole policy
# failed type-checking on every OPA version, so nothing in this file could load.
test_policy_loads_and_scores if {
	score := aism.aism_score with input as {}
	score >= 0
	score <= 1
}

test_i1_authenticated_borders_holds_with_full_identity if {
	aism.invariant_1_authenticated_borders with input as {"agent": {
		"did": "did:nexus:agent:test",
		"spiffe_id": "spiffe://nexus.local/agent/test",
		"aim_digest": "abc123",
	}}
}

test_i1_fails_without_did if {
	not aism.invariant_1_authenticated_borders with input as {"agent": {
		"spiffe_id": "spiffe://nexus.local/agent/test",
		"aim_digest": "abc123",
	}}
}

test_memory_scope_downgrade_is_blocked if {
	aism.memory_scope == "durable" with input as {"memory": {"zone": "PERMANENT", "persistence_scope": "request"}}
}

test_empty_input_is_not_allowed if {
	aism.aism_verdict != "allow" with input as {}
}
