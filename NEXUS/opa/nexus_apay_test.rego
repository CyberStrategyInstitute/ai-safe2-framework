package nexus.apay_test

import rego.v1

import data.nexus.apay

# Clean, routine, fully evidenced transaction. Mirrors the sample document that
# nexus_sdk.payments.opa_input.build_opa_input emits in test_apay_opa_contract.py.
digest := "63ad84ea30f4cdbc30e8e8fefa68158d0bc7531a5b294845bc3dfa912dfbba22"

base := {
	"now": "2026-09-21T12:00:00+00:00",
	"policy_id": "nexus-apay-v0.4",
	"principal": {"principal_id": "principal-1", "owner_of_record": "owner@example.org"},
	"grant": {
		"revocation_epoch": 0,
		"revoked": false,
		"unresolved_ambiguities": [],
		"capabilities": ["payment.execute"],
		"constraints": {
			"max_transaction": {"minor_units": 50000, "currency": "USD"},
			"max_aggregate": {"minor_units": 200000, "currency": "USD"},
			"window_max": {"minor_units": 80000, "currency": "USD"},
			"window_seconds": 3600,
			"currencies": ["USD"],
			"allowed_merchants": ["merchant-a"],
			"denied_merchants": [],
			"allowed_categories": ["cloud"],
			"allowed_geographies": ["US"],
			"allowed_rails": ["card_network"],
			"allowed_facilitators": ["facilitator-1"],
			"allowed_destinations": ["acct-a"],
			"min_assurance": 4,
			"max_finality": "reversible",
			"recurrence_allowed": false,
			"max_transactions": 50,
			"max_delegation_depth": 2,
			"not_after": "2026-09-22T12:00:00+00:00",
			"hear_above": {"minor_units": 40000, "currency": "USD"},
		},
	},
	"transaction": {
		"amount": {"minor_units": 10000, "currency": "USD"},
		"merchant_id": "merchant-a",
		"merchant_verified": true,
		"merchant_baseline_digest": "sha256:baseline-a",
		"destination": "acct-a",
		"category": "cloud",
		"geography": "US",
		"rail": "card_network",
		"finality": "reversible",
		"facilitator": "facilitator-1",
		"path_assurance": 4,
		"recurring": false,
		"quote_expires_at": "2026-09-21T13:00:00+00:00",
		"nonce": "n-1",
		"approved_cart_digest": digest,
		"capability": "payment.execute",
		"canonical_digest": digest,
	},
	"runtime": {
		"runtime_measurement_id": "rtm_1",
		"attested": true,
		"attestation_method": "tdx",
		"baseline_digest": "rb-1",
		"max_age_seconds": 300,
		"age_seconds": 0,
	},
	"expected_runtime_baseline": "rb-1",
	"revocation": {"available": true, "current_epoch": 0},
	"attenuation_violations": [],
	"exposure": {"subtree_committed_minor_units": 0, "window_committed_minor_units": 0, "subtree_transaction_count": 0},
	"velocity": {
		"window_transaction_count": 0, "distinct_merchants_in_window": 1, "sub_threshold_count": 0,
		"near_limit_same_merchant_count": 0, "max_transactions_per_window": 20,
		"max_distinct_merchants": 8, "micro_drain_count": 10, "split_count": 3,
	},
	"seen_nonces": [],
	"idempotency_digest": null,
	"merchant_baseline": "sha256:baseline-a",
	"known_destinations": ["acct-a"],
	"hear_satisfied_by": null,
	"agency_check_evidence": null,
}

with_patch(patch) := object.union(base, patch)

# Intended HEAR behavior is exercised with the key omitted; see APAY-REGO-DEF-1.
unheard(doc) := object.remove(doc, ["hear_satisfied_by"])

codes(doc) := c if {
	c := apay.reason_codes with input as doc
}

verdict(doc) := v if {
	v := apay.decision.decision with input as doc
}

# ---------------------------------------------------------------------------
# Decision: existing behavior (characterization)
# ---------------------------------------------------------------------------

test_clean_routine_transaction_is_allowed if {
	d := apay.decision with input as base
	d.decision == "allow"
	d.reason_codes == []
	d.consequence == "routine"
	d.policy_id == "nexus-apay-v0.4"
	apay.allow with input as base
	apay.release_credential with input as base
}

