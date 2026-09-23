# CP.5.APAY Controls

[← Profile](README.md) | [Threat Model](THREAT-MODEL.md) | [Challenge Lab](CHALLENGE-LAB.md)

**Status: draft. Non-normative until reviewed.**

Twenty controls for the agent-to-payment enforcement plane. Each entry gives the normative outcome, the AI SAFE² foundation it extends rather than duplicates, the NEXUS mechanism that implements it, and the test that proves it denies what it claims to deny.

Test references are to `NEXUS/sdk/python/tests/test_apay.py` unless noted.

---

## Reuse, not duplication

AI SAFE² v3.1 already supplies most of the governance primitives this profile needs. The payment controls extend existing pillars; they do not restate them.

| Payment requirement | AI SAFE² foundation | Extension APAY adds |
| ------------------- | ------------------- | ------------------- |
| Poisoned product or negotiation content | P1 malicious-prompt filtering, indirect-injection coverage, memory governance | Treat all merchant catalogs, offers, reviews, receipts and agent-to-agent messages as untrusted **payment-influencing** input |
| Payment-tool least privilege | P1 function access control, credential compartmentalization | Separate search, negotiate, approve, sign, settle, refund and account-management capabilities |
| Workload authenticity | CP.4 runtime trust, artifact provenance | Bind **transaction authorization** to measured runtime and artifact identity |
| Complete transaction trace | P2 activity logging, decision traceability, semantic execution traces | Add mandate, cart, delegation, policy, attestation and settlement linkage |
| Economic containment | MCP-8 economic ceiling, P3 rate limits, P4 cost tracking | Enforce cumulative spend across descendants, rails, facilitators, merchants, currencies and time windows |
| Emergency revocation | P3 NHI revocation, kill switches, CP.9 | Define **measurable** credential, mandate, channel and descendant revocation objectives |
| Delegation attenuation | CP.9 replication governance | Apply monotonic spend, merchant, item, geography, rail, time and tool narrowing |
| Human authority | CP.10 HEAR | Classify high-impact financial actions requiring HEAR or designated financial authority |
| Protocol seam control | CP.5 protocol profiles | Prevent downgrade from mandate-bound payment to browser checkout, bearer token or weaker rail |
| Independent evidence | P2 append-only evidence, CP.4 governance | Produce adjudication-ready payment evidence without exposing unnecessary principal data |

---

## APAY-01 — Principal and owner binding

**Outcome.** Every payment-capable agent is linked to a verified principal, a named owner of record, an ACT tier, a policy authority and any applicable HEAR authority. Registration fails without them.

**Rationale.** An agent that can move money with no accountable human is an orphan with a wallet. This is refused at registration rather than at transaction time, because by transaction time the question is already academic.

**Foundation.** AISM I-5 (Owner of Record), CP.10 (HEAR).
**Mechanism.** `PrincipalBinding`, `IdentityNormalizer`, `PaymentIntegrityGateway.register_principal`.
**Binding rule.** Payment eligibility requires a workload-level claim (SPIFFE or equivalent) **and** an accountability claim. Neither alone suffices: workload identity without an owner is an orphan that can spend; an owner without workload identity cannot support runtime binding.

**Tests.** `test_apay01_rejects_agent_with_no_owner_of_record`, `test_apay01_identity_normalizer_requires_workload_and_owner`, `test_apay01_identity_alone_never_reaches_runtime_bound`.

---

## APAY-02 — Trusted mandate rendering

**Outcome.** Consequential terms are rendered through an integrity-protected surface outside the nondeterministic agent's control, and the rendering digest binds into the grant.

**Rationale.** A signature covers the object placed in front of the principal. If a compromised agent controls that object, the signature is valid and useless. The surface therefore generates from compiled constraints only, contributing no agent prose.

**Ordering is itself a control.** Consequence first, then bounds, then unresolved items. Approval fatigue is a real failure mode, and burying an irreversible-rail warning under line items is how broad mandates get rubber-stamped.

**Foundation.** CP.10 HEAR, P1 injection resistance.
**Mechanism.** `MandateCompiler.render`, `RenderedMandate.rendering_digest`, `AuthorityGrant.approval_surface`.

