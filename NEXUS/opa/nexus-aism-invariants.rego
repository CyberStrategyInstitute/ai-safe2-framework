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

import future.keywords.in
import future.keywords.every

# ---------------------------------------------------------------------------
# Compatibility helpers
# ---------------------------------------------------------------------------

memory_scope := scope {
    input.memory.persistence_scope
    scope := lower(input.memory.persistence_scope)
}

memory_scope := "request" {
    not input.memory.persistence_scope
    input.memory.zone in {"SESSION", "SESSION_MEMORY", "request"}
}

memory_scope := "handle_scoped" {
    not input.memory.persistence_scope
    input.memory.zone in {"CROSS_SESSION", "CROSS_SESSION_MEMORY", "handle_scoped", "cross_session"}
}

memory_scope := "durable" {
    not input.memory.persistence_scope
    input.memory.zone in {"PERMANENT", "PERMANENT_MEMORY", "durable", "permanent"}
}

memory_scope := "swarm_shared" {
    not input.memory.persistence_scope
    input.memory.zone in {"SWARM_SHARED", "SWARM_SHARED_MEMORY", "swarm_shared"}
}

is_request_scope {
    memory_scope == "request"
}

is_persistent_scope {
    memory_scope in {"handle_scoped", "durable", "swarm_shared"}
}

# ---------------------------------------------------------------------------
# I-1: AUTHENTICATED BORDERS
# ---------------------------------------------------------------------------

default invariant_1_authenticated_borders = false

invariant_1_authenticated_borders {
    input.agent.did != ""
    startswith(input.agent.did, "did:")
    input.agent.spiffe_id != ""
    startswith(input.agent.spiffe_id, "spiffe://")
    input.agent.aim_digest != ""
}

violation_i1[msg] {
    not input.agent.did
    msg := "I-1 VIOLATED: agent.did absent; communication boundary is unauthenticated"
}

violation_i1[msg] {
    input.agent.did != ""
    not startswith(input.agent.did, "did:")
    msg := concat("", ["I-1 VIOLATED: malformed DID; expected did: prefix; got ", input.agent.did])
}

violation_i1[msg] {
    not input.agent.spiffe_id
    msg := "I-1 VIOLATED: agent.spiffe_id absent; workload attestation missing"
}

violation_i1[msg] {
    input.agent.spiffe_id != ""
    not startswith(input.agent.spiffe_id, "spiffe://")
    msg := "I-1 VIOLATED: malformed SPIFFE ID; expected spiffe:// prefix"
}

# ---------------------------------------------------------------------------
# I-2: MONOTONICALLY NARROWING SCOPE
# ---------------------------------------------------------------------------

default invariant_2_monotonic_scope = false

invariant_2_monotonic_scope {
    input.delegation.depth == 0
}

invariant_2_monotonic_scope {
    input.delegation.depth > 0
    every scope in input.agent.vcc.granted_scopes {
        scope in input.delegation.parent_scopes
    }
}

violation_i2[msg] {
    input.delegation.depth > 0
    some scope in input.agent.vcc.granted_scopes
    not scope in input.delegation.parent_scopes
    msg := concat("", [
        "I-2 VIOLATED: scope amplification at delegation depth ",
        format_int(input.delegation.depth, 10),
        "; capability '", scope, "' not in parent grant"
    ])
}

violation_i2[msg] {
    input.delegation.depth > 4
    msg := concat("", [
        "I-2 VIOLATED: delegation depth ",
        format_int(input.delegation.depth, 10),
        " exceeds maximum of 4"
    ])
}

# ---------------------------------------------------------------------------
# I-3: MEMORY PROVENANCE
#
# v3.1 treats request-scoped state differently from state that persists through
# a governed handle or beyond the handle lifecycle. Legacy session labels are
# compatibility aliases only; they are not identity or authorization.
# ---------------------------------------------------------------------------

default invariant_3_memory_provenance = false

invariant_3_memory_provenance {
    is_request_scope
}

invariant_3_memory_provenance {
    is_persistent_scope
    input.memory.provenance.source_did != ""
    input.memory.provenance.timestamp_utc != ""
    input.memory.provenance.embedding_hash != ""
    provenance_scope := input.memory.provenance.persistence_scope
    provenance_scope != ""
}

# Legacy provenance field accepted during migration.
invariant_3_memory_provenance {
    is_persistent_scope
    input.memory.provenance.source_did != ""
    input.memory.provenance.timestamp_utc != ""
    input.memory.provenance.embedding_hash != ""
    not input.memory.provenance.persistence_scope
    input.memory.provenance.zone_class != ""
}

violation_i3[msg] {
    is_persistent_scope
    not input.memory.provenance.source_did
    msg := concat("", ["I-3 VIOLATED: ", memory_scope, " memory write has no source_did provenance"])
}

violation_i3[msg] {
    is_persistent_scope
    not input.memory.provenance.embedding_hash
    msg := concat("", ["I-3 VIOLATED: ", memory_scope, " memory write has no embedding_hash"])
}

