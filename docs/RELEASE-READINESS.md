# Release-Readiness Card

[CLI guide](../safe2/README.md) | [Assessment scope](./ASSESSMENT-SCOPE.md) | [Change attribution](./CHANGE-ATTRIBUTION.md)

`safe2 evidence readiness` combines the system identity, assessment boundary,
change attribution, required-check status, residual risks, owners, actions,
assumptions, and rollback plan into canonical agent JSON and a readable Markdown
card. It supports—but never replaces—the named human release decision.

Start from [`safe2/data/release-readiness-source-demo.json`](../safe2/data/release-readiness-source-demo.json)
and replace every placeholder with evidence for the exact candidate revision.

## Quick start

```text
safe2 evidence readiness readiness-source.json \
  --system-identity system-identity.json \
  --assessment-scope assessment-scope.json \
  --change-attribution change-attribution.json \
  --output release-readiness.json \
  --card release-readiness.md \
  --strict
```

Outputs must be new, distinct, non-link paths. `--strict` writes both artifacts
and exits 1 unless the result is `ready_for_human_decision`.

## Status logic

| Status | Trigger | Meaning |
| --- | --- | --- |
| `hold` | Failed/cancelled required check, unsafe/conflicting/truncated scope, open critical/high risk, or introduced/changed critical/high finding | Do not release until blockers are resolved and reassessed. |
| `review` | Missing/pending/unavailable check, partial scope, unknown attribution, or open lower-severity risk | Evidence or an explicit human risk decision is still required. |
| `ready_for_human_decision` | No supplied technical blocker or gap remains | The named owner may decide; release is not automatically authorized. |

Accepted risks remain visible but do not independently block the technical gate.
The decision owner remains accountable for determining whether the acceptance is
valid, authorized, and within risk appetite.

## Evidence boundary

The workflow hashes and validates its inputs. It does not authenticate hosted
check claims, execute tests, discover all risks, prove causation or control
effectiveness, authorize release, or establish AI SAFE² conformance.
