# Change Attribution

[CLI guide](../safe2/README.md) | [Assessment scope](./ASSESSMENT-SCOPE.md) | [System identity](./SYSTEM-IDENTITY.md)

`safe2 evidence attribute` compares findings from an explicitly trusted baseline
with findings from a proposed revision. It separates inherited, introduced,
changed, resolved, and unknown findings without claiming causation or framework
conformance.

## Why it matters

A current scan alone cannot tell a reviewer whether a finding was introduced by
the proposed change. A missing finding is not demonstrably resolved when either
assessment had incomplete coverage. This workflow keeps those states separate
and binds both sides to the same declared agent system and exact scope artifacts.

## Command

```text
safe2 evidence attribute change.json \
  --system-identity system-identity.json \
  --baseline-scope baseline-scope.json \
  --current-scope current-scope.json \
  --output change-attribution.json \
  --strict
```

The source contains normalized findings for both revisions. A `finding_key` is
the caller's stable correspondence key. Duplicate keys are rejected. The
baseline must declare `trusted: true` and document its `trust_basis`. Each scope
file is bound by its exact SHA-256 digest.

## Interpretation

| Status | Meaning |
| --- | --- |
| `inherited` | The normalized finding is identical on both complete assessments. |
| `introduced` | It appears only in the current complete assessment. |
| `changed` | The same finding key exists on both sides, but normalized evidence differs. |
| `resolved` | It appears only in the baseline complete assessment. |
| `unknown` | Either side declares incomplete coverage, so direction is not supportable. |

`--strict` writes the result and exits with status 1 when unknown attribution
remains. This preserves the evidence needed to diagnose the failure.

## Evidence boundary

The command does not run scanners, authenticate the baseline, establish that a
change caused a finding, verify deployed contents, prove a control effective, or
claim AI SAFE² conformance. Retain provider-native evidence with the source.
