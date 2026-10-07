# nexus-aism-invariants.rego
# NEXUS AISM invariants
# Cyber Strategy Institute | AI SAFE2 v3.1 | NEXUS-A2A v0.3
#
# Six minimum architecture invariants for governed autonomous-agent operation.
# Deploy alongside nexus-authz.rego.
#
# AI SAFE2 v3.1 persistence vocabulary:
#   request | handle_scoped | durable | swarm_shared
# Legacy aliases accepted during migration:
#   SESSION | CROSS_SESSION | PERMANENT | SWARM_SHARED
#
# Reference: NEXUS-A2A Specification v0.3, AISM, AI SAFE2 CP.4/CP.5/CP.9/CP.10

package nexus.aism

import rego.v1

# ---------------------------------------------------------------------------
# Compatibility helpers
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
	declared := lower(input.memory.persistence_scope)
	rank := object.get(_scope_rank, declared, 3)
}

_declared_scope_ranks contains rank if {
	input.memory.zone
	rank := object.get(_scope_rank, object.get(_zone_scope, input.memory.zone, "swarm_shared"), 3)
}

memory_scope := scope if {
	count(_declared_scope_ranks) > 0
	top := max(_declared_scope_ranks)
	some scope, rank in _scope_rank
	rank == top
}

is_request_scope if {
	memory_scope == "request"
}

is_persistent_scope if {
	memory_scope in {"handle_scoped", "durable", "swarm_shared"}
}

# ---------------------------------------------------------------------------
# I-1: AUTHENTICATED BORDERS
# ---------------------------------------------------------------------------

default invariant_1_authenticated_borders := false

invariant_1_authenticated_borders if {
	input.agent.did != ""
	startswith(input.agent.did, "did:")
	input.agent.spiffe_id != ""
	startswith(input.agent.spiffe_id, "spiffe://")
	input.agent.aim_digest != ""
}

violation_i1 contains msg if {
	not input.agent.did
	msg := "I-1 VIOLATED: agent.did absent; communication boundary is unauthenticated"
}

violation_i1 contains msg if {
	input.agent.did != ""
	not startswith(input.agent.did, "did:")
	msg := concat("", ["I-1 VIOLATED: malformed DID; expected did: prefix; got ", input.agent.did])
}

violation_i1 contains msg if {
	not input.agent.spiffe_id
	msg := "I-1 VIOLATED: agent.spiffe_id absent; workload attestation missing"
}

violation_i1 contains msg if {
	input.agent.spiffe_id != ""
	not startswith(input.agent.spiffe_id, "spiffe://")
	msg := "I-1 VIOLATED: malformed SPIFFE ID; expected spiffe:// prefix"
}

# ---------------------------------------------------------------------------
# I-2: MONOTONICALLY NARROWING SCOPE
# ---------------------------------------------------------------------------

default invariant_2_monotonic_scope := false

invariant_2_monotonic_scope if {
	input.delegation.depth == 0
}

invariant_2_monotonic_scope if {
	input.delegation.depth > 0
	every scope in input.agent.vcc.granted_scopes {
		scope in input.delegation.parent_scopes
	}
}

violation_i2 contains msg if {
	input.delegation.depth > 0
	some scope in input.agent.vcc.granted_scopes
	not scope in input.delegation.parent_scopes
	msg := concat("", [
		"I-2 VIOLATED: scope amplification at delegation depth ",
		format_int(input.delegation.depth, 10),
		"; capability '", scope, "' not in parent grant",
	])
}

violation_i2 contains msg if {
	input.delegation.depth > 4
	msg := concat("", [
		"I-2 VIOLATED: delegation depth ",
		format_int(input.delegation.depth, 10),
		" exceeds maximum of 4",
	])
}

# ---------------------------------------------------------------------------
# I-3: MEMORY PROVENANCE
#
# v3.1 treats request-scoped state differently from state that persists through
# a governed handle or beyond the handle lifecycle. Legacy session labels are
# compatibility aliases only; they are not identity or authorization.
# ---------------------------------------------------------------------------

default invariant_3_memory_provenance := false

invariant_3_memory_provenance if {
	is_request_scope
}

invariant_3_memory_provenance if {
	is_persistent_scope
	input.memory.provenance.source_did != ""
	input.memory.provenance.timestamp_utc != ""
	input.memory.provenance.embedding_hash != ""
	provenance_scope := input.memory.provenance.persistence_scope
	provenance_scope != ""
}

# Legacy provenance field accepted during migration.
invariant_3_memory_provenance if {
	is_persistent_scope
	input.memory.provenance.source_did != ""
	input.memory.provenance.timestamp_utc != ""
	input.memory.provenance.embedding_hash != ""
	not input.memory.provenance.persistence_scope
	input.memory.provenance.zone_class != ""
}

violation_i3 contains msg if {
	is_persistent_scope
	not input.memory.provenance.source_did
	msg := concat("", ["I-3 VIOLATED: ", memory_scope, " memory write has no source_did provenance"])
}

