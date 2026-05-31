# nexus-aism-invariants.rego
# NEXUS AISM (AI Sovereignty Measurement) Invariants
# Cyber Strategy Institute | AI SAFE2 v3.0 | NEXUS-A2A v0.3
#
# Six minimum viable architecture invariants for any enterprise operating
# more than 50 autonomous agents. These are NOT optional policies --
# they are architectural preconditions for sovereign agentic operation.
#
# Deploy alongside nexus-authz.rego:
#   opa run --server --bundle ./opa/
#
# Query individual invariants:
#   POST http://localhost:8181/v1/data/nexus/aism/invariants_satisfied
#   POST http://localhost:8181/v1/data/nexus/aism/invariant_violations
#
# Export as ACS Guardian policy templates:
#   Use with NEXUS-ACS Bridge Specification v0.1
#   Any ACS-compatible Guardian can load these as policy rules.
#
# Reference: NEXUS-A2A Specification v0.3, Part IV -- AISM Invariants
# SAFE2 mapping: CP.4 (Agentic Control Plane), CP.7 (Swarm Defense),
#                CP.9 (Agent Replication Governance), CP.10 (HEAR Doctrine)

package nexus.aism

import future.keywords.in
import future.keywords.every

# ---------------------------------------------------------------------------
# INVARIANT I-1: AUTHENTICATED BORDERS
#
# Every agent-to-agent communication boundary must carry cryptographically
# verified identity. Bare string IDs, bearer tokens without binding, and
# trust-on-first-use authentication all violate this invariant.
#
# SAFE2 control: S1.1 (Zero Trust Transport), CP.4 (Agentic Control Plane)
# ACS mapping: steps/agentTrigger -- agent.id must reference a verified DID
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
    msg := "I-1 VIOLATED: agent.did absent -- communication boundary is unauthenticated"
}

violation_i1[msg] {
    input.agent.did != ""
    not startswith(input.agent.did, "did:")
    msg := concat("", ["I-1 VIOLATED: malformed DID -- must start with 'did:' -- got: ", input.agent.did])
}

violation_i1[msg] {
    not input.agent.spiffe_id
    msg := "I-1 VIOLATED: agent.spiffe_id absent -- workload attestation missing"
}

violation_i1[msg] {
    input.agent.spiffe_id != ""
    not startswith(input.agent.spiffe_id, "spiffe://")
    msg := "I-1 VIOLATED: malformed SPIFFE ID -- must start with 'spiffe://'"
}


# ---------------------------------------------------------------------------
# INVARIANT I-2: MONOTONICALLY NARROWING SCOPE
#
# Permission scope narrows at every delegation hop. A sub-agent can never
# hold a superset of its principal's scope. Scope amplification at any
# delegation edge is a critical violation.
#
# SAFE2 control: S1.2 (Capability Containment), F3.2 (Delegation Limits)
# ACS mapping: steps/toolCallRequest -- action.method must be in vcc.granted_scopes
# ---------------------------------------------------------------------------

default invariant_2_monotonic_scope = false

invariant_2_monotonic_scope {
    # scope_depth 0 = root agent, no parent to check
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
    msg := concat("", ["I-2 VIOLATED: scope amplification at delegation depth ",
                       format_int(input.delegation.depth, 10),
                       " -- '", scope, "' not in parent grant"])
}

violation_i2[msg] {
    input.delegation.depth > 4
    msg := concat("", ["I-2 VIOLATED: delegation depth ", format_int(input.delegation.depth, 10),
                       " exceeds maximum of 4 -- unbounded delegation chain"])
}


# ---------------------------------------------------------------------------
# INVARIANT I-3: MEMORY PROVENANCE
#
# Every cross-session and permanent memory write must carry a cryptographic
# provenance record: source DID, timestamp, zone classification, and
# embedding hash. Memory with no provenance is treated as an injection
# attempt.
#
# SAFE2 control: S1.5 (Memory Governance), A2.3 (Provenance Chain)
# ACS mapping: steps/memoryStore -- nexus_extension.provenance must be present
# ---------------------------------------------------------------------------

default invariant_3_memory_provenance = false

# Session-scoped writes are exempt from cross-session provenance requirement
invariant_3_memory_provenance {
    input.memory.zone == "SESSION"
}

invariant_3_memory_provenance {
    input.memory.zone != "SESSION"
    input.memory.provenance.source_did != ""
    input.memory.provenance.timestamp_utc != ""
    input.memory.provenance.embedding_hash != ""
    input.memory.provenance.zone_class != ""
}

violation_i3[msg] {
    input.memory.zone != "SESSION"
    not input.memory.provenance.source_did
    msg := concat("", ["I-3 VIOLATED: ", input.memory.zone,
                       " memory write has no source_did provenance"])
}

violation_i3[msg] {
    input.memory.zone != "SESSION"
    not input.memory.provenance.embedding_hash
    msg := concat("", ["I-3 VIOLATED: ", input.memory.zone,
                       " memory write has no embedding_hash -- drift detection disabled"])
}

violation_i3[msg] {
    input.memory.zone in {"CROSS_SESSION", "PERMANENT", "SWARM_SHARED"}
    input.memory.drift_score > 0.3
    msg := concat("", ["I-3 VIOLATED: memory drift score ",
                       sprintf("%.3f", [input.memory.drift_score]),
                       " exceeds 0.3 hard brake -- possible belief poisoning"])
}


