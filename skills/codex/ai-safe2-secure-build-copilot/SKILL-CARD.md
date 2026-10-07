# AI SAFE² Skill Trust Card

- **Skill Name:** AI SAFE² Secure Build Copilot (Codex package)
- **Framework Version:** v3.1
- **Owner:** Cyber Strategy Institute
- **Purpose:** Codex packaging of the AI SAFE² review skill: apply AI SAFE² controls, ACT tiers, HEAR and replication governance, and evidence requirements to AI system design, code review, and compliance mapping.
- **Network Access:** None required by the skill documents; any MCP connectivity is configured separately by the operator.
- **Credential Access:** None required; secrets must stay outside model context and follow applicable AI SAFE² controls.
- **Execution Capability:** Advisory instructions and reference files only (`SKILL.md`, `references/`, `agents/openai.yaml`); no scripts. `agents/openai.yaml` sets `allow_implicit_invocation: true`, so Codex may load the skill without an explicit mention. Runtime actions depend on separately authorized client capabilities.
- **Data Persistence:** None created by the skill documents; deployments govern persistence with v3.1 `request`, `handle_scoped`, `durable`, and `swarm_shared` semantics.
- **Review Status:** Maintainer reviewed for AI SAFE² v3.1 consistency (2026-10, PR #393); static trust gate APPROVE under `--strict`.

## Trust boundaries

The skill grants no authority. Tool access, credentials, network permissions, execution rights, and persistence remain external capabilities that must be independently authorized and evidenced.

## Relationship to the canonical skill

The canonical, platform-neutral skill is [`skills/ai-safe2-secure-build-copilot/`](../../ai-safe2-secure-build-copilot/SKILL.md). This package is the Codex adapter and carries a shorter workflow plus reference files.
