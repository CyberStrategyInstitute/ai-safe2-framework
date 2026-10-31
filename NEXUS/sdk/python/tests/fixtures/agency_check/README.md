# Agency Check receipt test vectors

Signed by Agency Check's own `makeNor` (`src/nexus/nor.ts`, wt-acm44 @ 11a4b0a)
with a throwaway Ed25519 key generated for this fixture. The private key was
never written to disk. Only the public JWKS is kept here. These receipts carry
no user content: the hashed arguments were a fixed placeholder.

- `cael_envelope_hash` = `binding_digest(sha256("nexus-apay-acr fixture transaction"))`
  = binding for transaction digest
  `38f6fbfee802b68c272763d7cf1a5cf2be95f1b59e3d3dcbe2d6468c85f772b3`.
- `receipt-allow.json`: the check ran (`outcome: allow`).
- `receipt-service-paused.json`: the check was refused because the operator kill
  switch was on (`outcome: deny`, `deny_reason: kill_switch`).

Cross-checked with Agency Check's `scripts/verify-receipt.mjs <receipt> jwks.json`
(hash_ok and signature_ok true, exit 0 for both) and with
`tests/test_apay_agency_check.py`.
