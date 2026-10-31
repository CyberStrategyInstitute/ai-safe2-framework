# nexus-apay.rego
# NEXUS CP.5.APAY - Agentic Payments Integrity Profile
# Cyber Strategy Institute | AI SAFE2 v3.1 | NEXUS v0.6.0 | CP.5.APAY/0.4
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

import rego.v1

default decision := {"decision": "deny", "reason_codes": ["FAIL_CLOSED_DEFAULT"]}

default allow := false

# ---------------------------------------------------------------------------
# Decision assembly
# ---------------------------------------------------------------------------

decision := result if {
	count(reason_codes) == 0
	result := {
		"decision": "allow",
		"reason_codes": [],
		"policy_id": policy_id,
		"consequence": consequence_class,
	}
}

decision := result if {
	count(reason_codes) > 0
	result := {
		"decision": verdict_kind,
		"reason_codes": reason_codes,
		"policy_id": policy_id,
		"consequence": consequence_class,
	}
}

allow if {
	count(reason_codes) == 0
}

policy_id := pid if {
	pid := object.get(input, "policy_id", "nexus-apay-v0.4")
}

# Ambiguous state is not a denial. Value must not move, but a human has to
# resolve it rather than the caller retrying into a duplicate settlement.
verdict_kind := "reconcile" if {
	some code in reason_codes
	code in {"REVOCATION_STATUS_UNAVAILABLE", "SETTLEMENT_AMBIGUOUS"}
}

verdict_kind := "escalate" if {
	reason_codes == ["HEAR_REQUIRED"]
}

verdict_kind := "deny" if {
	not has_ambiguous
	reason_codes != ["HEAR_REQUIRED"]
}

has_ambiguous if {
	some code in reason_codes
	code in {"REVOCATION_STATUS_UNAVAILABLE", "SETTLEMENT_AMBIGUOUS"}
}

reason_codes := sort([code | some code in all_violations])

all_violations contains code if {
	some code in lifecycle_violations
}

all_violations contains code if {
	some code in identity_violations
}

all_violations contains code if {
	some code in runtime_violations
}

all_violations contains code if {
	some code in constraint_violations
}

all_violations contains code if {
	some code in continuity_violations
}

all_violations contains code if {
	some code in economic_violations
}

all_violations contains code if {
	some code in path_violations
}

all_violations contains code if {
	some code in human_violations
}

# ---------------------------------------------------------------------------
# APAY-01: principal and owner binding
# ---------------------------------------------------------------------------

identity_violations contains "NO_PRINCIPAL_BINDING" if {
	not input.principal.principal_id
}

identity_violations contains "NO_OWNER_OF_RECORD" if {
	not input.principal.owner_of_record
}

# APAY-07: separation of duties. The capability being exercised must be one the
# grant actually carries. A grant that can buy cannot therefore refund.
identity_violations contains "SEPARATION_OF_DUTIES_VIOLATION" if {
	caps := object.get(input.grant, "capabilities", [])
	not input.transaction.capability in caps
}

# ---------------------------------------------------------------------------
# Lifecycle and revocation (APAY-13)
# ---------------------------------------------------------------------------

lifecycle_violations contains "GRANT_NOT_FOUND" if {
	not input.grant
}

lifecycle_violations contains "GRANT_REVOKED" if {
	input.grant.revoked == true
}

lifecycle_violations contains "STALE_REVOCATION_EPOCH" if {
	input.grant.revocation_epoch < input.revocation.current_epoch
}

# Unknown revocation status is never treated as live authority.
lifecycle_violations contains "REVOCATION_STATUS_UNAVAILABLE" if {
	input.revocation.available == false
}

lifecycle_violations contains "REVOCATION_STATUS_UNAVAILABLE" if {
	not input.revocation
}

lifecycle_violations contains "REVOCATION_STATUS_UNAVAILABLE" if {
	input.revocation.available == true
	not input.revocation.current_epoch
}

lifecycle_violations contains "GRANT_EXPIRED" if {
	input.grant.constraints.not_after
	time.parse_rfc3339_ns(input.now) > time.parse_rfc3339_ns(input.grant.constraints.not_after)
}

# APAY-03: a grant carrying unresolved constraint ambiguity cannot spend.
lifecycle_violations contains "UNRESOLVED_AMBIGUITY" if {
	count(object.get(input.grant, "unresolved_ambiguities", [])) > 0
}

