<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.5](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.5-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: CLI 0.9](https://img.shields.io/badge/CLI-0.9-808080?style=flat-square)](../../safe2/docs/CHALLENGE-CLI.md)

[Framework Home](../../README.md) | [Cross-Pillar Controls](../../00-cross-pillar/) | [Examples Index](../README.md) | [Challenge Lab](../../challenges/) | [CLI](../../safe2/README.md)

> **Current framework context:** AI SAFE² v3.5. This example proves the controlled process evidence seam, not evaluator independence, OS containment, or framework conformance.
<!-- AI-SAFE2-UX:END -->

<!-- stack: Challenge 001 Controlled Executor -->
<!-- description: Reproducible process-boundary evaluator with pre-registration, independent grading, incomplete states, and cross-bound evidence receipts. -->

# Challenge 001 Controlled Executor Example

<!-- REPOSITORY-ROUTES:START -->
[![Framework context: v3.5](https://img.shields.io/badge/Framework_Context-v3.5-F6921E?style=flat-square)](../../README.md)
[Framework home](../../README.md) | [Topic map](../../docs/README.md) | [Mapping validation](../../docs/ROSETTA-STONE-V35.md) | [Component status](../../docs/V35-ECOSYSTEM-ADOPTION.md) | [Agent routes](../../llms.txt)
<!-- REPOSITORY-ROUTES:END -->

This deterministic evaluator demonstrates the JSON contract expected by
`safe2 challenge execute`. It receives one frozen scenario on standard input and
returns a decision plus authoritative fixture-state observation on standard output.
It does not call a model, network, production target, or third-party provider.

<!-- V35-RUNTIME-ADOPTION:START -->
## Apply v3.5 to this example

[Review the integration requirements](../../docs/V35-ECOSYSTEM-ADOPTION.md) before extending this runtime's claims. Identify every tool, provider, browser and direct API path that can commit an effect. Test current authority and environment binding, shared descendant limits, stop propagation, duplicate effects and independently observed outcomes. Keep this example's existing version and evidence limits until those tests pass.

[Try the bounded local authority fixture](../v35-authority/README.md) | [Read the child requirements](../../docs/CONTROLS-V3.5.md) | [Return to examples](../README.md)
<!-- V35-RUNTIME-ADOPTION:END -->

## Verify the example

```console
safe2 example verify challenge-controlled-executor
```

## Run the workflow yourself

Use the absolute path to your Python interpreter and replace `PYTHON` below:

```console
safe2 challenge plan 001 --executable PYTHON --arg examples/challenge-controlled-executor/executor.py --provider-name "AI SAFE2 controlled example" --provider-version 1.0 --producer-id ai-safe2-example --treatment controlled-reference --output execution-plan.json
safe2 challenge execute execution-plan.json --output-dir controlled-result --authorize-process-execution
safe2 challenge verify-execution controlled-result --plan execution-plan.json
safe2 challenge report controlled-result/challenge-run.json --output controlled-card.md
safe2 evidence manifest execution-plan.json controlled-result/challenge-source.json controlled-result/challenge-run.json controlled-result/execution-receipt.json --subject-id controlled-example --output controlled-manifest.json --strict
```

The evaluator and script argument are hashed into the plan. The receipt checks
their before/after identity and binds every request and successful response. Run
untrusted implementations only inside a separately managed OS/container boundary.

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Cross-Pillar Controls](../../00-cross-pillar/) | [Challenge CLI](../../safe2/docs/CHALLENGE-CLI.md) | [Framework Home](../../README.md)

*AI SAFE² v3.5 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
