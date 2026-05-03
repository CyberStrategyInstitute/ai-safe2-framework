# Codex Sovereign Runtime v2

**Framework:** AI SAFE2 / AISM Level 4 (Sovereign Runtime Governance)

**Version:** 2.0

**Source Pattern:** Adapted from the Claude Code sovereign runtime example in the AI SAFE2 framework and optimized using the OpenClaw v2.0 governance model.

**Audience:** Individual developers, SMBs, enterprise engineering teams using OpenAI Codex CLI or the Codex desktop app.

---

## Why This Exists

The Claude example proves the core AI SAFE2 point: the trust boundary cannot live only inside a vendor agent. For Codex, the same principle applies, but the control surface is different.

Codex currently exposes strong sandbox and approval controls, project and user `config.toml`, profiles, MCP server configuration, and notification hooks. It does **not** provide Claude-style per-tool pre/post hooks. That means a Codex sovereign runtime must move enforcement outward into:

- launch wrappers that block unsafe startup modes
- managed `config.toml` baselines
- hardened `AGENTS.md` policy files
- external notification logging
- config and MCP audits
- CI wrappers that fail closed

This package implements that pattern.

---

## Evaluation Of The Claude Example

The upstream `claude-code-sovereign-runtime` example is strong on architecture and clear in its trust-boundary design.

What carries over directly:

- externalized controls are the right model
- inventory, audit, fail-safe, and monitoring remain necessary
- managed policy baselines matter more than ad hoc prompts
- MCP and CI/CD are part of the runtime, not separate concerns

What does **not** carry over directly:

- Codex has no native equivalent to Claude's pre-tool and post-tool hooks
- Codex uses `AGENTS.md` and `config.toml`, not `CLAUDE.md` plus `settings.json`
- Codex runtime hardening is centered on `approval_policy`, `sandbox_mode`, `profiles`, wrapper-enforced launch flags, and MCP governance

Net: the Claude package is the correct **control philosophy**, but not the correct **implementation surface** for Codex. This package replaces hook-driven controls with Codex-native and OS-level controls.

---

## What Changed After Real-World Validation

This package was tested against a live Windows Codex installation. That validation changed the design:

- global `~/.codex/config.toml` mutation is now **optional**, not the default
- wrapper-scoped enforcement is the primary deployment mode
- Codex executable discovery must not rely on `PATH` alone
- logs and summaries must fail over to a local workspace directory
- profile-based launch controls are less reliable than explicit launch flags

This is the same design lesson the OpenClaw example encodes at a higher maturity level: governance files help, but the strongest controls are the ones enforced at the execution boundary.

---

## What This Package Implements

### The Five AI SAFE2 Pillars Applied To Codex

```text
Pillar 1: Sanitize & Isolate    -> scripts/codex-jit-wrapper.ps1 + IDENTITY.md + TOOLS.md
Pillar 2: Audit & Inventory     -> scripts/audit-codex-install.ps1 + scripts/scan-dangerous-config.ps1 + EVALUATION.md
Pillar 3: Fail-Safe & Recovery  -> wrapper-scoped launch controls + ci-cd/github-actions-codex-safe.yml
Pillar 4: Engage & Monitor      -> monitoring/codex-notify.ps1 + monitoring/summarize-session.ps1 + HEARTBEAT guidance in EVALUATION.md
Pillar 5: Evolve & Educate      -> QUICKSTART.md + ARTICLE.md + SOUL.md + AGENTS.md
```

### Controls Implemented

| Control | File | Risk Addressed |
|---|---|---|
| Deny dangerous bypass startup | `scripts/codex-jit-wrapper.ps1` | `--dangerously-bypass-approvals-and-sandbox` |
| Enforce approval + sandbox baseline | `scripts/codex-jit-wrapper.ps1` | Overly broad execution |
| Narrow MCP inventory | `managed-settings/config.team.toml` + `TOOLS.md` | Adversarial or excess MCP exposure |
| Audit Codex installs and versions | `scripts/audit-codex-install.ps1` | Unknown runtime surface |
| Scan risky config settings | `scripts/scan-dangerous-config.ps1` | Unsafe local overrides |
| Notification-based external logging | `monitoring/codex-notify.ps1` | Invisible session outcomes |
| Session summary and alert rollup | `monitoring/summarize-session.ps1` | Missing audit evidence |
| Identity anchoring | `IDENTITY.md` | Identity replacement and prompt role drift |
| User data classification | `USER.md` | Context-insensitive handling of sensitive user data |
| Subagent governance | `SUBAGENT-POLICY.md` | ACT-4 delegation drift and privilege sprawl |
| Hardened project policy | `AGENTS.md` | Prompt injection and unsafe operator behavior |
| Operating constitution | `SOUL.md` | Value drift and inconsistent decision-making |
| Fail-closed CI template | `ci-cd/github-actions-codex-safe.yml` | Unreviewed autonomous CI execution |
| MCP review checklist | `integrations/mcp-allowlist.md` | Unvalidated external tools |
| Runtime validation checklist | `EVALUATION.md` | Unverified claims about what is actually enforced |

