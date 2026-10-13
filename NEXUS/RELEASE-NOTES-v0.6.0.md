# NEXUS v0.6.0: Denials That Hold

**GUARDIAN • AGBOM • OPA AUTHZ • REGISTRY-BOUND ACT TIERS**

NEXUS v0.6.0 closes enforcement gaps an adversarial battery found in v0.5.0. In each one,
NEXUS allowed something, or reported a check as satisfied, when it should not have.

## What changed

| Area | v0.5.0 | v0.6.0 |
|---|---|---|
| Guardian argument checks | 24 evasions allowed (encoded traversal, `id_ed25519`, IMDS as decimal or hex IP, key bytes in arguments, `curl \| sh`) | All 24 denied. Arguments are decoded and normalized before matching; five built-in detectors always run |
| HEAR reasoning (ACT-3/4) | `"x"` was accepted | Reasoning under 40 characters or 5 words is denied |
| Undeclared ACT tier | Treated as low risk | Treated as ACT-4, so HEAR applies (**breaking**, see below) |
| ACT tier source | Asserted by the caller | Bound to the agent's registered AIM v0.3 when `GuardianPolicy(aim_registry=...)` is set. A higher claim is denied; a lower claim cannot skip HEAR |
| Remote Guardian without `httpx` | Quietly ran the local default policy | Treated as unavailable, so the configured fail mode applies |
| AgBOM chain | A component edited inside a stored version still verified | Verification recomputes hashes. A changed MCP tool manifest is quarantined until approved |
| OPA authz | Undefined for 9 of 13 inputs; a `request` label could downgrade a durable write; deny rules did not gate `allow` | Always defined; most restrictive scope wins; deny gates allow. Loads on OPA 0.65 and 1.x |
| `nexus-score --v03-checks` | "10/10 verified" from imports and file presence | Tests behavior; reports NOT ASSESSED when evidence is missing |

## Breaking change

Callers that omit `act_tier` now get ACT-4 treatment. Declare the tier, register the
agent's AIM v0.3, or restore the old behavior with `GuardianPolicy(treat_undeclared_tier_as=None)`.
`nexus-score --v03-checks` exits 1 on a failed check and 2 on missing evidence.

## Install

```console
python -m pip install --upgrade nexus-a2a-sdk==0.6.0
python -c "import nexus_sdk; print(nexus_sdk.__version__)"
```

## Boundaries

- Pattern detectors are a floor. Paraphrased or novel payloads can still pass.
- AgBOM signatures remain a stub until ML-DSA-65 signing ships.
- The MCP adapter (`adapters/mcp/adapter.py`) is still fail-closed scaffolding, not production-ready.
- Results are self-assessed by the maintainers' tooling, not independent validation.

Full detail: [CHANGELOG](CHANGELOG.md) · Assessment record: `docs/assessments/2026-10-06-false-assurance/`