violation_i3 contains msg if {
	is_persistent_scope
	not input.memory.provenance.embedding_hash
	msg := concat("", ["I-3 VIOLATED: ", memory_scope, " memory write has no embedding_hash"])
}

violation_i3 contains msg if {
	is_persistent_scope
	input.memory.drift_score > 0.3
	msg := concat("", [
		"I-3 VIOLATED: memory drift score ",
		sprintf("%.3f", [input.memory.drift_score]),
		" exceeds 0.3 hard brake",
	])
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
	t := data.nexus.aim.agents[input.agent.did].act_tier
	is_number(t)
}

_has_registered_tier if is_number(_registered_tier)

_has_declared_tier if is_number(input.agent.act_tier)

effective_act_tier := _registered_tier if _has_registered_tier

effective_act_tier := input.agent.act_tier if {
	not _has_registered_tier
	_has_declared_tier
}

effective_act_tier := 4 if {
	not _has_registered_tier
	not _has_declared_tier
}

# ---------------------------------------------------------------------------
# I-4: INDEPENDENT KILL PATH
# ---------------------------------------------------------------------------

default invariant_4_kill_switch := false

invariant_4_kill_switch if {
	effective_act_tier < 2
}

invariant_4_kill_switch if {
	effective_act_tier >= 2
	input.agent.kill_switch.operator_registered == true
}

invariant_4_kill_switch if {
	effective_act_tier >= 2
	input.agent.kill_switch.domain_registered == true
}

violation_i4 contains msg if {
	effective_act_tier >= 2
	not input.agent.kill_switch.operator_registered
	not input.agent.kill_switch.domain_registered
	msg := concat("", [
		"I-4 VIOLATED: ACT-", format_int(effective_act_tier, 10),
		" agent '", input.agent.did, "' has no registered kill pathway",
	])
}

violation_i4 contains msg if {
	effective_act_tier >= 4
	not input.agent.kill_switch.cryptographic_kill_confirmed
	msg := concat("", [
		"I-4 VIOLATED: ACT-4 agent '", input.agent.did,
		"' requires an independently operable cryptographic kill path",
	])
}

# ---------------------------------------------------------------------------
# I-5: OWNER OF RECORD
# ---------------------------------------------------------------------------

default invariant_5_owner_of_record := false

invariant_5_owner_of_record if {
	input.agent.aim.oor_contact != ""
	input.agent.aim.oor_designation_date != ""
	input.agent.aim.oor_hear_acknowledged == true
}

violation_i5 contains msg if {
	not input.agent.aim.oor_contact
	msg := concat("", ["I-5 VIOLATED: agent '", input.agent.did, "' has no owner-of-record"])
}

violation_i5 contains msg if {
	input.agent.aim.oor_contact != ""
	not input.agent.aim.oor_hear_acknowledged
	msg := concat("", [
		"I-5 VIOLATED: owner-of-record for '", input.agent.did,
		"' has not acknowledged HEAR responsibilities",
	])
}

violation_i5 contains msg if {
	effective_act_tier >= 3
	not input.agent.aim.oor_escalation_contact
	msg := concat("", [
		"I-5 VIOLATED: ACT-3+ agent '", input.agent.did,
		"' requires an escalation contact",
	])
}

# ---------------------------------------------------------------------------
# I-6: BIAS / BEHAVIORAL DRIFT AS SECURITY OBSERVABLE
# ---------------------------------------------------------------------------

default invariant_6_bias_observable := false

invariant_6_bias_observable if {
	not input.behavioral_metrics
}

invariant_6_bias_observable if {
	input.behavioral_metrics.capability_drift_score <= 0.25
	input.behavioral_metrics.goal_alignment_score >= 0.75
	input.behavioral_metrics.nor_coverage_pct >= 80
}

violation_i6 contains msg if {
	input.behavioral_metrics.capability_drift_score > 0.25
	msg := concat("", [
		"I-6 VIOLATED: capability drift score ",
		sprintf("%.3f", [input.behavioral_metrics.capability_drift_score]),
		" exceeds 0.25 threshold",
	])
}

violation_i6 contains msg if {
	input.behavioral_metrics.goal_alignment_score < 0.75
	msg := concat("", [
		"I-6 VIOLATED: goal alignment score ",
		sprintf("%.3f", [input.behavioral_metrics.goal_alignment_score]),
		" below 0.75 floor",
	])
}

violation_i6 contains msg if {
	input.behavioral_metrics.nor_coverage_pct < 80
	msg := concat("", [
		"I-6 VIOLATED: NOR coverage at ",
		sprintf("%.1f", [input.behavioral_metrics.nor_coverage_pct]),
		"% below 80% minimum",
	])
}

