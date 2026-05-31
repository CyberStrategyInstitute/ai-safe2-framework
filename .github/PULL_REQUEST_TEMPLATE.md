## Summary

<!-- One paragraph: what does this PR do and why? -->

## Type of Change

- [ ] Bug fix
- [ ] New feature (non-breaking)
- [ ] Breaking change (requires CHANGELOG update and migration note)
- [ ] Protocol specification change (requires AI SAFE2 v3.0 mapping)
- [ ] Constitutional Amendment (AISM Invariant or HEAR Doctrine -- requires supermajority)
- [ ] Documentation / governance
- [ ] Dependency update

## AI SAFE2 v3.0 Mapping

<!-- Which controls does this change affect or enable? -->
<!-- E.g., S1.3 Guardian per-call enforcement, A2.3 AgBOM provenance -->

| Control ID | Control Name | Change |
|:-----------|:-------------|:-------|
| | | |

## Compliance Framework Impact

<!-- Does this affect any of the 32 mapped compliance frameworks? -->
<!-- E.g., EU AI Act Article 14, NIST AI RMF Govern 1.2, ISO 42001 -->

## Testing

- [ ] All 189 existing tests pass (`pytest tests/ -q`)
- [ ] New tests added for new behavior
- [ ] `--v03-checks` compliance checker passes (10/10)
- [ ] All three examples run clean
- [ ] Em dash scan clean (no `--` or en/em dashes in prose or code)

```
cd sdk/python
python -m pytest tests/ -q
PYTHONPATH=. python ../../compliance/scoring/nexus-score.py --v03-checks
PYTHONPATH=. python ../../examples/sovereign_gateway.py
PYTHONPATH=. python ../../examples/acs_bridge.py
PYTHONPATH=. python ../../examples/personal_agent.py
```

## OPA Policy Changes

<!-- If opa/ files changed: include example input/expected output -->

```json
// Input:
{}

// Expected output:
{}
```

## CHANGELOG

- [ ] Added entry under `[Unreleased]` in CHANGELOG.md

## DCO Sign-Off

By submitting this pull request, I certify that my contribution is made under the terms of the Apache 2.0 license and I have read and agree to the Developer Certificate of Origin in CONTRIBUTING.md.

- [ ] All commits are signed off (`Signed-off-by: Name <email>`)