**Tests.** `test_apay02_rendering_is_derived_from_constraints_not_agent_prose`, `test_apay02_irreversible_settlement_is_surfaced_first`, `test_exp01_poisoned_mandate_rendering`.

---

## APAY-03 — Intent translation evidence

**Outcome.** The system preserves the principal's original instruction, the normalized constraints derived from it, material assumptions, conflicts and unresolved ambiguities — as separately hashed artifacts. A grant carrying unresolved ambiguity MUST NOT authorize spend.

**Rationale.** This is the semantic-intent problem stated honestly. Cryptography cannot prove faithful translation, so the profile makes the translation inspectable instead: an adjudicator compares `instruction_digest` against `normalized_constraints_digest` rather than trusting the agent's account of its own reasoning.

**Open-ended language never becomes a number.** "Whatever we need", "as much as it takes", "best price" produce a recorded ambiguity that a human must close. A model resolving its own spending limit is the vulnerability, not the feature: the same injection that steers a purchase steers the constraint meant to bound it.

**Foundation.** P2 decision traceability, CP.4 governance evidence.
**Mechanism.** `MandateCompiler.compile`, `Ambiguity`, `CompiledMandate.unresolved`, `MandateCompiler.issue`.

**Tests.** `test_apay03_open_ended_language_becomes_ambiguity_not_a_number`, `test_apay03_grant_cannot_be_issued_with_unresolved_ambiguity`, `test_apay03_recurring_authority_is_never_inferred`, `test_apay03_instruction_and_constraints_are_separately_hashed`.

---

## APAY-04 — Independent constraint evaluation

**Outcome.** A deterministic policy engine — not the LLM — validates amount, payee, item, category, geography, rail, expiry, recurrence and cumulative exposure. All failing rules are reported, not just the first.

**Rationale.** A policy engine an attacker can talk to is a policy engine an attacker can talk out of. Reporting every failure matters operationally: returning one reason at a time turns a single misconfiguration into a queue of support tickets.

**Foundation.** P1 function access control, CP.5 protocol profiles.
**Mechanism.** `TransactionFirewall.evaluate`, `opa/nexus-apay.rego` (`constraint_violations`).

**Tests.** `test_apay04_each_constraint_axis_denies` (6 axes, parameterized), `test_apay04_clean_transaction_is_allowed`, `test_apay04_reports_every_failing_rule_not_just_the_first`.

---

## APAY-05 — Runtime-bound authorization

**Outcome.** Credential release and protected dispatch require an approved, fresh workload measurement or equivalent runtime-assurance evidence. Missing, stale, unattested or baseline-mismatched measurement denies.

**Rationale.** This is the control the rest of the ecosystem does not have. Identity answers "which agent arrived"; measurement answers "is that agent still the software we approved, right now". A measurement without freshness is a claim about the past being used to authorize the present.

**Self-declared is not attested.** `attestation_method` in `{none, declared}` fails. Where hardware attestation is unavailable the honest outcome is reduced functionality, not reduced assurance.

**Foundation.** CP.4 runtime trust and artifact provenance. **New AISM invariant I-7.**
**Mechanism.** `RuntimeMeasurement`, `TransactionFirewall._runtime_reasons`, `PaymentIntegrityGateway.pin_runtime_baseline`.

**Tests.** `test_apay05_missing_runtime_measurement_denies`, `test_apay05_stale_measurement_denies`, `test_apay05_unattested_measurement_denies`, `test_apay05_baseline_mismatch_denies`, `test_exp02_runtime_substitution`.

---

## APAY-06 — Non-exportable signing authority

**Outcome.** Payment and mandate keys remain in an HSM, TEE, secure element, managed signer or equivalent isolated service. The model never receives raw key material and never reaches the signer directly.

**Rationale.** Key residency decides whether a host compromise means "an attacker can propose transactions" or "an attacker can mint valid authorizations". Every published agent-payment protocol assumes the signing host is trustworthy; none require proof of it.

**Default is refusal.** `NullCredentialBroker` is the bound default and raises on every call. Replacing it with a stub that returns a fake signature is the single most damaging change available in this codebase, and `TestHonesty` exists to catch it.

