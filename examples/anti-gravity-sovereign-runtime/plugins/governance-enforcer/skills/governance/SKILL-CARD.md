# AI SAFE² Skill Trust Card

- **Skill Name:** ai-safe2-sovereign-governance (Antigravity governance-enforcer plugin example)
- **Framework Version:** v3.1
- **Owner:** Cyber Strategy Institute
- **Purpose:** Session-start and pre-tool governance checklist for Antigravity agents: path containment, network allowlist, command allowlist, secret-free writes, sandboxed subagents and memory-write screening, with deny-and-log on failure.
- **Network Access:** None required. The skill restricts outbound requests to an allowlist and forbids private IPs.
- **Credential Access:** None. It instructs the agent to refuse writes that contain credentials or secrets.
- **Execution Capability:** Instruction-only (`SKILL.md`); no scripts. `autoApply: true` and `loadOrder: 1`, so the platform loads it at every session start. Runtime enforcement is the separate `enforcement/safe_gateway.js` in the example workspace, if wired.
- **Data Persistence:** Instructs the agent to append denied actions to `enforcement/audit.log` in the workspace. It does not create other state.
- **Review Status:** Static trust gate APPROVE under `--strict` (2026-10-07, PR #395). Card authored by an agent; maintainer review pending.

## Trust boundaries

The skill states that it does not override platform system prompts or built-in tool safety controls. Its checks are advisory to the model; only the enforcement gateway blocks actions.
