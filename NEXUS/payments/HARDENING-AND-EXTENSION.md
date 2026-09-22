# APAY hardening and extension map

Every operator-facing feature has a human name and a stable technical name.
The human name explains the protection; the technical name is the API or type.

## Implemented hardening steps

| Step | Human name | Technical name | What is implemented | Honest boundary |
|---:|---|---|---|---|
| 1 | **Spend Hold** | `ExposureReservation` | Atomic reservation before credential release; settled and ambiguous outcomes commit exposure; definitive failure releases it | Reference in-memory state, not a distributed transaction coordinator |
| 2 | **Runtime Proof** | `AttestationVerifier` | Fail-closed verifier contract, challenge/signer/evidence fields, and a test-only HMAC verifier | Production TDX/SNP/TPM/cloud-verifier bindings remain required |
| 3 | **Full-Term Approval Seal** | `TransactionIntent.canonical_fields` | Approval now binds geography, finality, facilitator, assurance, capability, quote expiry, and merchant-verification state | A digest proves fidelity to the rendered terms, not that the bargain was wise |
| 4 | **Human Shield** | `UserControlPolicy` | Principal pause, merchant block, approved-payee control, amount confirmation, and cooling-off policy | Applications must provide an authenticated, independent confirmation surface |
| 5 | **SafePay Exact** | `X402V2ExactEVMUSDCBinding` | Narrow x402 v2 exact/EVM/authorization-flow validator with allowlists, continuity claims, strict requirement equality, and read-only reconciliation | Shadow mode only; it does not verify chain signatures or call a live facilitator |
| 6 | **Attack Gauntlet** | `test_apay_hardening.py` | Tests for reserved-exposure overspend, amount-less ambiguity, approval mutation, user pause, x402 substitution, and keyed evidence commitments | Full pytest execution requires the development dependency set |
| 7 | **Evidence Vault** | `DurableEvidenceLedger` | Fsynced JSONL evidence, hash chaining, HMAC record integrity, and keyed disclosure commitments | Confidentiality requires an encrypted volume or KMS envelope; no home-grown encryption is claimed |

## Required deployment gates

None of these controls authorize production use by themselves. A deployment must:

1. Replace in-memory authority, replay, revocation, reservation, and settlement
   state with one strongly consistent store and transactional compare-and-swap.
2. Bind Runtime Proof to an independently operated attestation verifier and
   trusted endorsements; never accept caller-declared `attested=true`.
3. Put Human Shield confirmation on a channel independent of the purchasing
   agent, with phishing-resistant authentication and a transaction preview.
4. Run SafePay Exact in observe-only mode against official fixtures and at
   least two facilitators before allowing signatures or settlement.
5. Place Evidence Vault on encrypted, access-controlled storage; keep integrity
   and commitment keys in a KMS/HSM; test restore, deletion, export, and legal hold.

## Future extension contract

### Shared adapter gate

**RailGuard Contract** (`RailBindingContract`) declares the exact protocol
version, scheme, networks, assets, payment flow, finality model, native assurance
ceiling, and whether verification is authoritative. **RailGuard Lab**
(`RailBindingConformanceSuite`) evaluates public synthetic vectors for canonical
binding, fail-closed authority checks, assurance overclaiming, finality,
reconciliation safety, deterministic input handling, and payload privacy.

Every implemented rail binding must pass RailGuard Lab before it can be described
as supported. Reports intentionally omit payloads and retain only case names and
control findings so conformance evidence does not become payment-data leakage.

### SafePay Verified

**SafePay Verified** (`X402V2ExactEVMUSDCAuthoritativeBinding`) adds an
authoritative-verifier boundary for x402 v2 exact EVM payments. Authenticated
verification and settlement evidence must bind the exact facilitator request
digest. Facilitator identity is allowlisted; successful settlement must match the
approved network and amount and include a transaction identifier. Verifier
outages halt instead of falling back to structural assurance.

