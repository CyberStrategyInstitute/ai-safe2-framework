# CP.5.EVAL | v3.5 candidate profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## E5.1 | C16

C04 owns the assurance rule. P4 and P5 own live observation and validation. Parallel core controls would blur independent evidence and model-justification signals.

- **E5.1.R01** Protect evaluation inputs, test selection, graders and live monitors from agent modification.
- **E5.1.R02** Evaluate actions and effects independently of model justification; record shared-source and evaluation-awareness limitations.

**Acceptance** Evaluation integrity and protected monitoring. Separate grader custody, test recognition, contaminated results and false completion.

[Research](../research/040_v35_c16.md)

## CP.5 | C27

Evaluation and training environments need dedicated isolation, scope, stopping and evidence custody. Reuse C04 and C16. Profile-specific rules prevent transferring assumptions to ordinary deployments.

- **CP.5.R05** For evaluation environments, isolate runs, shared package services, secrets, graders and external destinations.
- **CP.5.R06** Enforce the authorized scope and verified containment independently of tested-agent behavior.

**Acceptance** Evaluation infrastructure as an operating boundary. Verify scope and independent results on synthetic infrastructure.

[Research](../research/051_v35_c27.md)

## CP.13 | C48

Independent custody alone cannot establish evaluator competence or representative tests. The evidence contract needs reviewer capability, conflicts and dispute handling. Independent review adds cost and may remain unavailable.

- **CP.13.R04** Record reviewer competence, tool scope, financial or organizational conflicts and access limits.
- **CP.13.R05** Protect test selection, grader configuration and evidence custody from the evaluated agent.
- **CP.13.R06** Preserve reviewer disagreement and its adjudication with traceable reasons.
- **CP.13.R07** Retest after material changes to a benchmark, evaluator or assurance provider.

**Acceptance** Use a flawed grader, conflicted reviewer and contaminated test set. Verify that their verdict cannot silently become independent assurance.

[Research](../research/072_v35_c48.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