---

## Architectural Principle

```text
WITHOUT this package:
  User Intent -> Codex internal policies -> Your workstation / repo / network

WITH this package:
  User Intent -> [Wrapper + Core Governance Files + Audits] -> Codex -> [External Notifications + Evaluation] -> Your infrastructure
                    ^                                          ^
                    | controls you own                         | logs Codex cannot retroactively rewrite
```

Codex's internal controls are still useful, but AI SAFE2 requires the runtime governor to live outside the model-controlled reasoning loop. For Codex today, that means startup enforcement, config governance, and external monitoring rather than tool hooks.

---

## Compatibility

| Deployment Type | Supported |
|---|---|
| Codex CLI on Windows | Yes |
| Codex CLI on macOS/Linux | Yes, via bash wrapper templates |
| Codex desktop app | Partially |
| Codex in CI/CD | Yes |
| Codex with MCP servers | Yes |
| Codex multi-agent workflows | Yes, with tighter governance |

**Desktop app note:** the app honors project governance files and Codex config behavior, but wrapper-enforced launch controls are strongest when you launch via CLI or CI.

---

## ACT Tier Assessment

This pattern assumes **ACT-3** by default and **ACT-4** if you enable multi-agent roles or delegation.

- `CP.10` HEAR is required for production deployments at ACT-3 or ACT-4.
- `CP.9` is required when Codex is allowed to delegate or orchestrate sub-agents.
- `CP.8` gating is required if you combine broad tool access with regulated data or high-impact production workflows.

---

## Quick Navigation

| I am... | Start here |
|---|---|
| Individual developer hardening a workstation | [QUICKSTART.md](./QUICKSTART.md) |
| Security reviewer validating real enforcement | [EVALUATION.md](./EVALUATION.md) |
| Team lead standardizing Codex configs | [managed-settings](./managed-settings/) |
| Security engineer auditing developer setups | [scripts](./scripts/) + [monitoring](./monitoring/) |
| CI owner protecting non-interactive runs | [ci-cd](./ci-cd/) |
| MCP-heavy team | [integrations](./integrations/) |
| Reviewer looking for the rationale | [ARTICLE.md](./ARTICLE.md) |

---

## Residual Limitations

- Codex currently lacks native per-tool hook parity, so this package cannot block every individual tool action the way Claude hooks can.
- Notification logging is coarser than per-tool auditing.
- Desktop app launches are harder to mediate than wrapper-launched CLI sessions.

These are platform constraints, not design omissions. The mitigation is to tighten launch controls, minimize MCP scope, keep launch-time approval/sandbox flags explicit, and use CI for high-consequence actions.

---

## Core Governance Files

Inspired by the OpenClaw v2.0 approach, this package now includes a minimal Codex core-file standard:

- [IDENTITY.md](./IDENTITY.md): short identity anchor
- [SOUL.md](./SOUL.md): operating constitution
- [AGENTS.md](./AGENTS.md): primary operating manual
- [USER.md](./USER.md): data classification and trust handling
- [TOOLS.md](./TOOLS.md): environment and approved tool surface
- [SUBAGENT-POLICY.md](./SUBAGENT-POLICY.md): delegation rules for ACT-4 usage
- [EVALUATION.md](./EVALUATION.md): verification, drift checks, and known platform caveats

This is deliberately smaller than the OpenClaw 11-file standard because Codex does not expose the same runtime surfaces. The goal is not file count parity. The goal is a tighter governance surface with real operational effect.

---

*Cyber Strategy Institute -- AI SAFE2 Framework adaptation for Codex, v2*
