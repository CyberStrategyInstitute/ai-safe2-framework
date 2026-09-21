# nexus-apay.rego
# NEXUS CP.5.APAY - Agentic Payments Integrity Profile
# Cyber Strategy Institute | AI SAFE2 v3.1 | NEXUS-A2A v0.4
#
# Deploy: opa run --server --bundle ./opa/
# Query:  POST http://localhost:8181/v1/data/nexus/apay/decision
#
# This policy runs OUTSIDE the agent process and OUTSIDE the model. A language
# model never participates in a payment authorization decision. The Python
# TransactionFirewall and this policy implement the same rule set; deployments
# run one, the other, or both, and the reason codes are identical so evidence
# is comparable across enforcement points.
#
# DEFAULT IS DENY. Every unknown resolves to deny or reconcile. There is no
# path through this policy that produces "allow" from missing input.

package nexus.apay

import future.keywords.in
import future.keywords.every

default decision := {"decision": "deny", "reason_codes": ["FAIL_CLOSED_DEFAULT"]}
default allow := false

# ---------------------------------------------------------------------------
# Decision assembly
# ---------------------------------------------------------------------------

decision := result {
	count(reason_codes) == 0
	result := {
		"decision": "allow",
		"reason_codes": [],
		"policy_id": policy_id,
		"consequence": consequence_class,
	}
}

decision := result {
	count(reason_codes) > 0
	result := {
		"decision": verdict_kind,
		"reason_codes": reason_codes,
		"policy_id": policy_id,
		"consequence": consequence_class,
	}
}

allow {
	count(reason_codes) == 0
}

policy_id := pid {
	pid := object.get(input, "policy_id", "nexus-apay-v0.4")
}

# Ambiguous state is not a denial. Value must not move, but a human has to
# resolve it rather than the caller retrying into a duplicate settlement.
verdict_kind := "reconcile" {
	some code in reason_codes
	code in {"REVOCATION_STATUS_UNAVAILABLE", "SETTLEMENT_AMBIGUOUS"}
}

verdict_kind := "escalate" {
	reason_codes == ["HEAR_REQUIRED"]
}

verdict_kind := "deny" {
	not has_ambiguous
	reason_codes != ["HEAR_REQUIRED"]
}

has_ambiguous {
	some code in reason_codes
	code in {"REVOCATION_STATUS_UNAVAILABLE", "SETTLEMENT_AMBIGUOUS"}
}

reason_codes := sort([code | some code in all_violations])

all_violations[code] {
	some code in lifecycle_violations
}

all_violations[code] {
	some code in identity_violations
}

all_violations[code] {
	some code in runtime_violations
}

all_violations[code] {
	some code in constraint_violations
}

all_violations[code] {
	some code in continuity_violations
}

all_violations[code] {
	some code in economic_violations
}

all_violations[code] {
	some code in path_violations
}

all_violations[code] {
	some code in human_violations
}

# ---------------------------------------------------------------------------
# APAY-01: principal and owner binding
# ---------------------------------------------------------------------------

identity_violations["NO_PRINCIPAL_BINDING"] {
	not input.principal.principal_id
}

identity_violations["NO_OWNER_OF_RECORD"] {
	not input.principal.owner_of_record
}

# APAY-07: separation of duties. The capability being exercised must be one the
# grant actually carries. A grant that can buy cannot therefore refund.
identity_violations["SEPARATION_OF_DUTIES_VIOLATION"] {
	caps := object.get(input.grant, "capabilities", [])
	not input.transaction.capability in caps
}

# ---------------------------------------------------------------------------
# Lifecycle and revocation (APAY-13)
# ---------------------------------------------------------------------------

lifecycle_violations["GRANT_NOT_FOUND"] {
	not input.grant
}

lifecycle_violations["GRANT_REVOKED"] {
	input.grant.revoked == true
}

lifecycle_violations["STALE_REVOCATION_EPOCH"] {
	input.grant.revocation_epoch < input.revocation.current_epoch
}

# Unknown revocation status is never treated as live authority.
lifecycle_violations["REVOCATION_STATUS_UNAVAILABLE"] {
	input.revocation.available == false
}

lifecycle_violations["REVOCATION_STATUS_UNAVAILABLE"] {
	not input.revocation
}

lifecycle_violations["REVOCATION_STATUS_UNAVAILABLE"] {
	input.revocation.available == true
	not input.revocation.current_epoch
}

