# Governance Core

Use this reference for agent classification, mandatory governance flags, and risk scoring.

## ACT Tiers

| Tier | Summary | HEAR | CP.9 |
| --- | --- | --- | --- |
| ACT-1 | Assisted. Human reviews all outputs before action. | No | No |
| ACT-2 | Supervised. Human checkpoints for critical actions. | No | No |
| ACT-3 | Autonomous. System can act with limited post-hoc review. | Required | If spawning |
| ACT-4 | Orchestrator. System manages or delegates to other agents. | Required | Required |

## Mandatory Governance Rules

For any agent design:

1. State the ACT tier explicitly.
2. If ACT-3 or ACT-4, require `CP.10` HEAR before deployment.
3. If the system can spawn, delegate to, or manage other agents, require `CP.9`.
4. If autonomy, broad tool access, financial impact, health impact, or critical infrastructure is in scope, require `CP.8` deployment gating.

## HEAR Doctrine

Use `CP.10` when the system reaches ACT-3 or ACT-4 or performs high-consequence actions.

Expected characteristics:

- HEAR is a named individual, not a team mailbox or generic role
- The approval flow is fail-closed
- High-consequence actions pause for explicit approval
- Approval should be cryptographically attributable where the host platform supports it

## Agent Replication Governance

Use `CP.9` whenever an agent can create, invoke, or chain other agents.

Expected controls:

- Track parent-child lineage for every delegated agent action
- Narrow privileges at each hop
- Limit delegation depth
- Provide a fast kill path for the full delegation tree
- Record replication lineage in the agent inventory and trace logs

## Combined Risk Score

When a vulnerability or incident includes AI posture and agentic autonomy, use:

`Combined Risk Score = CVSS + ((100 - Pillar_Score) / 10) + (AAF / 10)`

Where:

- `CVSS` is the base vulnerability score
- `Pillar_Score` is the AI SAFE2 posture score from 0 to 100
- `AAF` is the agentic amplification factor

If the full AAF is unavailable, say that the score is partial or estimated and explain the assumptions.

## Priority Control Checks

When reviewing agent code or architecture, prioritize these questions:

- Are untrusted inputs, retrieved content, and tool results treated as indirect injection surfaces?
- Are secrets ever placed into prompts, memory, logs, or downstream context?
- Can the system write to memory, tools, or external systems without approval or policy checks?
- Is semantic execution tracing present for material actions?
- Are recursion, loops, and swarm fan-out constrained?
- Are tool misuse, anomaly detection, and human approvals in place for high-impact actions?
