# Agentic Payment Adapter Guide

This guide is the operational entry point for humans and software agents using
the CP.5.APAY reference adapters. Read the profile [status and acceptance
gates](README.md) before treating any result as deployable assurance.

## Choose the narrowest profile

| Human name | Technical name | Use it for | Never infer |
| --- | --- | --- | --- |
| SafePay Exact | `X402V2ExactEVMUSDCBinding` | Structural x402 v2 exact EVM/USDC shadow evaluation | Live signature or settlement verification |
| SafePay Verified | `X402V2ExactEVMUSDCAuthoritativeBinding` | Authenticated facilitator or chain evidence | Runtime integrity or user intent |
| SafePay Variable | `X402V2UptoBinding` | Maximum-versus-actual charge and reservation release | Escrow or recourse |
| SafePay Escrow | `X402V2EscrowBinding` | Deposit, release, refund, and mediated finality | Native rail reversibility |
| Mandate Bridge | `AP2V02Binding` | AP2 v0.2 mandate and receipt evidence | Workload integrity |
| Card Trust Bridge | `VisaTAPBinding` | Visa TAP request recognition | Payment authorization or settlement |
| Agent Token Bridge | `MastercardAP4MBinding` | Authenticated AP4M verifier evidence | Compatibility with a private token schema |
| Portable Delegation Bridge | `KYAOSBinding` | KYA-OS identity and delegated-authority evidence | Payment settlement |

## Required integration pattern

1. Build the NEXUS canonical transaction and authority grant first.
2. Select one exact adapter profile and configure explicit network, asset,
   counterparty, verifier, assurance, and finality allowlists.
3. Implement the adapter's verifier protocol with deterministic cryptography,
   fresh revocation state, and an atomic shared replay store. Never use an LLM
   as the verifier.
4. Treat `verify_authority` as preflight where documented. For **SafePay
   Verified**, authorization requires both an `ACCEPT` from
   `verify_authority(payload)` and an `ACCEPT` from the subsequent
   `bind_transaction(payload, canonical_digest)` call; never treat the binding
   result alone as authoritative verification. Use `bind_transaction` for the
   canonical binding decision and stop if either result rejects or halts.
   State consumption is profile-specific: SafePay Verified's adapter methods
   are stateless, so its authoritative verifier must enforce freshness and
   replay policy atomically at its own trust boundary.
5. Read verified assurance from the returned `BindingResult`; metadata methods
   intentionally return conservative answers when a query could consume state.
6. Keep Runtime Proof, Spend Hold, Human Shield, cumulative exposure, evidence,
   and revocation-tree enforcement in the NEXUS gateway above the adapter.
7. Halt on unknown, malformed, unavailable, stale, ambiguous, or unmapped
   evidence. Do not fall back to a weaker adapter.

## Verification

From the repository root, set `PYTHONPATH=NEXUS/sdk/python` and run:

```console
python -m pytest NEXUS/sdk/python/tests -q
python -m mypy --config-file NEXUS/pyproject.toml NEXUS/sdk/python/nexus_sdk/payments
```

The adapter corpus includes positive vectors, substitution attacks, malformed
runtime evidence, truthy-value bypass attempts, replay behavior, scope mapping,
privacy checks, and RailGuard conformance. Passing these local tests does not
replace live counterparty conformance, key custody, operational monitoring,
incident response, or the [MVP acceptance gates](README.md#mvp-acceptance-gates).

## Safe extension rule

Add a new human-named, technically named profile; do not broaden an existing
profile. Declare its exact protocol version, scheme, network, asset, flow,
finality, verifier boundary, assurance ceiling, privacy behavior, unsupported
claims, positive vectors, and adversarial vectors. Run the Verifier Contract
Shield before proposing production use. When the repository's optional
external-review provider is available, complete that review too; otherwise
follow the repository's documented fallback review process.
