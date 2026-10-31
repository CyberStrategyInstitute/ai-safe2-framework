# Agency Check Receipt as Payment Evidence

**Profile identifier:** `nexus-apay-acr/0.1`

**Profile:** CP.5.APAY evidence extension

**Status:** Draft. Shadow (advisory) mode only. Not a production assurance claim.

**Reference code:** `nexus_sdk/payments/agency_check.py`, `opa/nexus-apay.rego` (advisory section), tests in `sdk/python/tests/test_apay_agency_check.py` and `opa/nexus_apay_test.rego`

[Payment profile](README.md) | [Controls](CONTROLS.md) | [Policy parity](POLICY-PARITY.md) | [Adapter guide](ADAPTER-GUIDE.md)

## Purpose

Agency Check gives a person a second look before an agent acts and returns a
signed NEXUS Output Receipt (NOR v0.3) saying that the check ran. This profile
defines how that receipt is attached to one payment request as attributed
evidence, so a reviewer can later show that a check was run for *this* payment,
by *this* issuer, *recently*.

Payment-rail integration stays in NEXUS. Agency Check, MCP Pro and Warden are
clients of the profile; none of them hold payment authority.

## What a receipt proves, and what it does not

| A receipt proves | A receipt does not prove |
| --- | --- |
| A holder of the pinned issuer key signed these NOR fields | That the person read the card or agreed with it |
| The check ran (`outcome: allow`) or was refused (`outcome: deny`, with a signed `deny_reason`) | That the payment is safe, legitimate, or approved |
| The receipt names the digest of this transaction (binding) | What was checked, or that the check input matched the payment |
| The receipt existed at `timestamp_utc` | That the card recommendation is authentic (see below) |

`outcome: allow` means "the check ran". It is **not** approval. A receipt is not
an authorization, never satisfies HEAR, never removes a reason code, and never
releases a credential. Under this profile evidence can only add friction.

## Signed versus declared

Agency Check signs the NOR fields only. The card recommendation is returned
beside the receipt in the unsigned `meta` of `get_receipt`:

| Field | Source | Trust |
| --- | --- | --- |
| `receipt_id`, `tool_name`, `outcome`, `deny_reason`, `timestamp_utc`, `cael_envelope_hash`, `tool_arguments_hash` | NOR, covered by `receipt_hash` and the signature | Attested by the issuer key |
| `card_state` (`ready`, `clarify`, `pause`) | `get_receipt` `meta`, unsigned | **Declared.** Carried as `card_state_source: "unsigned_meta"`; the policy always reports `card_state_attested: false` |
| `ruleset_version` | `get_receipt` `meta`, unsigned | **Declared** |

An implementation must not present `card_state` as signed. Signing the card state
would require an upstream Agency Check change; none is assumed here. Until then a
`ready` card carries no more weight than the client's word.

## Evidence document

`verify_agency_check_receipt(...)` returns the `agency_check_evidence` object
that `build_opa_input(..., agency_check_evidence=...)` places in the policy input.
It contains ids, enums, hashes and timestamps only.

| Field | Type | Meaning |
| --- | --- | --- |
| `profile` | string | Always `nexus-apay-acr/0.1`. Any other value is `ACR_PROFILE_UNSUPPORTED` |
| `receipt_id`, `receipt_hash` | string or null | From the NOR |
| `issuer_key_id` | string or null | `kid` of the pinned key that verified the signature |
| `schema_valid` | bool | NOR v0.3 shape, closed field set, bounded sizes |
| `hash_verified` | bool | `receipt_hash` equals SHA-256 of the canonical body |
| `signature_verified` | bool | Ed25519 over the `receipt_hash` string verifies under a pinned key |
| `binding_verified` | bool | `cael_envelope_hash` equals the binding for this transaction |
| `transaction_digest` | string or null | Set only when `binding_verified` |
| `issued_at` | string or null | NOR `timestamp_utc` |
| `nor_outcome`, `nor_deny_reason`, `tool_name` | string or null | From the NOR |
| `card_state`, `card_state_source` | string | Declared; source is `unsigned_meta` or `absent` |
| `ruleset_version` | string or null | Declared |
| `findings` | list of string | Verifier findings, sorted, no free text |

The verifier never raises on hostile input. Every failure becomes a `false` and a
finding.

## Binding to the payment request

The binding anchors the receipt to one payment request through the transaction's
`canonical_digest`, the same digest recorded in the PTR (`transaction.canonical_digest`).

1. The client computes `binding_digest(transaction_digest)`, which is the NEXUS
   canonical hash of `{"profile": "nexus-apay-acr/0.1", "transaction_digest": <digest>}`.
2. The client sends it as MCP `params._meta.nexusCaelEnvelopeHash` on the
   `agency_check` call. Agency Check signs it into the receipt as
   `cael_envelope_hash`.
3. The verifier recomputes the value for the transaction being authorized and
   requires equality. No other binding is accepted.

The profile string is part of the hashed value, so a raw transaction digest
placed in `nexusCaelEnvelopeHash` does not bind. A receipt bound to a different
transaction, or with no binding, is `unbound`. The policy independently
re-checks `evidence.transaction_digest == transaction.canonical_digest`.

Binding proves the receipt was *requested for* this digest. It does not prove
the check's text described this payment: `tool_arguments_hash` hashes what the
client sent, and the arguments stay with the client by design.

## Signature verification

- Verification happens **outside** the policy, in the SDK, in the same position
  as runtime attestation. OPA cannot verify raw Ed25519.
- `receipt_hash` is SHA-256 over the canonical JSON of every other field (keys
  sorted recursively, no whitespace, UTF-8). The signature is Ed25519 over the
  ASCII `receipt_hash` string, base64url.
