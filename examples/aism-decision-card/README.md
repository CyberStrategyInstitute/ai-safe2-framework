<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.5](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.5-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [CLI](../../safe2/README.md)

> **Current framework context:** AI SAFE² v3.5. This executable example provides decision support and does not independently establish organizational maturity or framework conformance.
<!-- AI-SAFE2-UX:END -->

<!-- stack: AISM Decision Support -->
<!-- description: Executable assessment demonstrating evidence-aware AISM scoring and a human Decision Card. -->

# AISM Decision Card Example

<!-- REPOSITORY-ROUTES:START -->
[![Framework context: v3.5 candidate](https://img.shields.io/badge/Framework_Context-v3.5_candidate-F6921E?style=flat-square)](../../README.md)
[Framework home](../../README.md) | [Topic map](../../docs/README.md) | [Mapping validation](../../docs/ROSETTA-STONE-V35.md) | [Component status](../../docs/V35-ECOSYSTEM-ADOPTION.md) | [Agent routes](../../llms.txt)
<!-- REPOSITORY-ROUTES:END -->

This example turns a bounded agent environment assessment into two products:

- canonical JSON for agents and governance systems;
- a compact Markdown Decision Card for accountable humans.

It demonstrates facts, assumptions, conflicts, unknowns, history, alternatives,
an attributed outcome estimate, and a recommendation. The example is decision
support; it is not a claim of organizational maturity or full AI SAFE²
conformance.

<!-- V35-RUNTIME-ADOPTION:START -->
## Apply v3.5 to this example

[Review the integration requirements](../../docs/V35-ECOSYSTEM-ADOPTION.md) before extending this runtime's claims. Identify every tool, provider, browser and direct API path that can commit an effect. Test current authority and environment binding, shared descendant limits, stop propagation, duplicate effects and independently observed outcomes. Keep this example's existing version and evidence limits until those tests pass.

[Try the bounded local authority fixture](../v35-authority/README.md) | [Read the child requirements](../../docs/CONTROLS-V3.5.md) | [Return to examples](../README.md)
<!-- V35-RUNTIME-ADOPTION:END -->

## Run

```bash
cd examples/aism-decision-card
safe2 aism score assessment.json --format markdown --output decision-card.md
safe2 aism score assessment.json --format json --output decision.json
safe2 aism score assessment.json --format html --output decision-card.html
safe2 example verify aism-decision-card
python smoke_test.py
```

## Expected decision

The example returns `HOLD` because it intentionally contains a critical
conflict between a declared fail-closed policy and observed runtime behavior.
Resolving the conflict in the source assessment changes the recommendation;
the expected result is therefore testable rather than decorative.

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [CLI](../../safe2/README.md)

*AI SAFE² v3.5 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
