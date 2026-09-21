<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: CLI 0.8](https://img.shields.io/badge/CLI-0.8-808080?style=flat-square)](../../docs/AISM-REMEDIATION.md)

[Framework Home](../../README.md) | [Cross-Pillar Controls](../../00-cross-pillar/) | [Examples Index](../README.md) | [AISM](../../AISM/) | [CLI](../../safe2/README.md)

> **Current framework context:** AI SAFE² v3.1. This example validates remediation decision support. It does not authorize work or establish organizational conformance.
<!-- AI-SAFE2-UX:END -->

<!-- stack: AISM Remediation Decision Support -->
<!-- description: Executable evidence-bound AISM remediation plan with ownership, alternatives, exit criteria, history, and human decision gates. -->

# AISM Remediation Example

This example proves the CLI 0.8 planning contract from end to end. It creates a
bounded system identity and deployment scope, scores a complete illustrative
AISM assessment, binds a remediation source to the exact artifact bytes, and
produces a canonical plan plus a human card.

The fixture intentionally uses synthetic evidence. Its
`ready_for_human_decision` result means only that the supplied fixture is
complete and internally consistent. It does not prove implementation,
authorize remediation, or establish AI SAFE² conformance.

## Run

```bash
cd examples/aism-remediation
python smoke_test.py
safe2 example verify aism-remediation
```

For operational use, follow the complete
[AISM remediation guide](../../docs/AISM-REMEDIATION.md) and replace every
fixture with evidence from the exact system and deployment scope under review.

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [AISM](../../AISM/) | [CLI](../../safe2/README.md)

*AI SAFE² v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