test_empty_input_is_denied if {
	not apay.allow with input as {}
	verdict({}) == "deny"
	not apay.release_credential with input as {}
}

test_missing_principal_binding_denied if {
	doc := object.remove(base, ["principal"])
	{"NO_PRINCIPAL_BINDING", "NO_OWNER_OF_RECORD"} == {c | some c in codes(doc)}
	verdict(doc) == "deny"
}

test_capability_outside_grant_violates_separation_of_duties if {
	codes(with_patch({"transaction": {"capability": "payment.refund"}})) == ["SEPARATION_OF_DUTIES_VIOLATION"]
}

test_missing_grant_denied if {
	"GRANT_NOT_FOUND" in codes(object.remove(base, ["grant"]))
	not apay.allow with input as object.remove(base, ["grant"])
}

test_revoked_and_stale_grants_denied if {
	codes(with_patch({"grant": {"revoked": true}})) == ["GRANT_REVOKED"]
	"STALE_REVOCATION_EPOCH" in codes(with_patch({"revocation": {"current_epoch": 1}}))
}

test_unknown_revocation_status_reconciles if {
	verdict(with_patch({"revocation": {"available": false}})) == "reconcile"
	verdict(object.remove(base, ["revocation"])) == "reconcile"
	not apay.release_credential with input as with_patch({"revocation": {"available": false}})
}

test_ambiguity_outranks_other_violations if {
	doc := with_patch({"revocation": {"available": false}, "transaction": {"merchant_id": "merchant-z"}})
	verdict(doc) == "reconcile"
	"MERCHANT_NOT_PERMITTED" in codes(doc)
}

test_expired_grant_and_ambiguity_denied if {
	codes(with_patch({"now": "2026-09-23T00:00:00+00:00", "transaction": {"quote_expires_at": "2026-09-24T00:00:00+00:00"}})) == ["GRANT_EXPIRED"]
	codes(with_patch({"grant": {"unresolved_ambiguities": ["merchant scope"]}})) == ["UNRESOLVED_AMBIGUITY"]
	codes(with_patch({"attenuation_violations": ["widened"]})) == ["ATTENUATION_VIOLATION"]
}

test_constraint_violations if {
	codes(unheard(with_patch({"transaction": {"amount": {"minor_units": 50001}}}))) == ["AMOUNT_EXCEEDS_GRANT", "HEAR_REQUIRED"]
	"CURRENCY_NOT_PERMITTED" in codes(with_patch({"transaction": {"amount": {"currency": "EUR"}}}))
	codes(with_patch({"transaction": {"merchant_id": "merchant-z"}})) == ["MERCHANT_NOT_PERMITTED"]
	codes(with_patch({"grant": {"constraints": {"denied_merchants": ["merchant-a"]}}})) == ["MERCHANT_NOT_PERMITTED"]
	codes(with_patch({"transaction": {"category": "gambling"}})) == ["CATEGORY_NOT_PERMITTED"]
	codes(with_patch({"transaction": {"geography": "KP"}})) == ["GEOGRAPHY_NOT_PERMITTED"]
	codes(with_patch({"transaction": {"recurring": true}})) == ["RECURRENCE_NOT_PERMITTED"]
	codes(with_patch({"transaction": {"facilitator": "facilitator-x"}})) == ["FACILITATOR_NOT_TRUSTED"]
}

test_irreversible_rail_beyond_max_finality_denied if {
	doc := with_patch({"transaction": {"finality": "irreversible"}})
	"RAIL_NOT_PERMITTED" in codes(doc)
	verdict(doc) == "deny"
}

test_substituted_destination_denied if {
	doc := with_patch({"transaction": {"destination": "acct-attacker"}})
	"DESTINATION_SUBSTITUTED" in codes(doc)
	apay.consequence_class == "material" with input as doc
}

