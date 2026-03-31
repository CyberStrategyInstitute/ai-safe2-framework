<div align="center">
<img src="/assets/AI-Source-Code-Leak-Guide.png" alt="How to Secure Against Claude Code Source Leak Risks" width="100%" />
</div>

# The Claude Code Source Leak: What It Means and How to Protect Yourself Right Now

**Published:** March 31, 2026
**Framework:** AI SAFE2 / AISM Level 4
**Author:** Cyber Strategy Institute

---

## What Happened

On March 31, 2026, security researcher Chaofan Shou confirmed that Anthropic's Claude Code CLI had its entire TypeScript source code exposed. A `.js.map` artifact was accidentally included in the npm package `@anthropic-ai/claude-code` version 2.1.88. Within hours, over 512,000 lines of proprietary TypeScript were publicly reconstructable and archived to multiple GitHub repositories.

This is not primarily an IP story. Media framing it that way is missing the point entirely.

This is a **Zero-Day Blueprint Event**. Adversaries now have the exact schematic of:

- Every permission gate in Claude Code
- The `--dangerously-skip-permissions` bypass internals (YOLO mode)
- JWT authentication logic
- WebSocket connection structures
- Multi-agent orchestration and subagent trust propagation
- Telemetry instrumentation flags (including the monitoring blind spots)
- The complete startup flow before trust confirmation -- the highest-value attack surface

What was NOT exposed: model weights, training data, user conversation history. The Claude model itself is unaffected. The CLI is a client-layer wrapper -- but it is that wrapper that governs what actions the model can take on your infrastructure.

---

## This Is the Second Time

This fact is missing from most coverage: **this is not the first occurrence.** According to reporting from Odaily, an early version of Claude Code was exposed through the identical mechanism -- npm source map artifacts -- in February 2025. Anthropic patched it then. The same build pipeline failure resurfaced 13 months later.

This matters architecturally. This is not a one-off human error. It is a systematic build pipeline control failure. The tool uses Bun as its bundler, which generates source maps by default. Neither the `.npmignore` configuration nor post-publish artifact verification caught the file either time.

If you were building your security architecture on the assumption that Claude Code's internal guardrails were opaque to adversaries, that assumption has been wrong for at least 13 months.

---

## The CVE Pedigree -- Why Readable Source Is Strategically Dangerous

The leak does not exist in isolation. Claude Code has a documented pattern of vulnerabilities precisely at the trust-boundary seams that the leaked source now makes transparent:

**CVE-2026-21852** -- Pre-trust API requests leaked Anthropic API keys via malicious repo settings (affects < 2.0.65). The startup flow before trust confirmation is the highest-value attack surface and the source of this CVE. That flow is now publicly readable.

**CVE-2025-64755** -- A `sed` parsing flaw bypassed read-only validation leading to arbitrary file write (affects < 2.0.31). "Read-only mode" is an enforcement boundary implemented in code. That code is now public.

**CVE-2025-58764** -- Command parsing flaws bypassed approval prompts from hostile context (affects < 1.0.105). "Approval" is a policy claim implemented by parsing code. Now readable.

**CVE-2025-59828** -- Yarn config and plugins executed before the user accepted the directory trust dialog (affects < 1.0.39). Pre-trust execution order is a historically fragile surface.

**CVE-2025-52882** -- The IDE WebSocket accepted connections from arbitrary origins enabling unauthorized file access and code execution in Jupyter notebooks (affects >= 0.2.116 and < 1.0.24).

Every one of these CVEs exploits the seams between user intent, prompt context, repository trust, execution approval, and startup behavior. Readable implementation code sharply reduces the cost of finding new variants in those same seams. Adversaries no longer need to probe from the outside.

---

## The Eight Things Most Analysis Is Missing

### 1. The Silent Override Bug

When `--dangerously-skip-permissions` is combined with `--permission-mode plan`, the bypass silently wins. The developer believes they are in the safe read-only planning mode. They are not. There is no user-visible signal.

An attacker who can influence how Claude Code is launched -- through a poisoned `CLAUDE.md` file, a compromised MCP server, or a malicious repository setting -- can silently escalate from planning mode to full bypass. This is documented in the codebase, which is now public.