**The broker re-checks what the firewall already checked.** Decision must be ALLOW, canonical digest must be present, runtime reference must be present, and the revocation epoch must still be current. This is not redundancy; it is the assumption that the caller might be the compromised component.

**Foundation.** P1 credential compartmentalization, CP.4.
**Mechanism.** `CredentialBroker`, `NullCredentialBroker`, `CredentialBroker._preflight`, `CanonicalTransaction`.

**Tests.** `test_apay06_default_broker_refuses_everything`, `test_apay06_broker_signs_only_the_canonical_object`, `test_apay06_broker_refuses_a_non_allow_decision`, `test_apay06_broker_refuses_without_runtime_reference`, `test_gateway_default_broker_is_null`, `test_null_broker_cannot_be_talked_into_signing`.

---

## APAY-07 — Separation of duties

**Outcome.** Negotiation, policy evaluation, approval, signing, settlement, reconciliation and account management are independently authorized capabilities. A grant that can execute a payment does not thereby hold refund or account-management authority.

**Foundation.** P1 function access control, CP.9.
**Mechanism.** `AuthorityGrant.capabilities`, `TransactionIntent.capability`, capability attenuation in `AuthorityGraph.delegate`.

**Tests.** `test_apay07_capability_outside_grant_denies`, `test_apay07_child_cannot_gain_a_capability_parent_lacks`.

---

## APAY-08 — Monotonic delegation

**Outcome.** Every child grant is equal to or narrower than its parent across scope, spend, duration, tools, counterparties, rails, finality tolerance, assurance floor and delegation depth. Attenuation is re-derived at execution time, not trusted from mint time.

**Null means unconstrained, which makes it widening.** A child with `allowed_merchants: null` under a constrained parent is an escalation, not an inheritance. This is the default that quietly breaks most delegation implementations.

**A child may never forget a parent's deny list.** Deny lists union downward; allow lists intersect downward.

**Assurance and finality move one way only.** The assurance floor may rise, never fall. Finality tolerance may tighten, never loosen.

**`max_delegation_depth` is a remaining budget, not an absolute depth.** It decrements at every hop; a grant holding zero cannot mint children regardless of where it sits in the tree.

**Foundation.** CP.9 replication governance, AISM I-2 (Monotonic Scope).
**Mechanism.** `AuthorityConstraints.attenuation_violations`, `AuthorityConstraints.attenuate`, `AuthorityGraph.delegate`, `AuthorityGraph.lineage_violations`.

**Tests.** `test_apay08_widening_any_axis_is_refused` (6 axes, parameterized), `test_apay08_narrowing_is_accepted_and_depth_decrements`, `test_apay08_unconstrained_child_under_constrained_parent_is_widening`, `test_apay08_child_cannot_forget_parent_deny_list`, `test_apay08_depth_limit_stops_the_chain`, `test_apay08_lineage_reverified_at_execution_time`, `test_exp06_delegation_escalation_via_reissue`.

---

## APAY-09 — Aggregate economic ceiling

**Outcome.** Limits aggregate across agents, descendants, merchants, facilitators, wallets, rails, currencies and rolling time windows. A transaction must fit under the aggregate ceiling of the grant authorizing it **and every grant above it**.

**Rationale.** A per-transaction limit is the control an attacker never has to break. Spend is distributed across children until every individual check passes. Containment that is not evaluated on the tree is not containment.

**Cross-currency is refused, not converted.** `Money` raises on cross-currency comparison and the firewall denies on unmatched currency. Silently converting at an attacker-influenced rate would be worse than refusing.

**Foundation.** MCP-8 economic ceiling, P3 rate limits, P4 cost tracking. **New AISM invariant I-8.**
**Mechanism.** `AuthorityGraph.subtree_spend`, `AuthorityGraph.ceiling_violations`, `Money`.

**Tests.** `test_apay09_children_spend_counts_against_parent_ceiling`, `test_apay09_rolling_window_ceiling`, `test_exp05_salami_drain_across_children`, `test_money_refuses_cross_currency_comparison`, `test_money_rejects_float_construction`, `test_money_rejects_excess_precision`.

---