test_continuity_violations if {
	codes(json.remove(base, ["transaction/nonce"])) == ["NONCE_MISSING"]
	codes(with_patch({"seen_nonces": ["n-1"]})) == ["REPLAY_DETECTED"]
	codes(with_patch({"idempotency_digest": "other"})) == ["REPLAY_DETECTED"]
	codes(with_patch({"now": "2026-09-21T13:00:01+00:00"})) == ["QUOTE_EXPIRED"]
	codes(with_patch({"transaction": {"approved_cart_digest": "other"}})) == ["CART_MUTATED_AFTER_APPROVAL"]
	codes(json.remove(base, ["transaction/approved_cart_digest"])) == ["INTENT_BINDING_MISSING"]
	codes(with_patch({"transaction": {"merchant_verified": false}})) == ["COUNTERPARTY_UNVERIFIED"]
	codes(with_patch({"merchant_baseline": "sha256:baseline-b"})) == ["COUNTERPARTY_UNVERIFIED"]
}

test_economic_containment if {
	codes(with_patch({"exposure": {"subtree_committed_minor_units": 195000}})) == ["AGGREGATE_CEILING_EXCEEDED"]
	codes(with_patch({"exposure": {"window_committed_minor_units": 75000}})) == ["WINDOW_CEILING_EXCEEDED"]
	codes(with_patch({"exposure": {"subtree_transaction_count": 50}})) == ["TRANSACTION_COUNT_EXCEEDED"]
	codes(with_patch({"velocity": {"window_transaction_count": 20}})) == ["VELOCITY_ANOMALY"]
	codes(with_patch({"velocity": {"distinct_merchants_in_window": 9}})) == ["MERCHANT_DISPERSION_ANOMALY"]
	codes(with_patch({"velocity": {"sub_threshold_count": 10}})) == ["MICRO_DRAIN_SUSPECTED"]
	codes(with_patch({"velocity": {"near_limit_same_merchant_count": 3}})) == ["SPLIT_TRANSACTION_SUSPECTED"]
}

test_runtime_binding if {
	codes(object.remove(base, ["runtime"])) == ["NO_RUNTIME_MEASUREMENT"]
	codes(with_patch({"runtime": {"attested": false}})) == ["RUNTIME_NOT_ATTESTED"]
	codes(with_patch({"runtime": {"attestation_method": "declared"}})) == ["RUNTIME_NOT_ATTESTED"]
	codes(with_patch({"runtime": {"age_seconds": 301}})) == ["RUNTIME_MEASUREMENT_STALE"]
	codes(with_patch({"expected_runtime_baseline": "rb-2"})) == ["RUNTIME_BASELINE_MISMATCH"]
}

test_runtime_not_required_below_assurance_4 if {
	doc := with_patch({"runtime": null, "grant": {"constraints": {"min_assurance": 3}}})
	codes(doc) == []
	not apay.release_credential with input as doc
}

test_assurance_downgrade_denied if {
	codes(with_patch({"transaction": {"path_assurance": 3}})) == ["ASSURANCE_DOWNGRADE"]
}

test_hear_alone_escalates if {
	doc := unheard(with_patch({"transaction": {"amount": {"minor_units": 40000}}}))
	codes(doc) == ["HEAR_REQUIRED"]
	verdict(doc) == "escalate"
	verdict(with_patch({"transaction": {"amount": {"minor_units": 40000}}, "hear_satisfied_by": "hear-1"})) == "allow"
}

test_hear_with_another_violation_denies if {
	verdict(unheard(with_patch({"transaction": {"amount": {"minor_units": 40000}, "category": "gambling"}}))) == "deny"
}

critical_doc := with_patch({
	"grant": {"constraints": {"max_finality": "irreversible", "allowed_destinations": ["acct-a", "acct-new"]}},
	"transaction": {"finality": "irreversible", "destination": "acct-new"},
})

test_irreversible_novel_destination_is_critical if {
	doc := unheard(critical_doc)
	apay.consequence_class == "critical" with input as doc
	codes(doc) == ["HEAR_REQUIRED"]
	verdict(doc) == "escalate"
}

# ---------------------------------------------------------------------------
# Known policy defects (found by this suite; NOT fixed here)
# ---------------------------------------------------------------------------
# build_opa_input emits absent values as null, never omits them. Rules written as
# `not input.x` treat a present null as satisfied, because only false and
# undefined fail in Rego. These tests pin the CURRENT behavior so they fail, and
# must be inverted, when the policy is corrected. They do not endorse it. See
# payments/AGENCY-CHECK-RECEIPT-EVIDENCE.md "Findings outside this profile".