lifecycle_violations["GRANT_EXPIRED"] {
	input.grant.constraints.not_after
	time.parse_rfc3339_ns(input.now) > time.parse_rfc3339_ns(input.grant.constraints.not_after)
}

# APAY-03: a grant carrying unresolved constraint ambiguity cannot spend.
lifecycle_violations["UNRESOLVED_AMBIGUITY"] {
	count(object.get(input.grant, "unresolved_ambiguities", [])) > 0
}

# APAY-08: lineage must be monotonic. The caller supplies the re-derived
# attenuation result; a non-empty list is an escalation.
lifecycle_violations["ATTENUATION_VIOLATION"] {
	count(object.get(input, "attenuation_violations", [])) > 0
}

lifecycle_violations["DELEGATION_DEPTH_EXCEEDED"] {
	input.grant.constraints.max_delegation_depth < 0
}

# ---------------------------------------------------------------------------
# APAY-05: runtime-bound authorization
# ---------------------------------------------------------------------------

runtime_required {
	input.grant.constraints.min_assurance >= 4
}

runtime_violations["NO_RUNTIME_MEASUREMENT"] {
	runtime_required
	not input.runtime
}

runtime_violations["RUNTIME_NOT_ATTESTED"] {
	runtime_required
	input.runtime
	not input.runtime.attested
}

runtime_violations["RUNTIME_NOT_ATTESTED"] {
	runtime_required
	input.runtime.attestation_method in {"none", "declared"}
}

runtime_violations["RUNTIME_MEASUREMENT_STALE"] {
	runtime_required
	input.runtime.age_seconds > input.runtime.max_age_seconds
}

runtime_violations["RUNTIME_BASELINE_MISMATCH"] {
	runtime_required
	input.expected_runtime_baseline
	input.runtime.baseline_digest != input.expected_runtime_baseline
}

# ---------------------------------------------------------------------------
# APAY-04: deterministic constraint evaluation
# ---------------------------------------------------------------------------

tx := input.transaction

cons := input.grant.constraints

constraint_violations["AMOUNT_EXCEEDS_GRANT"] {
	cons.max_transaction
	cons.max_transaction.currency == tx.amount.currency
	tx.amount.minor_units > cons.max_transaction.minor_units
}

constraint_violations["CURRENCY_NOT_PERMITTED"] {
	cons.currencies
	not tx.amount.currency in cons.currencies
}

constraint_violations["CURRENCY_NOT_PERMITTED"] {
	cons.max_transaction
	cons.max_transaction.currency != tx.amount.currency
}

constraint_violations["MERCHANT_NOT_PERMITTED"] {
	tx.merchant_id in object.get(cons, "denied_merchants", [])
}

constraint_violations["MERCHANT_NOT_PERMITTED"] {
	cons.allowed_merchants
	not tx.merchant_id in cons.allowed_merchants
}

constraint_violations["CATEGORY_NOT_PERMITTED"] {
	cons.allowed_categories
	not tx.category in cons.allowed_categories
}

constraint_violations["GEOGRAPHY_NOT_PERMITTED"] {
	cons.allowed_geographies
	not tx.geography in cons.allowed_geographies
}

constraint_violations["RAIL_NOT_PERMITTED"] {
	cons.allowed_rails
	not tx.rail in cons.allowed_rails
}

constraint_violations["RAIL_NOT_PERMITTED"] {
	finality_rank[tx.finality] > finality_rank[cons.max_finality]
}

constraint_violations["RECURRENCE_NOT_PERMITTED"] {
	tx.recurring == true
	cons.recurrence_allowed == false
}

# An unconstrained destination on an irreversible rail is not a permission,
# it is an unbounded liability. Missing destination is a violation, not a skip.
constraint_violations["DESTINATION_SUBSTITUTED"] {
	cons.allowed_destinations
	not tx.destination in cons.allowed_destinations
}

constraint_violations["FACILITATOR_NOT_TRUSTED"] {
	cons.allowed_facilitators
	not tx.facilitator in cons.allowed_facilitators
}

finality_rank := {"reversible": 0, "mediated": 1, "irreversible": 2}

# ---------------------------------------------------------------------------
# APAY-11 / APAY-12: freshness, replay, continuity
# ---------------------------------------------------------------------------

continuity_violations["NONCE_MISSING"] {
	not tx.nonce
}

continuity_violations["REPLAY_DETECTED"] {
	tx.nonce in object.get(input, "seen_nonces", [])
}

continuity_violations["REPLAY_DETECTED"] {
	prior := object.get(input, "idempotency_digest", null)
	prior != null
	prior != tx.canonical_digest
}

