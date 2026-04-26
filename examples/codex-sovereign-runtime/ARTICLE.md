# Codex Sovereign Runtime: What Changes From The Claude Pattern

The Claude Code sovereign runtime example is built around hooks. That is the right answer for Claude because Claude exposes those events directly. Codex currently does not.

So the Codex implementation has to answer a narrower question:

> Where can we place controls that Codex cannot silently reason around, given today's runtime?

The answer is not "more prompt text." The answer is:

- launch-time enforcement
- managed configuration
- external notification sinks
- inventory and drift audits
- fail-closed CI

## 1. Launch-Time Enforcement

Codex exposes a dangerous startup mode:

- `--dangerously-bypass-approvals-and-sandbox`

That is the first place a sovereign runtime has to intervene. If you let users or injected shell aliases normalize that flag, every downstream control becomes advisory. The wrapper in this package blocks that flag before Codex starts.

## 2. Managed Configuration Is The Real Policy Plane

Codex's current durable control plane is `config.toml`.

That means a secure baseline has to govern:

- `approval_policy`
- `sandbox_mode`
- `web_search`
- profile definitions
- MCP server inventory
- notification commands

This is the Codex equivalent of hardened settings files in other agent harnesses.

## 3. `AGENTS.md` Is Necessary But Not Sufficient

`AGENTS.md` matters because it shapes the model's behavior around destructive operations, network use, prompt injection, and MCP scope. But it is not a sovereign boundary by itself.

AI SAFE2 requires external controls. For Codex today, `AGENTS.md` is one layer in a stack, not the stack.

## 4. Monitoring Is Coarser, So Audits Matter More

Without per-tool hooks, Codex runtime monitoring is not as granular as Claude's hook model. The compensating control is to:

- log session notifications externally
- record wrapper-launched sessions
- summarize sessions after completion
- audit configs and MCP definitions regularly

This is weaker than per-tool interception but still materially better than trusting the agent runtime alone.

## 5. CI Is Where You Must Be Strictest

CI runs are the easiest place to enforce:

- exact config files
- exact startup commands
- fixed sandbox and approval settings
- narrow tokens
- immutable logs

If you cannot fully govern desktop usage, govern CI first and treat workstation usage as semi-trusted development, not deployment authority.

## AI SAFE2 Assessment

- **ACT tier:** ACT-3 baseline, ACT-4 when multi-agent or delegation is enabled
- **CP.10 HEAR:** required for production deployments
- **CP.9:** required for multi-agent Codex usage
- **Evidence artifacts:** managed config files, wrapper logs, notification logs, session summaries, audit reports, CI workflow history

The key lesson is simple: the sovereign runtime concept survives the platform change, but the mechanism changes. Copying the Claude hooks blindly into Codex would look similar while failing operationally. This package avoids that mistake.