# APAY-REGO-DEF-1 (fail-open): hear_satisfied_by: null skips HEAR. An irreversible
# payment to a novel destination is allowed and its credential released. The
# Python TransactionFirewall escalates the same transaction, so a Policy Parity
# Guard deployment refuses (fails closed); an OPA-only deployment does not.
test_KNOWN_DEFECT_apay_rego_1_null_hear_satisfied_by_skips_hear if {
	critical_doc.hear_satisfied_by == null
	d := apay.decision with input as critical_doc
	d.consequence == "critical"
	d.decision == "allow"
	apay.release_credential with input as critical_doc
}

# APAY-REGO-DEF-2 (mislabel, still denies): runtime: null reports
# RUNTIME_NOT_ATTESTED; the firewall reports NO_RUNTIME_MEASUREMENT, so the
# reason-code sets disagree under the Policy Parity Guard.
test_KNOWN_DEFECT_apay_rego_2_null_runtime_reason_code if {
	codes(with_patch({"runtime": null})) == ["RUNTIME_NOT_ATTESTED"]
}

test_credential_release_rechecks_runtime_identity if {
	not apay.release_credential with input as with_patch({"runtime": {"runtime_measurement_id": ""}})
}

# ---------------------------------------------------------------------------
# Agency Check receipt evidence (nexus-apay-acr/0.1): advisory, shadow only
# ---------------------------------------------------------------------------

evidence := {
	"profile": "nexus-apay-acr/0.1",
	"receipt_id": "32a84d47-d036-4826-95e0-be2478aae0a6",
	"receipt_hash": "ab",
	"issuer_key_id": "k1",
	"schema_valid": true,
	"hash_verified": true,
	"signature_verified": true,
	"binding_verified": true,
	"transaction_digest": digest,
	"issued_at": "2026-09-21T11:55:00.000Z",
	"nor_outcome": "allow",
	"nor_deny_reason": null,
	"tool_name": "agency_check",
	"card_state": "ready",
	"card_state_source": "unsigned_meta",
	"ruleset_version": "1.1.0",
	"findings": [],
}

with_evidence(doc, patch) := object.union(doc, {"agency_check_evidence": object.union(evidence, patch)})

advisory(doc) := a if {
	a := apay.agency_check_advisory with input as doc
}

evidence_variants := [
	null,
	{},
	{"card_state": "clarify"},
	{"card_state": "pause"},
	{"card_state": null},
	{"signature_verified": false},
	{"hash_verified": false},
	{"binding_verified": false},
	{"transaction_digest": "other"},
	{"issued_at": "2026-09-20T00:00:00Z"},
	{"issued_at": "not-a-time"},
	{"nor_outcome": "deny", "nor_deny_reason": "kill_switch"},
	{"profile": "nexus-apay-acr/9.9"},
]

outcome(doc) := {"decision": d, "release": r} if {
	d := apay.decision with input as doc
	r := apay.release_credential with input as doc
}

decision_with(doc, null) := outcome(doc)

decision_with(doc, patch) := outcome(with_evidence(doc, patch)) if patch != null

# Backward compatibility: the payment decision, its reason codes and the
# credential release gate are identical with and without any receipt.
test_receipt_never_changes_decision_or_release if {
	docs := [
		base,
		unheard(with_patch({"transaction": {"amount": {"minor_units": 40000}}})),
		unheard(critical_doc),
		critical_doc,
		with_patch({"transaction": {"category": "gambling"}}),
		with_patch({"revocation": {"available": false}}),
	]
	every doc in docs {
		expected := decision_with(doc, null)
		every patch in evidence_variants {
			decision_with(doc, patch) == expected
		}
	}
}

test_ready_card_never_satisfies_hear if {
	doc := with_evidence(unheard(with_patch({"transaction": {"amount": {"minor_units": 40000}}})), {})
	advisory(doc).status == "ready"
	verdict(doc) == "escalate"
	codes(doc) == ["HEAR_REQUIRED"]
}

test_absent_evidence if {
	a := advisory(base)
	a.status == "absent"
	a.findings == ["ACR_ABSENT"]
	a.shadow_effect == "none"
	a.receipt_id == null
	advisory(object.remove(base, ["agency_check_evidence"])).status == "absent"
	advisory(with_patch({"agency_check_evidence": "receipt"})).status == "absent"
}