The interface follows the x402 Foundation v2 specification's read-only
`POST /verify` and state-committing `POST /settle` split:
<https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md>.
The included fixture verifier is test evidence only. Production deployments must
inject a mutually authenticated facilitator client or independently operated
chain verifier and protect its trust roots outside the agent process.

**SafePay Variable** (`X402V2UptoBinding`) preserves the distinction between the
client-signed ceiling and the server-metered actual charge, accepting zero or
partial settlement only when `actual <= ceiling`. **SafePay Escrow**
(`X402V2EscrowBinding`) models the separate deposit and claim/refund settles,
requires deposit before resource execution, and requires an authenticated
voucher even for a zero-charge refund. Its reference phase store is in-memory;
production deployments must use durable, transactional channel state so restart
or concurrency cannot replay a deposit or claim.

**Mandate Bridge** (`AP2V02Binding`) is a narrow AP2 v0.2 profile for one
configured direct or autonomous flow. It enforces exact mandate type versions,
checkout-to-payment hash continuity, audience and currency allowlists, expiry,
NEXUS authority continuity, autonomous open-mandate key confirmation, and
explicit selective disclosures before invoking a trusted deterministic verifier.
That verifier—not the agent—must authenticate SD-JWT/JWS signatures, the
merchant checkout JWT, constraint evaluation, key confirmation, and replay or
single-use state. Signed receipt verification is a separate evidence step.

Mandate Bridge deliberately does not parse or trust cryptographic claims inside
the agent process. Production deployments must inject an independently operated
verifier with protected trust roots and durable replay, budget, recurrence, and
receipt state. AP2 mandate assurance remains below Runtime Proof.

**Card Trust Bridge** (`VisaTAPBinding`) recognizes only Visa TAP payment
requests whose RFC 9421 signature covers method, authority, path, and content
digest and whose signed payment container is linked by nonce, key, and algorithm.
Its contract is pinned to the dated `merchant-spec@2026-09-22` snapshot because
Visa's public Merchant Specification exposes no formal version identifier; the
related Web Bot Auth dependency is an active Internet-Draft, not an RFC.

A trusted deterministic verifier must prove signature validity, exact covered
components, freshness, replay/relay prevention, allowlisted-key trust, bounded
SSRF-safe discovery, and payment-container binding. Recognition establishes at
most Signed Request assurance. It does not prove user mandate, uncompromised
runtime, payment authorization, or settlement.

Production callers should use `bind_transaction` as the single verification and
canonical-binding operation. Every invocation reaches the durable replay
verifier; no accepted nonce is cached. The non-consuming `assurance_of` query
therefore reports `NONE`; verified assurance is returned only in the operation's
`BindingResult`.

Extend by **profile, never by making SafePay Exact generic**. Each new adapter
gets its own human name, technical type, conformance corpus, and explicit tuple:

`protocol version × scheme × network × asset × payment flow × finality model`.

Recommended sequence:

1. **SafePay Exact — Base** (`X402V2ExactEVMUSDCBaseBinding`): add chain-aware
   signature/authorization verification and a Coinbase-independent facilitator.
2. **SafePay Escrow** (`X402V2EscrowBinding`): model both settlement calls,
   deposit ceilings, refunds, deadlines, and mediated recourse separately.
3. **SafePay Variable** (`X402V2UptoBinding`): distinguish authorized maximum,
   actual charge, unused reservation release, and server-led settlement state.
4. **Mandate Bridge** (`AP2V02Binding`): map Checkout and Payment Mandates onto
   the Full-Term Approval Seal and require deterministic constraint evaluation.
5. **Card Trust Bridge** (`VisaTAPBinding`) and **Agent Token Bridge**
   (`MastercardAgenticTokenBinding`): add recognition without upgrading it to
   Runtime Proof.
6. **Portable Delegation Bridge** (`KYAOSBinding`): translate only dimensions
   with lossless attenuation; reject every unmapped scope axis.

Every extension must preserve four invariants: no value without a Spend Hold;
no credential without Runtime Proof at the configured floor; no settlement
outside the Full-Term Approval Seal; and no ambiguity that restores spend.
