# Challenge 001 Harness
### Executable offline fixtures and the path to an isolated live study

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../../README.md)
[![Challenge Lab](https://img.shields.io/badge/Module-Challenge_Lab-820F1A?style=flat-square)](../../README.md)
[![Scope](https://img.shields.io/badge/Scope-Offline_fixture_pilot-808080?style=flat-square)](../../../docs/CHALLENGE-CLI.md)

[Framework Home](../../../README.md) | [Cross-Pillar Governance](../../../00-cross-pillar/README.md) | [AISM](../../../AISM/README.md) | [NEXUS](../../../NEXUS/README.md) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

[Challenge 001](../README.md) | [CLI Guide](../../../docs/CHALLENGE-CLI.md) | [Rules of Engagement](../ROE.md) | [Evidence Contract](../EVIDENCE.md)

---

## Available now

The executable implementation lives in [`safe2/challenge/`](../../../safe2/challenge/),
with CLI commands in [`safe2/commands/challenge.py`](../../../safe2/commands/challenge.py)
and versioned protocol/schema resources in [`safe2/data/`](../../../safe2/data/).
This folder remains the Challenge 001 study's documentation entry point, not a
second CLI installation or a separate runtime.

```console
safe2 challenge run 001 --output fixture-run.json
safe2 challenge verify fixture-run.json
safe2 challenge report fixture-run.json --output fixture-card.md
```

The first backend mutates only inert dictionary state. It covers six known cases
under uncontrolled, conventional and narrowly scoped `safe2-reference` policies.
It does not launch agents, operate on real files/processes/accounts, call cloud
services, or execute TENIR. The reference fixture is not full T4 or NEXUS.

Provider-neutral imports retain original records and distinguish shadow decisions
from enforcement. A packaged TENIR specimen demonstrates a **synthetic, invented
adapter contract**, not a verified upstream integration. Comparisons gate on
protocol and case/trial coverage; matching outcomes do not establish independent
replication. See the [complete command guide](../../../docs/CHALLENGE-CLI.md).

## Live backend: not implemented by this pilot

The full study still needs a harness that creates disposable isolated environments,
assigns conflicting and legitimate agent objectives, exposes controlled inert
tools, enforces independent stop/resource limits, captures authoritative evidence,
and tears down targets after retention requirements are met. It must satisfy the
[Rules of Engagement](../ROE.md) and frozen preregistration before live execution.

Fixture mechanics do not promote Challenge 001 to scenario validation or independent
replication, and do not award framework conformance or AISM scores. Preserve
negative and null results; conventional controls matching the reference at lower
complexity are valuable findings.

---

[Challenge 001](../README.md) | [CLI Guide](../../../docs/CHALLENGE-CLI.md) | [Framework Home](../../../README.md)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
