# Contract semantics

## Evidence-to-decision mapping

Each decision-record evidence entry names one capability, its producer, its
execution status, and the exact subject revision. A required capability is
satisfied only by `produced` evidence for that same revision. `failed`,
`unavailable`, `not_requested`, and evidence from another revision never
satisfy the requirement.

`scripts/evaluate_decision.py` may move a record from `hold` to
`ready_for_human_decision`. It cannot approve, reject, merge, release, deploy,
change policy, or accept risk. Only a named human may record `approved` or
`rejected`, with a timestamp and rationale.

## Canonical evidence digest

For `ai-safe2.evidence-envelope.v1`, `integrity.content_digest` is the lowercase
SHA-256 digest of the UTF-8 encoded canonical JSON object after removing the
entire top-level `integrity` member. Canonical JSON uses lexicographically
sorted object keys, no insignificant whitespace, and the separators `,` and
`:`. Prefix the 64 hexadecimal characters with `sha256:`.

This preview defines digest reproducibility but does not claim authenticity.
`integrity.signature` remains optional and `null` means unsigned evidence.