# APAY-08: lineage must be monotonic. The caller supplies the re-derived
# attenuation result; a non-empty list is an escalation.
lifecycle_violations contains "ATTENUATION_VIOLATION" if {
	count(object.get(input, "attenuation_violations", [])) > 0
}

lifecycle_violations contains "DELEGATION_DEPTH_EXCEEDED" if {
	input.grant.constraints.max_delegation_depth < 0
}

# ---------------------------------------------------------------------------
# APAY-05: runtime-bound authorization
# ---------------------------------------------------------------------------

runtime_required if {
	input.grant.constraints.min_assurance >= 4
}

runtime_violations contains "NO_RUNTIME_MEASUREMENT" if {
	runtime_required
	not input.runtime
}

runtime_violations contains "RUNTIME_NOT_ATTESTED" if {
	runtime_required
	input.runtime
	not input.runtime.attested
}

runtime_violations contains "RUNTIME_NOT_ATTESTED" if {
	runtime_required
	input.runtime.attestation_method in {"none", "declared"}
}

runtime_violations contains "RUNTIME_MEASUREMENT_STALE" if {
	runtime_required
	input.runtime.age_seconds > input.runtime.max_age_seconds
}

runtime_violations contains "RUNTIME_BASELINE_MISMATCH" if {
	runtime_required
	input.expected_runtime_baseline
	input.runtime.baseline_digest != input.expected_runtime_baseline
}

# ---------------------------------------------------------------------------
# APAY-04: deterministic constraint evaluation
# ---------------------------------------------------------------------------

tx := input.transaction

cons := input.grant.constraints

constraint_violations contains "AMOUNT_EXCEEDS_GRANT" if {
	cons.max_transaction
	cons.max_transaction.currency == tx.amount.currency
	tx.amount.minor_units > cons.max_transaction.minor_units
}

constraint_violations contains "CURRENCY_NOT_PERMITTED" if {
	cons.currencies
	not tx.amount.currency in cons.currencies
}

constraint_violations contains "CURRENCY_NOT_PERMITTED" if {
	cons.max_transaction
	cons.max_transaction.currency != tx.amount.currency
}

constraint_violations contains "MERCHANT_NOT_PERMITTED" if {
	tx.merchant_id in object.get(cons, "denied_merchants", [])
}

constraint_violations contains "MERCHANT_NOT_PERMITTED" if {
	cons.allowed_merchants
	not tx.merchant_id in cons.allowed_merchants
}

constraint_violations contains "CATEGORY_NOT_PERMITTED" if {
	cons.allowed_categories
	not tx.category in cons.allowed_categories
}

constraint_violations contains "GEOGRAPHY_NOT_PERMITTED" if {
	cons.allowed_geographies
	not tx.geography in cons.allowed_geographies
}

constraint_violations contains "RAIL_NOT_PERMITTED" if {
	cons.allowed_rails
	not tx.rail in cons.allowed_rails
}

constraint_violations contains "RAIL_NOT_PERMITTED" if {
	finality_rank[tx.finality] > finality_rank[cons.max_finality]
}

constraint_violations contains "RECURRENCE_NOT_PERMITTED" if {
	tx.recurring == true
	cons.recurrence_allowed == false
}

# An unconstrained destination on an irreversible rail is not a permission,
# it is an unbounded liability. Missing destination is a violation, not a skip.
constraint_violations contains "DESTINATION_SUBSTITUTED" if {
	cons.allowed_destinations
	not tx.destination in cons.allowed_destinations
}

constraint_violations contains "FACILITATOR_NOT_TRUSTED" if {
	cons.allowed_facilitators
	not tx.facilitator in cons.allowed_facilitators
}

finality_rank := {"reversible": 0, "mediated": 1, "irreversible": 2}

# ---------------------------------------------------------------------------
# APAY-11 / APAY-12: freshness, replay, continuity
# ---------------------------------------------------------------------------

continuity_violations contains "NONCE_MISSING" if {
	not tx.nonce
}

continuity_violations contains "REPLAY_DETECTED" if {
	tx.nonce in object.get(input, "seen_nonces", [])
}

continuity_violations contains "REPLAY_DETECTED" if {
	prior := object.get(input, "idempotency_digest", null)
	prior != null
	prior != tx.canonical_digest
}