# ---------------------------------------------------------------------------
# I-7: RUNTIME-BOUND AUTHORITY  (added in NEXUS v0.4 / CP.5.APAY)
# ---------------------------------------------------------------------------
# Authority to take a consequential action binds to a fresh measurement of the
# workload exercising it, not only to the identity presenting it.
#
# Rationale: identity answers "which agent arrived". Every published agent
# identity and agent payment protocol stops there. None of them establish that
# the workload holding a valid credential is still running the software that was
# approved. An attacker who owns the agent host inherits its identity and its
# mandates intact, and every signature they produce verifies correctly.
#
# Scope: applies where consequence_class is consequential or critical, which is
# how economically irreversible actions enter scope without forcing attestation
# onto every low-impact call.

invariant_7_runtime_bound_authority if {
	not requires_runtime_binding
}

invariant_7_runtime_bound_authority if {
	requires_runtime_binding
	input.runtime.attested == true
	not input.runtime.attestation_method in {"none", "declared"}
	input.runtime.age_seconds <= input.runtime.max_age_seconds
}

requires_runtime_binding if {
	input.consequence_class in {"consequential", "critical"}
}

requires_runtime_binding if {
	input.grant.constraints.min_assurance >= 4
}

violation_i7 contains msg if {
	requires_runtime_binding
	not input.runtime
	msg := "I-7 VIOLATED: consequential action attempted with no runtime measurement"
}

violation_i7 contains msg if {
	requires_runtime_binding
	input.runtime
	not input.runtime.attested
	msg := "I-7 VIOLATED: runtime measurement is self-declared, not attested"
}

violation_i7 contains msg if {
	requires_runtime_binding
	input.runtime.age_seconds > input.runtime.max_age_seconds
	msg := concat("", [
		"I-7 VIOLATED: runtime measurement is ",
		sprintf("%.0f", [input.runtime.age_seconds]),
		"s old, exceeding the ",
		sprintf("%d", [input.runtime.max_age_seconds]),
		"s freshness requirement",
	])
}

# ---------------------------------------------------------------------------
# I-8: AGGREGATE ECONOMIC CONTAINMENT  (added in NEXUS v0.4 / CP.5.APAY)
# ---------------------------------------------------------------------------
# Consumable authority - spend, compute, tokens, API quota - aggregates across
# the whole authority tree, and every descendant's consumption counts against
# every ancestor's ceiling.
#
# Rationale: a per-action limit is the control an attacker never has to break.
# Consumption is simply distributed across children, counterparties, rails and
# time until each individual check passes. Containment that is not evaluated on
# the tree is not containment.

invariant_8_aggregate_containment if {
	not has_economic_ceiling
}

invariant_8_aggregate_containment if {
	has_economic_ceiling
	input.exposure.aggregation_scope == "subtree"
	input.exposure.subtree_committed <= input.economic_ceiling.max_aggregate
}

has_economic_ceiling if {
	input.economic_ceiling.max_aggregate
}

violation_i8 contains msg if {
	has_economic_ceiling
	not input.exposure
	msg := "I-8 VIOLATED: economic ceiling declared with no exposure accounting"
}

violation_i8 contains msg if {
	has_economic_ceiling
	input.exposure.aggregation_scope != "subtree"
	msg := concat("", [
		"I-8 VIOLATED: exposure aggregated at scope '",
		input.exposure.aggregation_scope,
		"'; descendant consumption is not counted against this ceiling",
	])
}

violation_i8 contains msg if {
	has_economic_ceiling
	input.exposure.subtree_committed > input.economic_ceiling.max_aggregate
	msg := "I-8 VIOLATED: committed subtree exposure exceeds the aggregate ceiling"
}

# ---------------------------------------------------------------------------
# AGGREGATE
# ---------------------------------------------------------------------------

invariants_satisfied if {
	invariant_1_authenticated_borders
	invariant_2_monotonic_scope
	invariant_3_memory_provenance
	invariant_4_kill_switch
	invariant_5_owner_of_record
	invariant_6_bias_observable
	invariant_7_runtime_bound_authority
	invariant_8_aggregate_containment
}

all_violations := union({
	violation_i1,
	violation_i2,
	violation_i3,
	violation_i4,
	violation_i5,
	violation_i6,
	violation_i7,
	violation_i8,
})

invariant_violations := all_violations

# Fraction of the eight invariants that hold. The previous form combined
# array comprehensions with `|` (set union), which fails type-checking on every
# OPA version, so this policy file could not be loaded at all.
aism_score := count([1 |
	some satisfied in [
		invariant_1_authenticated_borders,
		invariant_2_monotonic_scope,
		invariant_3_memory_provenance,
		invariant_4_kill_switch,
		invariant_5_owner_of_record,
		invariant_6_bias_observable,
		invariant_7_runtime_bound_authority,
		invariant_8_aggregate_containment,
	]
	satisfied == true
]) / 8

aism_verdict := "allow" if count(all_violations) == 0
aism_verdict := "deny" if count(all_violations) > 0

aism_deny_reasons := [msg | msg := all_violations[_]]
