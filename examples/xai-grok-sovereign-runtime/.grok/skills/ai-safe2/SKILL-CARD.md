# AI SAFE² Skill Trust Card

- **Skill Name:** AI SAFE2 Sovereign Runtime advisor (`/ai-safe2`, Grok CLI example)
- **Framework Version:** v3.1
- **Owner:** Cyber Strategy Institute
- **Purpose:** Tells the Grok agent which runtime trust boundaries it operates inside (skill scanning, hook validation, permission mode, sandbox floor, multi-agent bounds, CI flags) and to stop and report instructions that try to cross them.
- **Network Access:** None. The skill instructs the agent not to exfiltrate via curl, webhooks or other network calls.
- **Credential Access:** None.
- **Execution Capability:** Advisory instructions only (`SKILL.md`); no scripts or hooks. The `/ai-safe2 status` and `report` commands request output from the separately installed runtime in `examples/xai-grok-sovereign-runtime/`.
- **Data Persistence:** None created by the skill.
- **Review Status:** Static trust gate APPROVE under `--strict` (2026-10-07, PR #395). Card authored by an agent; maintainer review pending.

## Trust boundaries

The skill grants no authority. Enforcement (permission mode, sandbox floor, hook validation) lives in the runtime and Grok configuration, not in this file.