test_advisory_is_shadow_and_declared if {
	a := advisory(with_evidence(base, {}))
	a.mode == "shadow"
	a.enforced == false
	a.card_state_attested == false
	a.profile == "nexus-apay-acr/0.1"
	a.receipt_id == "32a84d47-d036-4826-95e0-be2478aae0a6"
}

test_verified_bound_fresh_ready if {
	a := advisory(with_evidence(base, {}))
	a.status == "ready"
	a.shadow_effect == "none"
	a.findings == ["ACR_CARD_STATE_DECLARED"]
}

test_clarify_and_pause_would_escalate if {
	c := advisory(with_evidence(base, {"card_state": "clarify"}))
	c.status == "clarify"
	"ACR_CARD_CLARIFY" in c.findings
	c.shadow_effect == "would_escalate"
	p := advisory(with_evidence(base, {"card_state": "pause"}))
	p.status == "pause"
	"ACR_CARD_PAUSE" in p.findings
	p.shadow_effect == "would_escalate"
}

test_missing_or_unknown_card_state if {
	a := advisory(with_evidence(base, {"card_state": null}))
	a.status == "card_state_unknown"
	"ACR_CARD_STATE_ABSENT" in a.findings
	advisory(with_evidence(base, {"card_state": "go"})).status == "card_state_unknown"
}

test_unverified_receipt_is_invalid if {
	a := advisory(with_evidence(base, {"signature_verified": false}))
	a.status == "invalid"
	"ACR_SIGNATURE_UNVERIFIED" in a.findings
	a.shadow_effect == "would_escalate"
	"ACR_HASH_UNVERIFIED" in advisory(with_evidence(base, {"hash_verified": "yes"})).findings
	b := advisory(with_evidence(base, {"profile": "nexus-apay-acr/9.9"}))
	b.status == "invalid"
	"ACR_PROFILE_UNSUPPORTED" in b.findings
}

test_receipt_for_another_transaction_is_unbound if {
	a := advisory(with_evidence(base, {"transaction_digest": "other"}))
	a.status == "unbound"
	"ACR_BINDING_MISMATCH" in a.findings
	advisory(with_evidence(base, {"binding_verified": false})).status == "unbound"

	# The verifier's digest must also be THIS transaction's digest.
	mutated := with_evidence(with_patch({"transaction": {"canonical_digest": "mutated"}}), {})
	advisory(mutated).status == "unbound"
}

test_freshness if {
	advisory(with_evidence(base, {"issued_at": "2026-09-21T11:45:00Z"})).status == "ready"
	stale := advisory(with_evidence(base, {"issued_at": "2026-09-21T11:44:59Z"}))
	stale.status == "stale"
	"ACR_NOT_FRESH" in stale.findings
	future := advisory(with_evidence(base, {"issued_at": "2026-09-21T12:01:01Z"}))
	future.status == "stale"
	"ACR_FUTURE_DATED" in future.findings
	advisory(with_evidence(base, {"issued_at": "2026-09-21T12:01:00Z"})).status == "ready"
	advisory(with_evidence(base, {"issued_at": "not-a-time"})).status == "stale"
}

test_service_paused_is_not_a_card if {
	a := advisory(with_evidence(base, {"nor_outcome": "deny", "nor_deny_reason": "kill_switch", "card_state": null}))
	a.status == "check_not_run"
	"ACR_SERVICE_PAUSED" in a.findings
	"ACR_CHECK_NOT_RUN" in a.findings
	a.shadow_effect == "would_escalate"
	"ACR_SERVICE_PAUSED" in advisory(with_evidence(base, {"nor_outcome": "deny", "nor_deny_reason": "frozen"})).findings
}

test_receipt_for_another_tool_did_not_check if {
	advisory(with_evidence(base, {"tool_name": "get_receipt"})).status == "check_not_run"
}

# A declared card state cannot outrank a verification failure.
test_status_precedence if {
	advisory(with_evidence(base, {"signature_verified": false, "transaction_digest": "other"})).status == "invalid"
	advisory(with_evidence(base, {"transaction_digest": "other", "issued_at": "2020-01-01T00:00:00Z"})).status == "unbound"
	advisory(with_evidence(base, {"issued_at": "2020-01-01T00:00:00Z", "nor_outcome": "deny"})).status == "stale"
	advisory(with_evidence(base, {"nor_outcome": "deny", "card_state": "ready"})).status == "check_not_run"
}