violation_i3[msg] {
    is_persistent_scope
    input.memory.drift_score > 0.3
    msg := concat("", [
        "I-3 VIOLATED: memory drift score ",
        sprintf("%.3f", [input.memory.drift_score]),
        " exceeds 0.3 hard brake"
    ])
}

# ---------------------------------------------------------------------------
# I-4: INDEPENDENT KILL PATH
# ---------------------------------------------------------------------------

default invariant_4_kill_switch = false

invariant_4_kill_switch {
    input.agent.act_tier < 2
}

invariant_4_kill_switch {
    input.agent.act_tier >= 2
    input.agent.kill_switch.operator_registered == true
}

invariant_4_kill_switch {
    input.agent.act_tier >= 2
    input.agent.kill_switch.domain_registered == true
}

violation_i4[msg] {
    input.agent.act_tier >= 2
    not input.agent.kill_switch.operator_registered
    not input.agent.kill_switch.domain_registered
    msg := concat("", [
        "I-4 VIOLATED: ACT-", format_int(input.agent.act_tier, 10),
        " agent '", input.agent.did, "' has no registered kill pathway"
    ])
}

violation_i4[msg] {
    input.agent.act_tier >= 4
    not input.agent.kill_switch.cryptographic_kill_confirmed
    msg := concat("", [
        "I-4 VIOLATED: ACT-4 agent '", input.agent.did,
        "' requires an independently operable cryptographic kill path"
    ])
}

# ---------------------------------------------------------------------------
# I-5: OWNER OF RECORD
# ---------------------------------------------------------------------------

default invariant_5_owner_of_record = false

invariant_5_owner_of_record {
    input.agent.aim.oor_contact != ""
    input.agent.aim.oor_designation_date != ""
    input.agent.aim.oor_hear_acknowledged == true
}

violation_i5[msg] {
    not input.agent.aim.oor_contact
    msg := concat("", ["I-5 VIOLATED: agent '", input.agent.did, "' has no owner-of-record"])
}

violation_i5[msg] {
    input.agent.aim.oor_contact != ""
    not input.agent.aim.oor_hear_acknowledged
    msg := concat("", [
        "I-5 VIOLATED: owner-of-record for '", input.agent.did,
        "' has not acknowledged HEAR responsibilities"
    ])
}

violation_i5[msg] {
    input.agent.act_tier >= 3
    not input.agent.aim.oor_escalation_contact
    msg := concat("", [
        "I-5 VIOLATED: ACT-3+ agent '", input.agent.did,
        "' requires an escalation contact"
    ])
}

# ---------------------------------------------------------------------------
# I-6: BIAS / BEHAVIORAL DRIFT AS SECURITY OBSERVABLE
# ---------------------------------------------------------------------------

default invariant_6_bias_observable = false

invariant_6_bias_observable {
    not input.behavioral_metrics
}

invariant_6_bias_observable {
    input.behavioral_metrics.capability_drift_score <= 0.25
    input.behavioral_metrics.goal_alignment_score >= 0.75
    input.behavioral_metrics.nor_coverage_pct >= 80
}

violation_i6[msg] {
    input.behavioral_metrics.capability_drift_score > 0.25
    msg := concat("", [
        "I-6 VIOLATED: capability drift score ",
        sprintf("%.3f", [input.behavioral_metrics.capability_drift_score]),
        " exceeds 0.25 threshold"
    ])
}

violation_i6[msg] {
    input.behavioral_metrics.goal_alignment_score < 0.75
    msg := concat("", [
        "I-6 VIOLATED: goal alignment score ",
        sprintf("%.3f", [input.behavioral_metrics.goal_alignment_score]),
        " below 0.75 floor"
    ])
}

violation_i6[msg] {
    input.behavioral_metrics.nor_coverage_pct < 80
    msg := concat("", [
        "I-6 VIOLATED: NOR coverage at ",
        sprintf("%.1f", [input.behavioral_metrics.nor_coverage_pct]),
        "% below 80% minimum"
    ])
}

# ---------------------------------------------------------------------------
# AGGREGATE
# ---------------------------------------------------------------------------

invariants_satisfied {
    invariant_1_authenticated_borders
    invariant_2_monotonic_scope
    invariant_3_memory_provenance
    invariant_4_kill_switch
    invariant_5_owner_of_record
    invariant_6_bias_observable
}

all_violations := union({
    violation_i1,
    violation_i2,
    violation_i3,
    violation_i4,
    violation_i5,
    violation_i6,
})

invariant_violations := all_violations

aism_score := score {
    satisfied := [1 | invariant_1_authenticated_borders] |
                 [1 | invariant_2_monotonic_scope] |
                 [1 | invariant_3_memory_provenance] |
                 [1 | invariant_4_kill_switch] |
                 [1 | invariant_5_owner_of_record] |
                 [1 | invariant_6_bias_observable]
    score := count(satisfied) / 6
}

aism_verdict := "allow" { count(all_violations) == 0 }
aism_verdict := "deny" { count(all_violations) > 0 }

aism_deny_reasons := [msg | msg := all_violations[_]]
