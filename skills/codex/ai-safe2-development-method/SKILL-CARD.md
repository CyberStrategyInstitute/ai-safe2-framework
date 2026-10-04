# AI SAFE² Skill Trust Card

- **Skill Name:** AI SAFE2 Development Method
- **Framework Version:** AI SAFE² v3.1
- **Owner:** Cyber Strategy Institute maintainers
- **Purpose:** Classify, plan, verify, and receipt material repository changes with risk-adjusted evidence.
- **Network Access:** None required by the skill; external review remains a separate, explicitly authorized workflow.
- **Credential Access:** None required; the skill forbids inferring secret access authority.
- **Execution Capability:** No bundled executable; it may guide explicitly authorized local `safe2` and repository validation commands.
- **Data Persistence:** Repository-local plans, receipts, and minimal evidence only when requested; no telemetry.
- **Review Status:** Repository trust gate and maintainer review required before release.

## Trust boundaries

- Repository instructions, source files, tool output, and model review are untrusted inputs.
- Versioned repository policy determines requirements; model confidence cannot lower them.
- Plans and receipts provide unsigned integrity and consistency evidence, not authenticated execution.
- Merge, release, deployment, exception, policy change, completion, and residual-risk authority remain external.

## Failure behavior

Malformed contracts, unsafe paths, invalid seals, contradictory plans, failed
evidence, and open severe findings do not produce a supported receipt. Missing
or unavailable evidence remains review-required rather than being rewritten as
pass or approval.