continuity_violations contains "QUOTE_EXPIRED" if {
	tx.quote_expires_at
	time.parse_rfc3339_ns(input.now) > time.parse_rfc3339_ns(tx.quote_expires_at)
}

continuity_violations contains "INTENT_BINDING_MISSING" if {
	not tx.approved_cart_digest
}

continuity_violations contains "CART_MUTATED_AFTER_APPROVAL" if {
	tx.approved_cart_digest
	tx.approved_cart_digest != tx.canonical_digest
}

# APAY-15: counterparty provenance
continuity_violations contains "COUNTERPARTY_UNVERIFIED" if {
	not tx.merchant_verified
}

continuity_violations contains "COUNTERPARTY_UNVERIFIED" if {
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
economic_violations contains "AGGREGATE_CEILING_EXCEEDED" if {
	cons.max_aggregate
	cons.max_aggregate.currency == tx.amount.currency
	committed := object.get(input.exposure, "subtree_committed_minor_units", 0)
	committed + tx.amount.minor_units > cons.max_aggregate.minor_units
}

economic_violations contains "WINDOW_CEILING_EXCEEDED" if {
	cons.window_max
	cons.window_seconds
	cons.window_max.currency == tx.amount.currency
	windowed := object.get(input.exposure, "window_committed_minor_units", 0)
	windowed + tx.amount.minor_units > cons.window_max.minor_units
}

economic_violations contains "TRANSACTION_COUNT_EXCEEDED" if {
	cons.max_transactions
	object.get(input.exposure, "subtree_transaction_count", 0) + 1 > cons.max_transactions
}

economic_violations contains "VELOCITY_ANOMALY" if {
	object.get(input.velocity, "window_transaction_count", 0) + 1 > object.get(input.velocity, "max_transactions_per_window", 20)
}

economic_violations contains "MERCHANT_DISPERSION_ANOMALY" if {
	object.get(input.velocity, "distinct_merchants_in_window", 0) > object.get(input.velocity, "max_distinct_merchants", 8)
}

economic_violations contains "MICRO_DRAIN_SUSPECTED" if {
	object.get(input.velocity, "sub_threshold_count", 0) >= object.get(input.velocity, "micro_drain_count", 10)
}

economic_violations contains "SPLIT_TRANSACTION_SUSPECTED" if {
	object.get(input.velocity, "near_limit_same_merchant_count", 0) >= object.get(input.velocity, "split_count", 3)
}

# ---------------------------------------------------------------------------
# APAY-14: downgrade resistance
# ---------------------------------------------------------------------------

path_violations contains "ASSURANCE_DOWNGRADE" if {
	tx.path_assurance < cons.min_assurance
}

# ---------------------------------------------------------------------------
# APAY-01 / CP.10: human authority
# ---------------------------------------------------------------------------

consequence_class := "critical" if {
	tx.finality == "irreversible"
	novel_destination
}

consequence_class := "consequential" if {
	tx.finality == "irreversible"
	not novel_destination
}

consequence_class := "material" if {
	tx.finality == "mediated"
}

consequence_class := "material" if {
	tx.finality == "reversible"
	novel_destination
}

consequence_class := "routine" if {
	tx.finality == "reversible"
	not novel_destination
}

novel_destination if {
	tx.destination
	not tx.destination in object.get(input, "known_destinations", [])
}

hear_required if {
	consequence_class in {"consequential", "critical"}
}

hear_required if {
	cons.hear_above
	cons.hear_above.currency == tx.amount.currency
	tx.amount.minor_units >= cons.hear_above.minor_units
}

human_violations contains "HEAR_REQUIRED" if {
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

release_credential if {
	allow
	input.grant.revocation_epoch >= input.revocation.current_epoch
	input.revocation.available == true
	input.runtime.runtime_measurement_id != ""
}

# ---------------------------------------------------------------------------
# Advisory evidence: Agency Check receipt (nexus-apay-acr/0.1)
# ---------------------------------------------------------------------------
# Spec: payments/AGENCY-CHECK-RECEIPT-EVIDENCE.md
#
# SHADOW ONLY. Nothing in this section is referenced by reason_codes, decision,
# allow or release_credential, so a payment decision is identical with and
# without a receipt, and the Policy Parity Guard is unaffected. Query
# /v1/data/nexus/apay/agency_check_advisory for the advisory.
#
# The receipt is verified OUTSIDE this policy (signature, hash, binding) by
# nexus_sdk.payments.agency_check; OPA cannot verify raw Ed25519. This section
# re-checks what it can independently: the bound transaction digest against
# this transaction, freshness against input.now, and that the check ran.
#
# A receipt is not an authorization. A "ready" card never satisfies HEAR and
# never removes a reason code. card_state is unsigned in Agency Check receipts,
# so it is reported as declared, never attested.

acr_profile := "nexus-apay-acr/0.1"

acr_max_age_seconds := 900

acr_max_future_skew_seconds := 60

acr := input.agency_check_evidence

acr_present if is_object(acr)

acr_authentic if {
	acr_present
	acr.profile == acr_profile
	acr.hash_verified == true
	acr.signature_verified == true
}

acr_bound if {
	acr.binding_verified == true
	acr.transaction_digest == tx.canonical_digest
}

acr_age_ns := time.parse_rfc3339_ns(input.now) - time.parse_rfc3339_ns(acr.issued_at)

acr_fresh if {
	acr_age_ns >= (0 - acr_max_future_skew_seconds) * 1000000000
	acr_age_ns <= acr_max_age_seconds * 1000000000
}

acr_check_ran if {
	acr.nor_outcome == "allow"
	acr.tool_name == "agency_check"
}

agency_check_status := "absent" if {
	not acr_present
} else := "invalid" if {
	not acr_authentic
} else := "unbound" if {
	not acr_bound
} else := "stale" if {
	not acr_fresh
} else := "check_not_run" if {
	not acr_check_ran
} else := state if {
	state := acr.card_state
	state in {"ready", "clarify", "pause"}
} else := "card_state_unknown"

agency_check_findings contains "ACR_ABSENT" if not acr_present

agency_check_findings contains "ACR_PROFILE_UNSUPPORTED" if {
	acr_present
	acr.profile != acr_profile
}

agency_check_findings contains "ACR_HASH_UNVERIFIED" if {
	acr_present
	not acr.hash_verified == true
}

agency_check_findings contains "ACR_SIGNATURE_UNVERIFIED" if {
	acr_present
	not acr.signature_verified == true
}

agency_check_findings contains "ACR_BINDING_MISMATCH" if {
	acr_present
	not acr_bound
}

agency_check_findings contains "ACR_NOT_FRESH" if {
	acr_present
	not acr_fresh
}

agency_check_findings contains "ACR_FUTURE_DATED" if {
	acr_present
	acr_age_ns < (0 - acr_max_future_skew_seconds) * 1000000000
}

# The service refused to run the check. Signed: deny_reason is a NOR field.
agency_check_findings contains "ACR_CHECK_NOT_RUN" if {
	acr_present
	not acr_check_ran
}

agency_check_findings contains "ACR_SERVICE_PAUSED" if {
	acr_present
	acr.nor_outcome == "deny"
	acr.nor_deny_reason in {"kill_switch", "frozen"}
}

agency_check_findings contains "ACR_CARD_CLARIFY" if {
	acr_present
	acr.card_state == "clarify"
}

agency_check_findings contains "ACR_CARD_PAUSE" if {
	acr_present
	acr.card_state == "pause"
}

agency_check_findings contains "ACR_CARD_STATE_ABSENT" if {
	acr_present
	not acr.card_state in {"ready", "clarify", "pause"}
}

agency_check_findings contains "ACR_CARD_STATE_DECLARED" if {
	acr_present
	acr.card_state in {"ready", "clarify", "pause"}
}

# What a future enforce profile would do. Reported, never applied. Absence is
# not escalated under 0.1 because no grant constraint requires a check yet.
agency_check_shadow_effect := "none" if {
	agency_check_status in {"absent", "ready"}
} else := "would_escalate"

acr_receipt_id := object.get(acr, "receipt_id", null) if acr_present

default acr_receipt_id := null

agency_check_advisory := {
	"profile": acr_profile,
	"mode": "shadow",
	"enforced": false,
	"status": agency_check_status,
	"shadow_effect": agency_check_shadow_effect,
	"findings": sort([f | some f in agency_check_findings]),
	"card_state_attested": false,
	"receipt_id": acr_receipt_id,
}