### 2. The Subagent Inheritance Problem

When bypass mode is active, all subagents spawned during the session inherit full autonomous access. This cannot be overridden at the subagent level. Your agents-calling-agents architecture just became a full lateral escalation surface. The leaked orchestration code shows exactly how this inheritance works.

### 3. The Telemetry Dead-Zone Map

The exposed telemetry instrumentation flags do not just reveal how the system works. They reveal where the monitoring is and where it is not. This is the equivalent of a burglar receiving the floor plan of the security camera coverage alongside the building schematic.

### 4. The Supply Chain Worm Vector

Research from UpGuard analyzing 18,470 `.claude/settings.local.json` files found that developers routinely grant Claude Code permission to download content from the web, execute code, and push to GitHub without requiring per-action approval. When chained -- download from untrusted source, execute locally, push to GitHub -- this creates conditions for autonomous self-propagating supply chain worms that weaponize existing developer permissions.

### 5. The Enterprise Egress Blindspot

The Anthropic API domain is allowlisted in most enterprise network egress controls because Claude Code requires it to function. A hijacked Claude Code session can package and exfiltrate data via API calls to that allowlisted endpoint. Standard egress controls will not flag it.

### 6. The Secret Leakage Baseline Has Already Shifted

Before this leak, GitGuardian research found that commits assisted by Claude Code already leaked secrets at a rate of 3.2% -- approximately double the GitHub baseline. Two CVEs specifically addressing API key exfiltration were disclosed concurrently with that research. The leak does not create this problem. It removes the reverse-engineering barrier that was the only thing slowing adversaries down.

### 7. Legal Liability Has Changed

California AB 316, effective January 1, 2026, explicitly precludes organizations from using an AI system's autonomous operation as a defense to liability claims. If a hijacked Claude Code instance causes damage to your infrastructure or a third party, you cannot argue that "the AI did it." The deployer is liable. This changes the board-level calculus on agentic AI governance.

### 8. The Undercover Mode Irony

Claude Code contains an internal system called Undercover Mode, specifically engineered to prevent internal codenames from appearing in git commits. The entire source codebase was then shipped in a `.map` file -- reportedly generated by Claude itself. The containment mechanism was bypassed by the system it was built to protect. This is not merely ironic. It is a proof case for the core architectural thesis: the agent cannot be its own security control.

---

## The Architectural Diagnosis

The foundational problem is structural. Claude Code's permission enforcement logic is implemented in TypeScript, ships via npm, and is now in the public domain. Waiting for Anthropic to patch and restore the opacity of these mechanisms is a failed model. The next version will be reverse-engineered from its artifacts within hours of release.

Here is what the trust boundary looks like without external controls:

```
User Intent --> Claude Code (vendor TypeScript guardrails) --> Your Infrastructure
                              ^
                              |  Guardrails now publicly readable
                              |  Adversary has the exact bypass code
```

Here is what it needs to look like:

```
User Intent --> [External Pre-Hook: YOUR CONTROLS] --> Claude Code --> [External Post-Hook] --> Your Infrastructure
                      ^                                                       ^
                      |  Enforced at OS/network layer                         |  Monitored externally
                      |  Agent code cannot see or influence                   |  Agent cannot suppress logs
```

The Sovereign Runtime Governor does not ask Claude to reconsider. It enforces the boundary at the OS or network layer. An adversary who perfectly bypasses Claude Code's internal guardrails using the leaked source still hits your wall -- because your wall is not in Claude Code's code.

---

## The AI SAFE2 Response -- Five Pillars Applied

**Pillar 1: Sanitize and Isolate.** Deploy input and output filtering at every agent boundary before prompts enter Claude Code and before outputs leave. Implement JSON schema enforcement on all incoming webhooks and project configuration files. For any Claude Code session processing untrusted content -- cloned repositories, web-fetched pages, MCP server outputs -- treat all content as adversarial regardless of apparent source.

**Pillar 2: Audit and Inventory.** You cannot defend an attack surface you have not mapped. The adversary now has your complete map. Build yours. Inventory every Claude Code installation: developer workstations, CI/CD runners, GitHub Actions images, devcontainers, shared jump hosts, golden images, and cloud workstations. Scan `.claude/settings.local.json` files across your developer ecosystem for overly broad permission grants.