# ---------------------------------------------------------------------------
# INVARIANT I-4: PHYSICAL KILL SWITCH
#
# Every autonomous agent operating at ACT-2 or above must have a designated
# kill switch pathway: operator-level, domain-level, or principal-level.
# Agents with no registered kill switch pathway cannot be granted ACT-2+
# capabilities.
#
# SAFE2 control: F3.1 (Emergency Stop), CP.10 (HEAR Doctrine)
# ACS mapping: steps/agentTrigger -- act_tier >= 2 requires kill_switch_registered
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
    msg := concat("", ["I-4 VIOLATED: ACT-", format_int(input.agent.act_tier, 10),
                       " agent '", input.agent.did,
                       "' has no registered kill switch pathway -- HEAR Doctrine requires kill switch for ACT-2+"])
}

violation_i4[msg] {
    input.agent.act_tier >= 4
    not input.agent.kill_switch.cryptographic_kill_confirmed
    msg := concat("", ["I-4 VIOLATED: ACT-4 agent '", input.agent.did,
                       "' must have cryptographic (not procedural) kill switch -- 500ms propagation required"])
}


# ---------------------------------------------------------------------------
# INVARIANT I-5: OWNER OF RECORD
#
# Every deployed agent must have a registered human owner-of-record (OOR):
# a natural person accountable for the agent's actions under EU AI Act
# Article 14 and NIST AI RMF accountability requirements.
# No owner-of-record = no authorization to deploy.
#
# SAFE2 control: A2.1 (Asset Inventory), CP.4 (Agentic Control Plane)
# ACS mapping: steps/agentTrigger -- agent.aim must contain oor_contact
# ---------------------------------------------------------------------------

default invariant_5_owner_of_record = false

invariant_5_owner_of_record {
    input.agent.aim.oor_contact != ""
    input.agent.aim.oor_designation_date != ""
    input.agent.aim.oor_hear_acknowledged == true
}

violation_i5[msg] {
    not input.agent.aim.oor_contact
    msg := concat("", ["I-5 VIOLATED: agent '", input.agent.did,
                       "' has no owner-of-record -- EU AI Act Article 14 requires human accountability"])
}

violation_i5[msg] {
    input.agent.aim.oor_contact != ""
    not input.agent.aim.oor_hear_acknowledged
    msg := concat("", ["I-5 VIOLATED: owner-of-record for '", input.agent.did,
                       "' has not acknowledged HEAR Doctrine responsibilities"])
}

violation_i5[msg] {
    input.agent.act_tier >= 3
    not input.agent.aim.oor_escalation_contact
    msg := concat("", ["I-5 VIOLATED: ACT-3+ agent '", input.agent.did,
                       "' requires escalation contact in addition to primary OOR"])
}


# ---------------------------------------------------------------------------
# INVARIANT I-6: BIAS AS SECURITY OBSERVABLE
#
# Behavioral drift, capability boundary creep, and goal misalignment are
# treated as security events, not performance metrics. Any agent exhibiting
# drift above threshold triggers a mandatory incident report.
# This is not optional monitoring -- it is a security control.
#
# SAFE2 control: M4.8 (Bias as Security Observable), A2.5 (NOR Execution Trace)
# ACS mapping: steps/toolCallRequest -- nexus_extension.drift_score monitored
# ---------------------------------------------------------------------------

default invariant_6_bias_observable = false

invariant_6_bias_observable {
    # No drift data means no persistent memory -- acceptable for stateless agents
    not input.behavioral_metrics
}

invariant_6_bias_observable {
    input.behavioral_metrics.capability_drift_score <= 0.25
    input.behavioral_metrics.goal_alignment_score >= 0.75
    input.behavioral_metrics.nor_coverage_pct >= 80
}

violation_i6[msg] {
    input.behavioral_metrics.capability_drift_score > 0.25
    msg := concat("", ["I-6 VIOLATED: capability drift score ",
                       sprintf("%.3f", [input.behavioral_metrics.capability_drift_score]),
                       " exceeds 0.25 threshold -- mandatory incident report required"])
}

violation_i6[msg] {
    input.behavioral_metrics.goal_alignment_score < 0.75
    msg := concat("", ["I-6 VIOLATED: goal alignment score ",
                       sprintf("%.3f", [input.behavioral_metrics.goal_alignment_score]),
                       " below 0.75 floor -- agent purpose drift detected"])
}

violation_i6[msg] {
    input.behavioral_metrics.nor_coverage_pct < 80
    msg := concat("", ["I-6 VIOLATED: NOR coverage at ",
                       sprintf("%.1f", [input.behavioral_metrics.nor_coverage_pct]),
                       "% -- minimum 80% required for bias-as-security-observable enforcement"])
}


# ---------------------------------------------------------------------------
# AGGREGATE: INVARIANTS SATISFIED + VIOLATION REPORT
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

# AISM score: fraction of invariants satisfied (0.0 to 1.0)
aism_score := score {
    satisfied := [1 | invariant_1_authenticated_borders] |
                 [1 | invariant_2_monotonic_scope] |
                 [1 | invariant_3_memory_provenance] |
                 [1 | invariant_4_kill_switch] |
                 [1 | invariant_5_owner_of_record] |
                 [1 | invariant_6_bias_observable]
    score := count(satisfied) / 6
}

# Guardian-compatible verdict: deny if any invariant violated
aism_verdict := "allow" { count(all_violations) == 0 }
aism_verdict := "deny" { count(all_violations) > 0 }

aism_deny_reasons := [msg | msg := all_violations[_]]