## APAY-10 — Velocity and micro-drain defense

**Outcome.** The system detects salami theft, split transactions, merchant dispersion, unusual cadence and cumulative sub-threshold spend.

**Rationale.** None of these shapes are fraud on their own. They are what a drain looks like when every individual transaction is inside policy — precisely the case per-transaction limits cannot see.

**Thresholds are policy, not truth.** `VelocityProfile` is exposed so a deployment measures its own false-block cost rather than inheriting numbers from a vendor who never saw its traffic.

**Foundation.** P3 rate limits, P4 anomaly detection, AISM I-6 (behavioral drift as a security signal).
**Mechanism.** `VelocityProfile`, `AuthorityGraph.velocity_violations`.

**Tests.** `test_apay10_micro_drain_detected`, `test_apay10_merchant_dispersion_detected`.

---

## APAY-11 — Freshness and replay resistance

**Outcome.** Mandates, payment authorizations, quotes, carts, attestations and receipts are nonce-bound, expiring, idempotent and replay-resistant.

**A retry is not a replay; a retry with changed terms is.** An idempotency key may be reused, but only carrying the same canonical digest. A "retry" that quietly changed the amount is a replay attack wearing a retry's clothes.

**Foundation.** P2 non-repudiation, CP.5 protocol profiles.
**Mechanism.** `ReplayLedger`, `TransactionIntent.idempotency_key`, `TransactionIntent.quote_expired`, broker-side idempotency guard.

**Tests.** `test_apay11_missing_nonce_denies`, `test_apay11_nonce_reuse_denies`, `test_apay11_expired_quote_denies`, `test_apay11_retry_with_changed_terms_is_a_replay`.

---

## APAY-12 — Transaction continuity

**Outcome.** Material changes between approved checkout and execution trigger re-evaluation or renewed authorization.

**The TOCTOU boundary is explicit.** `TransactionIntent.canonical_fields()` defines what makes this *this* transaction: amount, merchant, destination, category, rail, recurrence and line items. Anything inside that set may not drift between approval and settlement. Anything outside it may.

**Foundation.** P2 semantic execution traces, CP.5.
**Mechanism.** `TransactionIntent.canonical_digest`, `approved_cart_digest` comparison in `TransactionFirewall`.

**Tests.** `test_apay12_cart_mutation_after_approval_denies`, `test_apay12_missing_binding_denies`, `test_apay12_destination_substitution_denies`, `test_exp03_checkout_toctou`.

---

## APAY-13 — Revocation effectiveness

**Outcome.** Revocation invalidates credentials, grants, mandates, channels, cached decisions and descendant authority within a declared, **measured** objective.

**Revocation is an epoch, not a delete.** A revocation implemented as "remove the row" races every cache, facilitator and child in the system. A monotonic epoch carried in every grant and signed transaction invalidates all descendants and all cached decisions simultaneously.

**The epoch is re-read immediately before signing.** A decision made microseconds ago is not authority if the kill switch fired in between.

**Unknown is not live.** A component that cannot reach the epoch authority fails closed. A revocation plane that returns "probably fine" when it is down is worse than none, because it manufactures confidence.

**The metric is exposure, not acknowledgement.** `exposure_after_revocation` measures value that still moved after the kill decision. An API returning 200 is not revocation.

**Foundation.** P3 NHI revocation and kill switches, CP.9, AISM I-4.
**Mechanism.** `RevocationPlane`, `PaymentIntegrityGateway.revoke_principal`, `AuthorityGraph.exposure_after`.

**Tests.** `test_apay13_revocation_kills_descendants_immediately`, `test_apay13_unavailable_revocation_authority_fails_closed`, `test_apay13_zero_exposure_after_revocation`, `test_exp04_revocation_race`.

---

## APAY-14 — Downgrade resistance

**Outcome.** An agent cannot move to guest checkout, bearer credentials, alternate facilitators or weaker rails to bypass required controls.

**Assurance is ordered and enforced as a floor.** 0 none/guest, 1 bearer, 2 signed request (Web Bot Auth / Visa TAP class), 3 mandate bound to a cart (AP2 class), 4 mandate plus fresh workload measurement. The CP.5.APAY floor is 4.