**Pillar 3: Fail-Safe and Recovery.** This is the AISM Level 4 Sovereign Runtime Governor. Implement an external circuit breaker: an independent process monitors agent state transitions. When a hijacked agent attempts a prohibited state transition, the circuit breaker mathematically rejects the action before OS execution -- not by asking Claude to reconsider. Implement just-in-time credential issuance. Replace long-lived API keys with scoped, short-lived tokens issued at session initialization.

**Pillar 4: Engage and Monitor.** Stand up behavioral analytics external to the Claude Code process. API call volumes, destinations, rates per agent, filesystem write patterns, and subprocess spawn chains. Set anomaly thresholds against known-good baseline behavior. The leaked telemetry flags give you the exact internal metrics the agent uses -- build external equivalents the agent cannot influence.

**Pillar 5: Evolve and Educate.** Developers are the primary attack surface. The 3.2% secret leakage rate exists because developers normalize Claude Code as a trusted extension of their own hands rather than a semi-autonomous entity. Train on the silent override bug. Establish a "never trust AI to check its own homework" policy. Red team agent-to-agent impersonation using the leaked orchestration logic.

---

## Immediate Actions -- The 72-Hour Window

**Hours 0 to 4:**
- Check your Claude Code version. If below 2.0.65, rotate your Anthropic API key immediately.
- Ban `--dangerously-skip-permissions` via enterprise managed settings.
- Audit `.claude/settings.local.json` files for `bypassPermissions: true`.

**Hours 4 to 24:**
- Set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` across all deployments.
- Deploy the pre-tool-use hook from this repository.
- Move all sessions processing untrusted repositories to plan mode or sandboxed mode.
- Block outbound connections from Claude Code to non-allowlisted domains at the network layer.

**Hours 24 to 72:**
- Complete inventory of all Claude Code install paths including CI/CD, devcontainers, and golden images.
- Implement external behavioral monitoring.
- Establish JIT credential issuance -- eliminate long-lived credential access.
- Begin AISM Level 3 to 4 maturity gap assessment.
- Engage legal on AB 316 exposure.

---

## What to Watch in the Next 30 Days

From the adversary community: The leaked orchestration architecture enables construction of adversarial MCP servers that exploit the now-public subagent trust model. Expect published proof-of-concept tools within weeks. The leaked bypass logic enables prompt templates targeting the exact decision boundaries in permission enforcement. The supply chain worm vector is substantially cheaper to operationalize.

From Anthropic: Watch npm package distribution changes. The docs already list npm installation as deprecated. Watch for build pipeline controls in subsequent releases. The absence of an immediate public statement on the second occurrence of the same class of failure is worth noting.

From the regulatory environment: California AB 316 creates immediate civil liability exposure for organizations that cannot demonstrate governance over their agentic AI deployments. This incident is precisely the kind of catalyst that converts regulatory exposure into litigation.

---

## The Core Principle

Policy is intent. Engineering is reality.

The Claude Code source leak is the clearest empirical proof yet that vendor-managed safety mechanisms are not a security architecture -- they are a convenience layer. For at least 13 months, Anthropic's internal guardrails for autonomous code execution have been in or near the public domain.

The Sovereign Runtime Governor at AISM Level 4 governs agent behavior through external enforcement the agent's code cannot observe or influence. The leaked source gives adversaries a better map of what they are trying to bypass. Your external circuit breaker does not care about their map.

The question for your team is not whether Anthropic made a mistake. They did, twice. The question is: when your autonomous agent is operating with your developer's credentials on your codebase, who controls the execution boundary -- the vendor's TypeScript code, or your engineering?

---

## Implementation

The complete implementation of the controls described in this article is available at:

[AI SAFE2 Framework -- Claude Code Sovereign Runtime Example](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/claude-code-sovereign-runtime)

Start with [QUICKSTART.md](./QUICKSTART.md) for 15-minute protection, or [README.md](./README.md) for the full picture.

---

*Cyber Strategy Institute -- AI SAFE2 Framework*
*Classification: Public Technical Guidance*
*March 31, 2026*
