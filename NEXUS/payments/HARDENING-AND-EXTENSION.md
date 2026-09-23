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