**Deployment caveat.** This control bounds what flows *through* the gateway. Any network path that bypasses the gateway entirely is outside it. Network-level enforcement is a deployment requirement, not a profile control.

**Foundation.** CP.5 protocol profiles.
**Mechanism.** `AssuranceLevel`, `AuthorityConstraints.min_assurance`, `GatewayMetrics.downgrade_block_rate`.

**Tests.** `test_apay14_weaker_path_is_refused` (4 levels, parameterized), `test_apay14_downgrade_block_rate_is_measured`, `test_exp07_protocol_downgrade`, `test_apay20_no_binding_claims_native_runtime_assurance`.

---

## APAY-15 — Counterparty provenance

**Outcome.** Merchant identity, catalog and schema provenance, payment destination and settlement contract validate against trusted baselines.

**Registry entries are baselines, not blessings.** A merchant whose baseline digest has changed is unverified until re-baselined. A valid registry entry pointing at a substituted destination is exactly the registry-compromise case this catches.

**Stated limit.** Provenance confirms a counterparty is who the registry says. It cannot detect an authentic merchant behaving adversarially. See Challenge Lab experiment 8.

**Foundation.** CP.4 artifact provenance, P1 untrusted-input handling.
**Mechanism.** `CounterpartyRegistry`, `AuthorityConstraints.allowed_destinations`.

**Tests.** `test_apay15_unregistered_merchant_denies`, `test_apay15_changed_merchant_baseline_denies`, `test_apay15_untrusted_facilitator_denies`, `test_exp09_registry_compromise_destination_swap`.

---

## APAY-16 — Settlement atomicity

**Outcome.** Verification, credential release, protected action, settlement result and receipt state cannot silently diverge.

**Ambiguous is a first-class outcome.** Most payment integrations model success and failure. The state that actually causes duplicate settlement and service-without-payment is the third one: a timeout where nobody knows whether value moved.

**Ambiguous settlement commits exposure.** Counting it as zero spend is how a rail failure becomes free money. The ceiling assumes value may have moved until reconciliation proves otherwise.

**One canonical transaction, one signature.** A second signature over the same idempotency key with a different digest is a double-authorization, not a retry.

**Foundation.** P2 append-only evidence, CP.4.
**Mechanism.** `SettlementState`, `PaymentIntegrityGateway.settle`, broker idempotency guard.

**Tests.** `test_apay16_ambiguous_settlement_still_commits_exposure`, `test_apay16_broker_refuses_second_signature_with_different_terms`, `test_exp10_settlement_ambiguity_no_double_spend`.

---

## APAY-17 — Privacy-preserving evidence

**Outcome.** Verifiers receive only required attributes, using selective disclosure or derived claims where practical.

