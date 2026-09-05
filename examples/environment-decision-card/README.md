<!-- stack: Environment Discovery, Drift, Evidence, and Policy -->
<!-- description: Privacy-safe baseline-to-decision workflow with human cards and a unified evidence manifest. -->

<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [CLI](../../safe2/README.md)

> **Current framework context:** AI SAFE² v3.1. This executable example provides decision support and does not independently establish organizational maturity or framework conformance.
<!-- AI-SAFE2-UX:END -->

# Environment Decision Card Example

This executable example demonstrates the complete local evidence workflow
without inspecting the user's real harness configuration. It creates a small
temporary project, captures a hashed baseline, makes one controlled instruction
change, detects the drift, evaluates a policy, writes Markdown and HTML Decision
Cards, records sanitized friction evidence, and produces a unified run manifest.

```bash
python smoke_test.py
```

To retain the generated artifacts for review:

```bash
python smoke_test.py --output-dir ./validation-output
```

Expected result:

- policy decision: `DENY`, because the example policy allows zero drift;
- the decision command returns exit `1` after writing its evidence;
- the changed `AGENTS.md` is reported rather than silently ignored;
- the final run manifest contains only valid artifacts;
- no conformance, certification, or universal-safety claim is made.

The example is instructional evidence, not a production policy recommendation.
Organizations should define thresholds, required targets, evidence retention,
owners, and exceptions for their own context.

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [CLI](../../safe2/README.md)

*AI SAFE² v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
