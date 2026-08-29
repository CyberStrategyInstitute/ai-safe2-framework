# AI SAFE² Skill Trust Card

- **Skill Name:** AI SAFE² Secure Build Copilot
- **Framework Version:** v3.1
- **Owner:** Cyber Strategy Institute
- **Purpose:** Apply AI SAFE² controls and evidence requirements to AI system design, build, review, and governance workflows.
- **Network Access:** None required by the skill document itself; optional MCP connectivity is configured separately by the operator.
- **Credential Access:** None required by the skill document; secrets must remain outside model context and follow applicable AI SAFE² controls.
- **Execution Capability:** Advisory instructions only; runtime actions depend on separately authorized client, MCP, scanner, or gateway capabilities.
- **Data Persistence:** No persistence is created by the skill document itself; deployments must govern persistence using v3.1 request, handle_scoped, and durable semantics.
- **Review Status:** Maintainer reviewed for AI SAFE² v3.1 release consistency.

## Trust boundaries

The skill does not grant authority. Tool access, credentials, network permissions, execution rights, and persistence remain external capabilities that must be independently authorized and evidenced.

## Profile dependencies

MCP-connected deployments should use the CP.5.MCP v3.1 profile aligned to MCP `2026-07-28`. NEXUS is CSI's first-party reference implementation, not a mandatory conformance dependency.