- Keys are **pinned** by the deployment as a JWKS (at most 16 keys). A JWKS URL
  inside a receipt or a `get_receipt` result is a hint, never a trust anchor, and
  this profile never fetches keys.
- The hash is checked before the signature. Receipts over 8192 canonical bytes,
  with unknown fields, or with missing required fields are refused with findings.
- If no Ed25519 implementation is installed the result is
  `ACR_VERIFIER_UNAVAILABLE` and `signature_verified: false`. Missing evidence is
  never reported as verified.

Cross-implementation check: `scripts/verify-receipt.mjs` in Agency Check and
this verifier agree on the fixtures in `sdk/python/tests/fixtures/agency_check`.

## Freshness

Judged by the policy against its own `input.now`, never by the verifier's clock.

| Rule | Value |
| --- | --- |
| Maximum age | 900 seconds |
| Maximum future skew | 60 seconds |
| Outside the window | status `stale`; finding `ACR_NOT_FRESH`, plus `ACR_FUTURE_DATED` if future |

Deployments may tighten these constants in the policy; widening them needs a
decision owner.

## Policy outcome by receipt state

Status is the first matching row, top to bottom. In **shadow** mode (the only
mode in 0.1) every row leaves `decision`, `reason_codes`, `allow` and
`release_credential` unchanged. The last column is what a future *enforce*
profile would do, reported as `shadow_effect`.

| Status | When | Findings (examples) | Shadow effect | Future enforce profile |
| --- | --- | --- | --- | --- |
| `absent` | no receipt | `ACR_ABSENT` | `none` | Escalate only where a grant constraint requires a check; none exists in 0.1, so absence is never penalized |
| `invalid` | wrong profile, hash or signature not verified | `ACR_HASH_UNVERIFIED`, `ACR_SIGNATURE_UNVERIFIED` | `would_escalate` | Treat as no evidence; escalate where required |
| `unbound` | not bound to this transaction | `ACR_BINDING_MISMATCH` | `would_escalate` | Same |
| `stale` | outside freshness window | `ACR_NOT_FRESH` | `would_escalate` | Same |
| `check_not_run` | `outcome: deny` or wrong tool | `ACR_CHECK_NOT_RUN`; `ACR_SERVICE_PAUSED` when the signed `deny_reason` is `kill_switch` or `frozen` | `would_escalate` | Escalate to a human; a paused service is a service state, not a verdict on the payment |
| `pause` | authentic, bound, fresh, ran; declared card `pause` | `ACR_CARD_PAUSE` | `would_escalate` | Escalate to a human (HEAR); never auto-deny on unsigned input |
| `clarify` | same; declared card `clarify` | `ACR_CARD_CLARIFY` | `would_escalate` | Escalate to a human |
| `ready` | same; declared card `ready` | `ACR_CARD_STATE_DECLARED` | `none` | No change. `ready` never satisfies HEAR and never relaxes a control |
| `card_state_unknown` | authentic and ran, but no valid card state | `ACR_CARD_STATE_ABSENT` | `would_escalate` | Same as no card |

Missing, paused and clarify cases, stated plainly:

- **Missing receipt:** the payment proceeds exactly as it would have. The advisory
  reports `absent`.
- **Paused service (kill switch / frozen):** the check did not run. Shadow mode
  reports it and changes nothing. An enforce profile escalates; it must not treat
  a paused advisory service as a reason to block a payment the grant permits.
- **Clarify / pause card:** the advisory reports the declared state. No automatic
  decision is taken from an unsigned field.

## Backward compatibility

- Nothing in the advisory section is referenced by `reason_codes`, `decision`,
  `allow` or `release_credential`. `opa/nexus_apay_test.rego` asserts the decision
  and release gate are identical with and without any receipt variant, across
  allow, escalate and deny inputs. `test_apay_agency_check.py` repeats that end to
  end from `build_opa_input` through OPA.
- `agency_check_evidence` is optional and defaults to `null`. Existing callers and
  the Policy Parity Guard are unaffected.
- Read the advisory at `/v1/data/nexus/apay/agency_check_advisory`.
- Promotion from shadow to enforce is a policy change for a named decision owner
  and needs its own profile version (`0.2` or later). It is out of scope here.

## Privacy

- The evidence document carries ids, enums, hashes and timestamps. It carries no
  card text, no `tool_arguments`, no merchant or recipient names, and no URLs.
- Free text in `meta` (titles, details) is dropped by the verifier. Only
  `card_state` (closed enum) and `ruleset_version` (short token) are kept.
- `agent_did` is not copied into the evidence. Receipts are retained by the
  deployment on the same basis as the PTR, and a receipt hash must not be
  published beside user-identifying data.
- A receipt is a correlation handle: anyone holding it and a candidate input can
  confirm `tool_arguments_hash`. Treat receipts as sensitive records.

## Rail scope

This profile is rail-independent. It does not enable any rail: Visa TAP and
Mastercard Agent Pay remain stubs, and x402 remains in shadow mode. No test
or fixture contacts Agency Check or a payment network.

## Known limits

- `card_state` is unsigned; a compromised client can claim `ready`.
- Binding is to the transaction digest, not to the content that was checked.
- This profile defines no receipt revocation. Freshness is the only expiry, so a
  receipt stays verifiable for the 900-second window whatever happens afterwards.
  (Agency Check's OAuth token revocation is a separate mechanism and does not
  revoke receipts.)
- Key rotation relies on the deployment updating its pinned JWKS.
- Enforcement is not implemented. Self-assessment only; no independent review
  has been performed.
