# Agent Claim Audit

`safe2 evidence claims` compares explicit agent outcome claims with existing
SAFE² task-receipt criteria and creates both a machine artifact and human review
card.

```bash
safe2 schema export claim-audit-source-v1 --output claim-source.schema.json
safe2 evidence claims claims.json task-receipt.json \
  --output claim-audit.json --card claim-audit.md --strict
```

Each claim names its type, asserted outcome, and the receipt criterion IDs that
are supposed to support it. The audit labels the claim `evidence_consistent`,
`contradicted`, or `unverifiable`. It separately counts explicit `failed`,
`unavailable`, and `not_attempted` disclosures so a truthful limitation is not
mistaken for incomplete work hidden behind a success claim.

The source also declares the complete `receipt_input_sha256s` set. This binds
the audit to each supplied receipt's own canonical criteria-input document while
still allowing independently produced receipts for the same task to be combined.

There is intentionally no “honesty score.” A missing or contradictory receipt
does not prove intent or deception, while a consistent unsigned receipt can still
be fabricated. Coverage and contradiction ratios always retain their denominator
and apply only to the supplied claim set. Task completion remains human-owned and
`completion_verified` is always false.

For stronger evidence, precommit acceptance criteria, use authenticated collectors
where available, bind receipts to the exact system identity and revision, and keep
the evaluator independent from the agent making the claim.