**Three disclosure tiers.** Public (what a merchant or facilitator sees), adjudication (what a dispute reviewer sees), sealed (what only the principal's organization can open).

**Withheld is committed, not dropped.** Sealed fields are replaced by a digest over them, so omission is detectable and the principal can later open them to prove content. That is what makes this selective disclosure rather than omission. AP2 already uses selective disclosure for mandate privacy; this follows the same pattern for adjudication evidence.

**Foundation.** P2 evidence governance, data minimization.
**Mechanism.** `PaymentTransactionReceipt.redacted`, `DisclosureTier`.

**Tests.** `test_apay17_adjudication_tier_withholds_and_commits`, `test_apay17_public_tier_hides_authority_internals`.

---

## APAY-18 — Fail-safe financial response

**Outcome.** Ambiguous verification, timeout, partial settlement, policy conflict or unavailable revocation status fails closed or enters governed reconciliation.

**Three terminal states, deliberately distinguished.** `deny` (a rule was violated), `escalate` (a named human must authorize), `reconcile` (the state is unknown and a human must resolve it). Collapsing the third into the second or the first is how ambiguity becomes a retry loop.

**High-consequence actions always require a human.** Irreversible settlement is classified `consequential` or, to a novel destination, `critical`. Finality dominates amount: a small irreversible payment to an unknown destination is worse than a larger reversible one, because there is no path to undo it.

**Foundation.** CP.10 HEAR, fail-closed enforcement.
**Mechanism.** `PaymentDecision`, `classify_consequence`, ambiguity routing in `TransactionFirewall.evaluate`.

**Tests.** `test_apay18_unknown_states_never_produce_allow`, `test_apay18_hear_requirement_escalates_rather_than_denies`, `test_apay18_hear_satisfied_allows`, `test_apay18_irreversible_rail_always_requires_human`.

---

## APAY-19 — Dispute-grade evidence

**Outcome.** The system generates an independently reconstructable evidence package linking intent, authorization, runtime, delegation, execution and settlement.

**The test of adequacy.** A third party who trusts none of the participants must be able to reconstruct who was accountable, what authority existed, what the principal approved, what workload executed, which ruleset decided, what moved, and whether revocation had already fired — **without believing the agent's own explanation of its reasoning**.

**Completeness is a property of the transaction, not of one receipt.** An authorization receipt legitimately cannot carry a settlement id. Coverage is measured across the union of receipts for a transaction, and missing fields are named rather than scored away.

**An empty list is an answer.** A clean allow carries no reason codes. Scoring `[]` as a gap would penalize exactly the transactions where nothing went wrong.

**`hear_satisfied_by` is never null.** It is an identity, `not_required`, or `required_not_satisfied`, so a reviewer can distinguish "no human was needed" from "a human was needed and the record is missing".

**Foundation.** P2 append-only evidence, non-repudiation, CP.4.
**Mechanism.** `PaymentTransactionReceipt`, `EvidenceLedger`, `REQUIRED_EVIDENCE_FIELDS` (41 fields), `EvidenceLedger.verify_chain`.

**Tests.** `test_apay19_evidence_chain_detects_tampering`, `test_apay19_evidence_is_complete_across_the_transaction`, `test_apay19_incomplete_evidence_is_reported_not_hidden`, `test_apay19_denied_transactions_also_produce_evidence`, `test_exp11_evidence_adjudication_distinguishes_causes`.

---

## APAY-20 — Continuous adversarial validation

**Outcome.** Changes to agents, models, prompts, policies, payment adapters, signers or rails trigger relevant security and payment-integrity tests.

**Unimplemented adapters must raise, not return success.** Every rail binding in `adapters.py` raises `NotImplementedError` by design, matching the convention in `NEXUS/adapters/mcp/adapter.py`. An incomplete adapter fails closed; it does not pass traffic. Shipping a stub that returns success would let a deployment believe it has binding it does not have.

**No binding claims native runtime assurance.** A test asserts that every rail binding's `max_native_assurance` is strictly below `RUNTIME_BOUND`, which is the structural claim of this whole profile expressed as an executable assertion.

**The framework is the subject of falsification, not the source of its own proof.** The twelve Challenge Lab experiments belong in the AI SAFE² Challenge Lab, with fixtures, graders, negative results and environmental constraints published.

**Foundation.** P4 continuous validation, Challenge Lab.
**Mechanism.** `test_apay.py`, `test_apay_opa_contract.py`, [CHALLENGE-LAB.md](CHALLENGE-LAB.md).

**Tests.** `test_apay20_rail_bindings_are_fail_closed_not_stubs`, `test_apay20_no_binding_claims_native_runtime_assurance`, and the entire `TestHonesty` class.

---

## Conformance levels

| Level | Requirement |
| ----- | ----------- |
| **APAY-Baseline** | APAY-01, 04, 06, 07, 08, 11, 12, 18, 19. Deterministic evaluation, isolated signing, monotonic delegation, fail-closed, evidence |
| **APAY-Contained** | Baseline plus 09, 10, 13, 14. Aggregate containment, velocity defense, measured revocation, downgrade resistance |
| **APAY-Assured** | Contained plus 02, 03, 05, 15, 16, 17, 20. Trusted rendering, translation evidence, runtime binding, counterparty provenance, settlement atomicity, privacy-preserving evidence, continuous validation |

A deployment states its level and publishes its metrics. A level claimed without published `GatewayMetrics` and evidence-completeness figures is an assertion, not a conformance claim.

---

*CP.5.APAY draft · NEXUS v0.4 · AI SAFE² v3.1*
