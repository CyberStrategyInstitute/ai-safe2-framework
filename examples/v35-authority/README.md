<!-- stack: Python SQLite local authority fixture -->
<!-- description: Synthetic transactional effects with exact approvals, current conditions, ancestor budgets, idempotency and descendant revocation. -->

<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.5](https://img.shields.io/badge/AI_SAFE2-v3.5-F6921E)](../../README.md)
[![Reference](https://img.shields.io/badge/Reference-820F1A)](../../docs/CONTROLS-V3.5.md)
[![Synthetic](https://img.shields.io/badge/Synthetic-808080)](../../challenges/002-v35-commit-boundary/README.md)
[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/README.md)
<!-- AI-SAFE2-UX:END -->

# v3.5 local authority and effect fixture

<!-- REPOSITORY-ROUTES:START -->
[![Framework context: v3.5 candidate](https://img.shields.io/badge/Framework_Context-v3.5_candidate-F6921E?style=flat-square)](../../README.md)
[Framework home](../../README.md) | [Topic map](../../docs/README.md) | [Mapping validation](../../docs/ROSETTA-STONE-V35.md) | [Component status](../../docs/V35-ECOSYSTEM-ADOPTION.md) | [Agent routes](../../llms.txt)
<!-- REPOSITORY-ROUTES:END -->

Run `python examples/v35-authority/demo.py` from an installed source checkout. The fixture grants a child narrower authority, binds a synthetic operator approval to the exact action, commits a local resource effect and budget together, returns the first receipt for a duplicate request, and prevents subsequent execution after root revocation.

The HMAC approval helper is reusable protocol logic. It authenticates the approval message. The integrating application must authenticate and authorize its human approver, protect the key and database, and deliver the approval over its reviewed channel. The helper supplies no user identity proof or second authentication factor. There is no automatic email, webhook or network request.

The resource table is synthetic. Tests verify serial admission and local postconditions with a separate database observation in the same fixture. External transactions, queues, multi-host containment and an independent evidence collector need their own bindings and tests. The relevant controls remain applicable even where that binding is unimplemented.

[Research](../../research/README.md) | [Controls](../../docs/CONTROLS-V3.5.md)

<!-- AI-SAFE2-UX-FOOTER:START -->
[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/README.md)
<!-- AI-SAFE2-UX-FOOTER:END -->