continuity_violations["QUOTE_EXPIRED"] {
	tx.quote_expires_at
	time.parse_rfc3339_ns(input.now) > time.parse_rfc3339_ns(tx.quote_expires_at)
}

continuity_violations["INTENT_BINDING_MISSING"] {
	not tx.approved_cart_digest
}

continuity_violations["CART_MUTATED_AFTER_APPROVAL"] {
	tx.approved_cart_digest
	tx.approved_cart_digest != tx.canonical_digest
}

# APAY-15: counterparty provenance
continuity_violations["COUNTERPARTY_UNVERIFIED"] {
	not tx.merchant_verified
}

continuity_violations["COUNTERPARTY_UNVERIFIED"] {
	baseline := object.get(input, "merchant_baseline", null)
	baseline != null
	tx.merchant_baseline_digest != baseline
}

# ---------------------------------------------------------------------------
# APAY-09 / APAY-10: economic containment
# ---------------------------------------------------------------------------

# Exposure is supplied by the authority graph as the committed spend of the
# grant AND every descendant. Evaluating a transaction against its own limit
# alone is the failure this control exists to prevent.
economic_violations["AGGREGATE_CEILING_EXCEEDED"] {
	cons.max_aggregate
	cons.max_aggregate.currency == tx.amount.currency
	committed := object.get(input.exposure, "subtree_committed_minor_units", 0)
	committed + tx.amount.minor_units > cons.max_aggregate.minor_units
}

economic_violations["WINDOW_CEILING_EXCEEDED"] {
	cons.window_max
	cons.window_seconds
	cons.window_max.currency == tx.amount.currency
	windowed := object.get(input.exposure, "window_committed_minor_units", 0)
	windowed + tx.amount.minor_units > cons.window_max.minor_units
}

economic_violations["TRANSACTION_COUNT_EXCEEDED"] {
	cons.max_transactions
	object.get(input.exposure, "subtree_transaction_count", 0) + 1 > cons.max_transactions
}

economic_violations["VELOCITY_ANOMALY"] {
	object.get(input.velocity, "window_transaction_count", 0) + 1 > object.get(input.velocity, "max_transactions_per_window", 20)
}

economic_violations["MERCHANT_DISPERSION_ANOMALY"] {
	object.get(input.velocity, "distinct_merchants_in_window", 0) > object.get(input.velocity, "max_distinct_merchants", 8)
}

economic_violations["MICRO_DRAIN_SUSPECTED"] {
	object.get(input.velocity, "sub_threshold_count", 0) >= object.get(input.velocity, "micro_drain_count", 10)
}

economic_violations["SPLIT_TRANSACTION_SUSPECTED"] {
	object.get(input.velocity, "near_limit_same_merchant_count", 0) >= object.get(input.velocity, "split_count", 3)
}

# ---------------------------------------------------------------------------
# APAY-14: downgrade resistance
# ---------------------------------------------------------------------------

path_violations["ASSURANCE_DOWNGRADE"] {
	tx.path_assurance < cons.min_assurance
}

# ---------------------------------------------------------------------------
# APAY-01 / CP.10: human authority
# ---------------------------------------------------------------------------

consequence_class := "critical" {
	tx.finality == "irreversible"
	novel_destination
}

consequence_class := "consequential" {
	tx.finality == "irreversible"
	not novel_destination
}

consequence_class := "material" {
	tx.finality == "mediated"
}

consequence_class := "material" {
	tx.finality == "reversible"
	novel_destination
}

consequence_class := "routine" {
	tx.finality == "reversible"
	not novel_destination
}

novel_destination {
	tx.destination
	not tx.destination in object.get(input, "known_destinations", [])
}

hear_required {
	consequence_class in {"consequential", "critical"}
}

hear_required {
	cons.hear_above
	cons.hear_above.currency == tx.amount.currency
	tx.amount.minor_units >= cons.hear_above.minor_units
}

human_violations["HEAR_REQUIRED"] {
	hear_required
	not input.hear_satisfied_by
}

# ---------------------------------------------------------------------------
# Credential release gate (APAY-06)
# ---------------------------------------------------------------------------
# Queried separately, immediately before the credential broker is invoked.
# Re-reads the revocation epoch so a decision made microseconds earlier does
# not survive a kill switch that fired in between.

default release_credential := false

release_credential {
	allow
	input.grant.revocation_epoch >= input.revocation.current_epoch
	input.revocation.available == true
	input.runtime.runtime_measurement_id != ""
}
