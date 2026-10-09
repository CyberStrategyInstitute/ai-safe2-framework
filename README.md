[![AI SAFE2 Framework Visual Map](https://github.com/CyberStrategyInstitute/ai-safe2-framework/raw/main/assets/AI%20SAFE2%20Architecture.png)](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/assets/AI%20SAFE2%20Architecture.png)

<div align="center">

# AI SAFE² Framework v3.1

[Documentation map](docs/README.md) · [Developer Workflow](developer-workflow/README.md) · [CLI 1.0 workflow](safe2/docs/CLI-1.0-WORKFLOW.md) · [Security advisories](docs/advisories/README.md) · [Topic registry](repository-topics.manifest.json)

### The Universal GRC Standard for Agentic AI, Swarm Governance, and Runtime Enforcement

[![Version](https://img.shields.io/badge/version-3.1.0-orange.svg)](https://github.com/CyberStrategyInstitute/ai-safe2-framework/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/LICENSE)
[![Compliance](https://img.shields.io/badge/Mapped-32_Frameworks_%7C_ISO_42001_%7C_NIST_%7C_SOC2_%7C_EU_AI_Act-005696?style=flat-square&logo=auth0)](https://cyberstrategyinstitute.com/ai-safe2/)
[![Scope](https://img.shields.io/badge/Scope-161_Controls_%7C_Agentic_%7C_NHI_%7C_Swarm_%7C_CP.1--CP.10-red)](https://cyberstrategyinstitute.com/ai-safe2/)
[![MCP](https://img.shields.io/badge/MCP-2026--07--28-blue.svg)](00-cross-pillar/cp5_mcp_server_security.md)

**[Use the CLI](#use-ai-safe-with-an-agent)** · **[Why AI SAFE²](#what-ai-safe-is-for)** · **[Architecture](#the-core-architecture)** · **[MCP Security](#mcp-security-in-v31)** · **[Challenge Lab](#challenge-lab-falsification-before-claims)** · **[Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)**

</div>

---

## Use AI SAFE² with an agent

If your immediate goal is to inspect an agent project—not read the entire
framework—start with the [`safe2` CLI](safe2/README.md).

If your goal is to give a software team a repeatable, provider-neutral pull
request and release process, start with the
[AI SAFE² Developer Workflow](developer-workflow/README.md). The contract
preview supports teams using Claude and Codex together without replacing either
tool's configuration. It routes game and other software changes through
proportionate evidence requirements, attributes each reviewer or scanner, and
preserves the human merge and release decision.

Use it when you need to:

- inventory a machine or repository running one or several agent harnesses;
- assess a project without treating missing evidence as “safe”;
- screen a downloaded or newly created skill before activation;
- bind results to the model, harness, tools, memory, environment, and policy
  that were actually assessed;
- check an agent's completion claim against receipts and test evidence;
- turn AISM findings into a human-owned remediation decision; or
- create replayable Challenge Lab evidence.

### The shortest safe start

```bash
python -m pip install "ai-safe2[all]==1.0.1"
safe2 self-check --strict
mkdir review-project
cd review-project
safe2 init .
safe2 assess . --scan-content --inspect-config
```

The assessment writes canonical JSON for agents and a readable Decision Card
for people. It does not authorize a fix, deployment, exception, or compliance
claim.

### Prefer to delegate setup?

Give your agent the copyable instruction in
[Give this to your agent](safe2/README.md#give-this-to-your-agent). The same
provider-neutral workflow can be invoked from Codex, Claude Code, Hermes,
OpenClaw, Antigravity, MiroFish, TinyFish, bots, CI, or another harness that can
run a local command and preserve evidence files. That means the harness can use
the CLI; it does not imply that every named product has a native adapter.

| What you want | Start here |
|---|---|
| A reusable developer pull-request and release workflow | [Developer Workflow](developer-workflow/README.md) |
| A game repository using both Claude and Codex | [Game developer quickstart](developer-workflow/docs/GAME-DEVELOPER-QUICKSTART.md) |
| One bounded project assessment | [CLI outcome guide](safe2/README.md#start-with-the-outcome) |
| Multiple harnesses or environments | [Multi-harness discovery](safe2/README.md#multi-harness-environment-discovery) |
| A new skill checked before use | [Skill-screening demo](safe2/docs/SKILL-SCREENING-DEMO.md) |
| Human-readable facts, gaps, alternatives, and next actions | [CLI 1.0 operator workflow](safe2/docs/CLI-1.0-WORKFLOW.md) |
| Framework controls and governance model | Continue with the framework overview below |

## The 10-Second Version

AI SAFE² is an engineering and governance contract for agentic AI. It defines what must be governed, what must be enforced, and what evidence must exist when autonomous systems act.

The framework contains **161 controls**, organized across five operational pillars plus a Cross-Pillar Governance Layer. AI SAFE² v3.1 keeps the overall framework control total at 161 while materially updating the MCP security profile for the Model Context Protocol `2026-07-28` specification.

Version 3.1 also formalizes three enforcement planes:

| Plane | Traffic | Primary concern |
|---|---|---|
| **North-south** | Agent to model provider | Content, policy, consumption, and spend |
| **East-west** | Agent to agent | Identity, delegation, lineage, and authority |
| **Agent-to-tool** | Agent to MCP server or tool | Tool reachability, authorization, provenance, and returned-content trust |

**AI SAFE² specifies the required outcomes and evidence. NEXUS is Cyber Strategy Institute's first-party reference implementation for agent-to-agent and agent-to-tool enforcement. Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable AI SAFE² controls.**

---

<a id="what-ai-safe-is-for"></a>
## What AI SAFE² Is For

Production agents can drift without a code change. Retrieval changes, accumulated memory, delegated authority, tool calls, identity confusion, protocol behavior, or changes in external services can alter the effective operating environment while the source code remains unchanged.

AI SAFE² defines the operating envelope around those systems. It combines governance, identity, runtime enforcement, auditability, fail-safe behavior, adversarial testing, protocol security, and evidence requirements so an organization can reconstruct why an autonomous action was allowed, rejected, halted, or escalated.

### What both builders and governors get

- A single control vocabulary across agent runtime, identity, memory, tools, delegation, and evidence.
- Runtime enforcement patterns rather than policy-only guidance.
- Named fail-safe authority and kill-switch governance.
- Agent replication and non-human identity controls.
- Memory and RAG governance.
- MCP security controls for both provider and consumer risk.
- Mapping to 32 governance, security, privacy, and AI frameworks.
- Challenge Lab experiments designed to falsify framework claims rather than merely demonstrate the framework.

---

## What Changed in v3.1

AI SAFE² v3.1 is primarily a **protocol-governance and enforcement-plane release**.

### MCP `2026-07-28` realignment

The MCP core became substantially more stateless. AI SAFE² v3.1 therefore removes governance dependencies on protocol-owned session concepts and instead binds governance to framework-owned constructs such as:

- verified principal identity;
- capability grants;
- delegation chains;
- provenance baselines;
- explicit trust-establishment events;
- principal-scoped state handles;
- policy and authorization evidence.

The governing design rule is:

> A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.


### CP.5.MCP expands from 13 to 19 sub-controls

The six v3.1 additions are:

| Control | v3.1 focus |
|---|---|
| **MCP-14** | Extension capability negotiation |
| **MCP-15** | Header/body assertion integrity |
| **MCP-16** | State-handle binding and lifecycle |
| **MCP-17** | MRTR round-trip integrity and replay resistance |
| **MCP-18** | Catalog-cache integrity and provenance revalidation |
| **MCP-19** | Authorization-chain integrity, intended resource/audience validation, and SSRF boundaries |

The **overall AI SAFE² framework remains 161 controls**. MCP-14 through MCP-19 are profile-level sub-controls within CP.5, not six additional top-level framework controls.

### Compatibility

MCP `2025-11-25` remains a legacy compatibility binding for a twelve-month migration window. `Mcp-Session-Id`, when encountered in the legacy binding, is treated as a principal-scoped state handle rather than identity or the authorization boundary.

`server/discover` is optional under MCP `2026-07-28`; AI SAFE² does not require its presence for conformance.

---

## The Core Architecture

The framework is organized around **5 Operational Pillars** plus the **Cross-Pillar Governance Layer**, which was introduced in v3.0 and remains the governance operating system in v3.1.

| Pillar | Role | Focus |
|---|---|---|
| **P1** | The Shield | Input validation, injection defense, memory governance, no-code platform security |
| **P2** | The Ledger | Full visibility, semantic execution tracing, model provenance, RAG diff tracking |
| **P3** | The Brakes | Recursion limits, swarm abort, behavioral drift rollback, cascade containment |
| **P4** | The Control Room | Adversarial detection, tool-misuse monitoring, cloud AI telemetry, HITL |
| **P5** | The Feedback Loop | Continuous adversarial evaluation, capability emergence review, red-team repositories |
| **CP** | The Governance OS | ACT tiers, control planes, agent replication governance, HEAR doctrine, catastrophic-risk thresholds, protocol profiles |

### CP.5 in v3.1

CP.5 provides platform and protocol-specific security profiles without allowing the profiled protocol to define the governance boundary. The v3.1 MCP profile is the primary example of this principle.

See: [CP.5.MCP, MCP Server Security Profile](00-cross-pillar/cp5_mcp_server_security.md)

---

## Assess Organizations, Technologies, and Evidence Separately

**Documentation updated: 2026-10-02.** Start with the
[AISM assessment guide](AISM/ASSESSMENT-GUIDE.md) to use all three instruments
with the Technology Card and a worked example.

An organization earns an AISM maturity level. A technology contributes evidence
for specific controls within a defined boundary. A paper, benchmark, released
implementation, or vendor test cannot establish organizational maturity by itself.

AISM is the **AI Sovereign Maturity (AISM) Model**, which assesses the organization's
retained authority and governance capabilities across five pillars and six dimensions.

| Review instrument | Question | Starting point |
|---|---|---|
| AISM Sovereignty Score | How mature is the organization's governance across five pillars and six dimensions? | [Organizational methodology](AISM/AISM-Scoring-Matrix-Methodology.md) |
| AISM Technology Contribution Profile v1.0 | Which controls does this artifact address, implement, enforce, validate, evidence, or challenge? | [Profile and adoption rule](docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md), [Technology Card](docs/templates/TECHNOLOGY-CARD.md) |
| AI SAFE² Evidence Assurance v1.0 | What evidence supports each scoped claim? | [Assurance rubric and compatibility](docs/EVIDENCE-ASSURANCE.md) |

Select technologies by required-control fit, enforcement location, evidence,
failure behavior, retained authority, residual risk, and integration value.
Do not rank purchases by average pillar contribution or label a product
"AISM Level 4." A measured control contribution remains bounded by its tests.

The [nine-example review](research/technology-contribution-examples.md) frames
ContractWarden, DGF-Bench, ActionGuard, OpenShell/Sentry, policy learning, oversight,
and incident/accountability inputs as adoption candidates. Follow the
[validation guide](docs/TECHNOLOGY-VALIDATION.md) and
[incident evidence workflow](docs/INCIDENT-EVIDENCE.md) before promoting claims.

These additions are CSI v1.0 assessment methods for use and feedback. The CLI's current E0-E5
numeric grades, Challenge Lab C0-C5 scale, organizational scoring, 161 controls,
and generated profile data keep their existing meanings. No TCP command or
dashboard scoring integration is implemented by this update. See the
[repository coverage review](docs/TECHNOLOGY-PROFILE-REPO-REVIEW.md).

---

## Navigate the Framework

| Section | What You'll Find |
|---|---|
| [Pillar 1: Sanitize & Isolate](01-sanitize-isolate/) | Input defense, injection coverage, memory governance, no-code security |
| [Pillar 2: Audit & Inventory](02-audit-inventory/) | Tracing, logging, model lineage, RAG integrity |
| [Pillar 3: Fail-Safe & Recovery](03-fail-safe-recovery/) | Circuit breakers, recursion limits, rollback |
| [Pillar 4: Engage & Monitor](04-engage-monitor/) | Detection pipelines, HITL, platform monitoring |
| [Pillar 5: Evolve & Educate](05-evolve-educate/) | Adversarial evaluation and red-team artifacts |
| [Cross-Pillar Governance](00-cross-pillar/) | CP.1 through CP.10, ACT tiers, HEAR doctrine, replication governance, CP.5 profiles |
| [AI Sovereign Maturity (AISM) Model](AISM/) | Organizational maturity model and control mapping |
| [Technology Contribution Profile](docs/TECHNOLOGY-CONTRIBUTION-PROFILE.md) | Artifact review, evidence assurance, adoption rule, and reusable card |
| [AI SAFE² CLI](safe2/README.md) | Agent-facing scanning, evidence, AISM decisions, reports, and gates |
| [AI SAFE² Developer Workflow](developer-workflow/README.md) | Provider-neutral change routing, review evidence, game profile, and replayable human decision records |
| [AI SAFE² Development Method](docs/engineering/AI-SAFE2-DEVELOPMENT-METHOD.md) | Risk-adjusted planning, implementation evidence, reviews, and completion receipts |
| [NEXUS](NEXUS/) | CSI reference implementation for governed agent-to-agent and agent-to-tool interactions |
| [Research](research/) | Threat research and deep-dive control evidence |
| [Challenge Lab](challenges/) | Open falsification and replication experiments |
| [Interactive Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) | Search, filter, and explore AI SAFE² controls |

---

## MCP Security in v3.1

AI SAFE² v3.1 treats MCP as an **agent-to-tool security plane**, not merely a transport feature.

The profile covers:

- tool invocation authorization;
- returned-content sanitization;
- server and binary integrity;
- evidence and audit attribution;
- economic ceilings;
- delegation lineage;
- extension negotiation;
- header/body integrity;
- principal-scoped state handles;
- MRTR binding and replay resistance;
- catalog and schema provenance;
- OAuth/resource/audience authorization integrity.

### MCP Security Toolkit

The repository includes an agent-facing `safe2` governance CLI and retains the
three legacy MCP entry points during migration:

```bash
pip install -e ".[all]"
safe2 --help
```

| Tool | What it does |
|---|---|
| **`mcp-score`** | Remote black-box CP.5.MCP assessment |
| **`mcp-scan`** | Static analysis across MCP security patterns |
| **`mcp-safe-wrap`** | Consumer-side inspection, policy, and audit proxy |

All three ship in the `ai-safe2` package and run as `safe2 score mcp`, `safe2 scan mcp`,
`safe2 gate mcp` and `safe2 mcp wrap-stdio` / `wrap-proxy`. See the
[command map](safe2/README.md#command-map).

### Agent-facing governance and AISM decisions

The unified CLI makes repository evidence directly callable by agents while
preserving human decision authority:

```bash
safe2 init . --profile local
safe2 config show
safe2 assess . --scan-content --inspect-config
safe2 self-check --strict
safe2 acceptance run ./safe2-acceptance --strict
safe2 acceptance verify ./safe2-acceptance
safe2 scan project .
safe2 doctor . --format json --output environment-inventory.json
safe2 doctor . --assess --inspect-config --baseline trusted-inventory.json
safe2 doctor . --assess --card-format markdown --card-output environment-card.md
safe2 doctor . --assess --policy environment-policy.json --enforce-policy --output environment-decision.json
safe2 schema list
safe2 gate skill ./candidate-skill --strict
safe2 evidence nexus ./NEXUS --output nexus-evidence.json
safe2 evidence skillspector ./candidate-skill --output skillspector-evidence.json
safe2 evidence manifest environment-inventory.json nexus-evidence.json --subject-id governed-agent --output run-manifest.json --strict
safe2 evidence system safe2/data/system-identity-source-demo.json --output system-identity.json --strict
safe2 evidence diagnose safe2/data/failure-source-demo.json --system-identity system-identity.json --output failure-diagnosis.json --card failure-card.md --strict
safe2 evidence scope safe2/data/assessment-scope-source-demo.json --project-root . --system-identity system-identity.json --output assessment-scope.json
safe2 evidence truth operational-truth-policy.json harness-evidence.json task-receipt.json --output operational-truth.json --card operational-truth.md --strict
safe2 evidence changes . --baseline prior-agent-inputs.json --output current-agent-inputs.json --strict
safe2 evidence watch . --state .safe2/watch-state.json --evidence-dir .safe2/evidence/changes --continuous --max-runs 1
safe2 adapter codex-jsonl codex-trace.jsonl --codex-version VERSION --output codex-evidence.json
safe2 adapter otel-jsonl agent-traces.jsonl --otel-version VERSION --output otel-evidence.json
safe2 evidence claims claims.json task-receipt.json --output claim-audit.json --card claim-audit.md --strict
safe2 aism ingest nexus-evidence.json --subject-id nexus-local --subject-name "NEXUS Local" --output assessment.json
safe2 aism score assessment.json --format markdown --output decision-card.md
safe2 aism remediation-init assessment.json --system-identity system-identity.json --assessment-scope assessment-scope.json --decision-owner "Accountable system owner" --output remediation-source.json
safe2 aism plan remediation-source.json assessment.json --system-identity system-identity.json --assessment-scope assessment-scope.json --output remediation-plan.json --card remediation-card.md --strict
```

`safe2 init` creates a versioned secure-default project configuration without
overwriting an existing file. See the [CLI configuration contract](safe2/docs/CLI-CONFIGURATION.md).

`safe2 doctor` provides metadata-only discovery for multi-harness workstations,
including known Codex, Claude Code, Antigravity, Hermes, OpenClaw, and Grok
indicators, available shells, host details, CI markers, and WSL availability.
It does not read configuration contents or credential values and does not treat
inventory as proof of secure configuration. Named WSL distributions and
explicit SSH-accessible Linux hosts or cloud VMs can use the same fixed,
non-interactive metadata probe; the command never scans a network. Operational frustrations and false
completion claims can be captured locally with `safe2 feedback record` and
measured with `safe2 feedback summary`.

A reviewed `safe2 doctor` inventory can also serve as a trusted baseline.
Later runs report harness, asset, redacted configuration-hash, target-coverage,
and assessment-scope drift. Drift remains a review signal rather than proof of
authorization, compromise, control conformance, or organizational maturity.

The AISM Decision Card separates facts, assumptions, conflicts, unknowns,
alternatives, history, and recommendations. Machine-readable JSON remains the
canonical exchange format. An automated pass is not a claim of full framework
conformance or organizational maturity.

CLI 1.0 binds proposed remediation to the exact assessment, system identity,
and deployment scope. It validates control and AISM-cell traceability,
evidence, assumptions, owners, dependencies, alternatives, impacts, exit
criteria, completion evidence, residual risk, and status history. It never
executes or authorizes the proposed work and never increases the normative AISM
score merely because an action is marked complete.

See the [AISM implementation and remediation guide](safe2/docs/AISM-REMEDIATION.md).

See the executable [AISM Decision Card example](examples/aism-decision-card/).
See the executable [environment Decision Card workflow](examples/environment-decision-card/).
Evidence ingestion is conservative: collectors suggest candidate AISM cells but never invent maturity ratings. Evidence without verification provenance is labeled and capped until a human confirms the mapping.

See the complete [AI SAFE² CLI command and architecture guide](safe2/README.md).
See [what 1.0 includes and what should be built next](safe2/docs/CLI-POST-1.0-PRIORITIES.md).

The CLI includes [task receipts and usage evidence](safe2/docs/TASK-RECEIPTS.md) to
check artifact and test/tool claims, capture explicit local runs, recheck fresh
pytest evidence, authenticate report bytes, and correlate declared per-task
resource use. These checks do not establish task completion or verified billing.

The CLI includes a provider-neutral
[harness evidence intake](safe2/docs/TASK-RECEIPTS.md#provider-neutral-harness-evidence-intake)
that makes declared, observed, partial, and missing coverage visible before native
harness adapters are introduced.

The provider-neutral [adapter SDK](safe2/docs/ADAPTER-SDK.md), privacy-preserving
[Codex JSONL translator](safe2/docs/CODEX-JSONL-ADAPTER.md), and
[OpenTelemetry exchange](safe2/docs/OPENTELEMETRY-ADAPTER.md) let external harnesses
contribute attributed evidence without becoming AI SAFE² decision authorities.

The [continuous local evidence runner](safe2/docs/CONTINUOUS-EVIDENCE.md) preserves
repeated skill and harness-configuration change reports. The
[agent claim audit](safe2/docs/CLAIM-AUDIT.md) separates evidence-consistent,
contradicted, unverifiable, and explicitly limited outcomes without assigning a
speculative honesty score or inferring deception.

The [agent system identity manifest](safe2/docs/SYSTEM-IDENTITY.md) adds the next layer,
harness, tools, skills, memory, environment, policies, evaluator, authority and
relationships to one assessment subject without claiming the declared deployment
was independently verified.

[Failure localization](safe2/docs/FAILURE-LOCALIZATION.md) binds task observations and
competing failure candidates to that complete system identity. It ranks where to
investigate, exposes assumptions and contradictions, and recommends a repair
owner and next action without claiming a verified root cause or probability.

[Assessment scope](docs/ASSESSMENT-SCOPE.md) inventories which repository paths
are declared product, tests, adversarial fixtures, examples, research, generated
artifacts, dependencies, third-party content, configuration, documentation, or
unknown. It binds that declaration to system identity without reading file
contents or claiming the declared boundary was independently verified.

[Change attribution](docs/CHANGE-ATTRIBUTION.md) compares normalized findings
against an explicitly trusted baseline, binds both revisions to their assessment
scope artifacts, and separates inherited, introduced, changed, resolved, and
unknown states without claiming causation or conformance.

[Release readiness](safe2/docs/RELEASE-READINESS.md) combines identity, scope, change
attribution, required checks, risks, ownership, next actions, and rollback into
agent JSON plus a human card while preserving human release authority.

[Operational truth](safe2/docs/OPERATIONAL-TRUTH.md) correlates provider-attributed
harness evidence, task receipts, coverage, usage declarations, and completion
claims without promoting agreement into verified completion or billing. The
bounded one-shot change monitor supports local or CI use; the explicit polling
runner can preserve repeated reports until interrupted. Neither installs an OS
service, intercepts pasted context, sends telemetry, exports file content, or
turns detection into prevention.

For release boundaries, verified behavior, and external checks that still
require human or production execution, see the
[Stranger-Ready CLI Review](safe2/docs/STRANGER-READY-CLI-REVIEW.md),
[Security Policy](SECURITY.md), and [Support Policy](SUPPORT.md).

### MCP-19 and legacy bearer tokens

Opaque static bearer tokens do not contain an audience claim. A deployment using them must not claim MCP-19 audience-validation conformance unless equivalent intended-resource binding is independently established and evidenced.

The AI SAFE² MCP server therefore retains static-token handling as a compatibility mechanism, not as proof of MCP-19 conformance. JWT/OAuth deployments should validate the intended resource or audience before protected dispatch.

---

## NEXUS Reference Implementation

AI SAFE² and NEXUS intentionally serve different roles:

- **AI SAFE²** defines required governance outcomes, controls, evidence, and conformance criteria.
- **NEXUS** is CSI's first-party reference implementation for enforcing those requirements across agent-to-agent and agent-to-tool interactions.

A conformant implementation does not have to use NEXUS. It does have to satisfy the applicable control outcome and produce the required evidence.

The v3.1 NEXUS MCP adapter currently defines a fail-closed interface contract. Unimplemented enforcement methods raise rather than silently allowing traffic. It is not presented as production-ready until integrated and tested.

See [NEXUS/adapters/mcp/](NEXUS/adapters/mcp/).

---

## Examples: Sovereign Runtimes in the Wild

The `examples/` directory contains governed runtime patterns and integrations for common agent stacks, including Claude Code, Codex, AutoGen, CrewAI, LangChain, LangGraph, Make.com, xAI Grok, OpenClaw, MCP, and others.

Each implementation is intended to demonstrate how AI SAFE² controls can be enforced around an actual runtime rather than remaining policy-only statements.

See [examples/](examples/).

---

## Challenge Lab: Falsification Before Claims

The [AI SAFE² Challenge Lab](challenges/) converts public incidents, evaluation findings, and credible agentic threats into reproducible experiments.

**The framework is the subject of the test, not the source of its own proof.**

Challenge 001, the Anthropic Multi-Agent Turf War challenge, is designed to test whether externally enforced authority can stop destructive multi-agent conflict without blocking legitimate collaboration.

For v3.1, validation claims are scoped to the enforcement planes actually exercised by preregistered scenarios. Successful east-west agent governance does not automatically establish MCP/tool-plane or model-provider-plane validation.

Material normative framework, protocol-profile, implementation, policy, or grader changes after preregistration require a new preregistration version before confirmatory evidence is pooled.

See [Challenge 001](challenges/001-anthropic-multi-agent-turf-war/).

The [Challenge CLI workflow](safe2/docs/CHALLENGE-CLI.md) runs an offline fixture or an
explicitly authorized, bounded external evaluator, independently grades recorded
state, and translates third-party evidence through a versioned contract. Plans and
receipts bind the evaluator, requests, responses, optional system identity, source,
and normalized run. Bounded execution is not an OS sandbox, provider authentication,
or independent replication. The synthetic TENIR example remains illustrative only.

---

## 5-Layer Architectural Coverage

AI SAFE² v3.1 models the broader operational stack, from model infrastructure through agent identity and protocol-mediated tool use.

| Layer | Scope | Representative controls |
|---|---|---|
| **L1: Core Models** | LLMs and fine-tuned weights | Model lineage and provenance |
| **L2: Data Infrastructure** | Vector DBs, RAG, knowledge bases | Memory governance and corpus-diff tracking |
| **L3: System Patterns** | MCP, A2A, APIs, protocol meshes | CP.5 profiles, protocol security, vulnerability scanning |
| **L4: Agentic AI** | Swarms, orchestration, autonomous workflows | Fail-safe suite, agent replication governance |
| **L5: Non-Human Identities** | Agents, service identities, API principals | Agentic control plane, HEAR doctrine, delegation lineage |

---

## The v3.1 Coverage Matrix

| Risk Domain | Agentic Swarms | Non-Human Identity | Memory & RAG | Supply Chain | Replication | Universal GRC |
|---|---|---|---|---|---|---|
| **P1: Sanitize & Isolate** | Isolation | Secret hygiene | Memory governance | Model signing | Inherited | ISO A.8.4 |
| **P2: Audit & Inventory** | Traceability | Discovery | RAG diff | Provenance | Lineage | NIST MAP |
| **P3: Fail-Safe & Recovery** | Kill switch | Revocation | Rollback | Inherited | Cascade block | ISO A.17 |
| **P4: Engage & Monitor** | Adversarial monitoring | Behavior monitoring | Integrity monitoring | Inherited | Inherited | NIST MEASURE |
| **P5: Evolve & Educate** | Red teaming | Credential rotation | Model updates | Specification updates | Inherited | Continuous improvement |
| **Cross-Pillar** | Swarm governance | HEAR doctrine | Cognitive tags | Protocol and MCP security | Agent replication governance | CP.1 through CP.10 |

---

## Interactive Dashboard

Explore the AI SAFE² taxonomy and control mappings through the live dashboard:

[Launch the AI SAFE² Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

The dashboard provides control search, pillar filtering, risk-level views, executive summaries, and framework mappings. Generated dashboard data should remain synchronized with the canonical framework data during release updates.

---

## The Universal Rosetta Stone: 32 Frameworks

AI SAFE² maps its controls across 32 AI, cybersecurity, privacy, resilience, and enterprise governance frameworks so organizations can reuse evidence rather than run independent governance programs for every external standard.

Representative mappings include:

### AI and Agentic Frameworks

- NIST AI RMF
- ISO/IEC 42001
- OWASP AIVSS
- OWASP Top 10 for LLM Applications
- OWASP Agentic Top 10
- MITRE ATLAS
- MIT AI Risk Repository
- Google SAIF
- CSA agentic and zero-trust guidance
- EU AI Act

### Enterprise and Security Frameworks

- NIST CSF 2.0
- NIST SP 800-53 Rev. 5
- ISO/IEC 27001
- SOC 2
- PCI DSS
- HIPAA
- FedRAMP
- CMMC
- CIS Controls
- GDPR
- DORA
- Zero Trust architecture

The exact mapping remains control-specific. AI SAFE² alignment does not replace an organization's obligation to independently determine regulatory or certification applicability.

---

## Why AI SAFE² Is Different

| Capability | AI SAFE² v3.1 | Traditional GRC | AI point tools |
|---|---|---|---|
| **Unified mapping** | 32-framework crosswalk | Usually framework-specific | Usually limited |
| **Agentic awareness** | Native agents, swarms, loops, tools, delegation | Often software or human-process centric | Often model I/O centric |
| **Runtime enforcement** | Explicit control and evidence patterns | Often policy centric | Product dependent |
| **Agent replication governance** | CP.9 | Rarely explicit | Rarely explicit |
| **Named kill-switch authority** | CP.10 HEAR doctrine | Process dependent | Usually outside tool scope |
| **MCP agent-to-tool governance** | CP.5.MCP, MCP-1 through MCP-19 | Usually not protocol-specific | Product dependent |
| **Non-human identity** | First-class governance object | Often adapted from human IAM | Frequently secret-centric |
| **Memory and RAG governance** | Lifecycle and evidence controls | Limited | Often filtering only |
| **Reference implementation** | NEXUS plus runtime examples | Usually none | Vendor-specific implementation |

---

## Fast-Track Implementation

This repository provides the framework definitions and open implementation examples. Cyber Strategy Institute also maintains implementation tooling and services for organizations that want a faster path from framework adoption to operational enforcement.

Core open assets include:

- framework taxonomy and control definitions;
- AISM maturity model;
- NEXUS reference implementation;
- MCP security toolkit;
- gateway and sovereign runtime patterns;
- scanner and validation tooling;
- Challenge Lab experiments;
- framework mappings and research notes.

Commercial implementation resources are available through [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/).

---

## Framework Evolution

AI SAFE² is a living standard that adapts to changes in agent architectures, threat models, security research, and the protocols that connect autonomous systems.

| Version | Focus | Key additions | Framework controls |
|---|---|---|---|
| **v3.1** | Protocol governance and enforcement planes | MCP `2026-07-28` realignment, CP.5.MCP 13 to 19 profile controls, session-independent governance, agent-to-tool enforcement plane, NEXUS MCP reference contract | **161** |
| **v3.0** | Swarm governance and production evidence | 23 new pillar controls, CP.1 through CP.10, AIVSS integration, HEAR doctrine, agent replication governance | **161** |
| **v2.1** | Agentic and distributed systems | NHI governance, swarm controls, memory vaccine, OpenSSF OMS | **128** |
| **v2.0** | Enterprise operations | NIST and ISO mapping | **99** |
| **v1.0** | Foundational concepts | 10 core topics | **10** |

See [EVOLUTION.md](EVOLUTION.md) for the full history.

---

## Repository Structure

```text
/
├── .github/                   # CI/CD workflows and contribution automation
├── 00-cross-pillar/           # CP.1 through CP.10, including CP.5 profiles
├── 01-sanitize-isolate/       # Pillar 1
├── 02-audit-inventory/        # Pillar 2
├── 03-fail-safe-recovery/     # Pillar 3
├── 04-engage-monitor/         # Pillar 4
├── 05-evolve-educate/         # Pillar 5
├── AISM/                      # Normative AI Sovereign Maturity (AISM) Model
├── safe2/                     # Unified agent-facing Python CLI and AISM runtime
├── NEXUS/                     # CSI reference implementation
├── challenges/                # Falsification and replication experiments
├── examples/                  # Governed runtime and integration examples
├── gateway/                   # Runtime enforcement gateway
├── research/                  # Threat research and control evidence
├── scanner/                   # Static and framework assessment tooling
├── skills/                    # AI assistant and MCP integration assets
├── dashboard/                 # Interactive framework explorer
├── EVOLUTION.md               # Release and framework evolution history
├── SECURITY.md                # Supported versions and vulnerability reporting
├── SUPPORT.md                 # Support, compatibility, and maintenance policy
├── README.md                  # Current framework overview
└── skill.md                   # Framework context for AI assistants
```

---

## Companion Framework: Cognitive Sovereignty Framework

AI SAFE² secures and governs the AI system. The Cognitive Sovereignty Framework addresses the human operator's ability to remain capable of governing that system.

| | AI SAFE² | CSF |
|---|---|---|
| **Layer** | Machine and agent system | Human operator |
| **Defends** | AI operating environment | Human cognitive agency |
| **Governs** | Tool behavior and authority | Capacity to govern the tool |
| **Prevents** | Unsafe autonomy, injection, leakage, identity and protocol abuse | Cognitive offloading, attention capture, decision-automation capture |

The two frameworks are complementary rather than substitutes.

[CSF Learning Hub](https://cyberstrategyinstitute.github.io/cognitive-sovereignty/) · [Threat Explorer](https://cyberstrategyinstitute.github.io/cognitive-sovereignty/csf-explorer.html) · [CSF Repository](https://github.com/CyberStrategyInstitute/cognitive-sovereignty)

---

## Citation

```bibtex
@misc{aisafe2_framework,
  title = {AI SAFE² Framework v3.1: Agentic AI Governance and Runtime Enforcement},
  author = {Sullivan, Vincent and {Cyber Strategy Institute}},
  year = {2026},
  publisher = {Cyber Strategy Institute},
  url = {https://github.com/CyberStrategyInstitute/ai-safe2-framework},
  note = {Version 3.1. 161 framework controls, CP.5.MCP profile aligned to MCP 2026-07-28, and mappings across 32 frameworks.}
}
```

---

## Licensing and Usage Rights

**Code, MIT License:** Applies to code assets unless a subdirectory states a different license. NEXUS remains Apache 2.0 where explicitly designated.

**Framework and documentation, CC BY-SA 4.0:** Applies to AI SAFE² methodology text, pillar definitions, framework documentation, and derivative public documentation where designated.

See repository license files and subdirectory notices for authoritative terms.

Managed by [Cyber Strategy Institute](https://cyberstrategyinstitute.com).
Copyright © 2025-2026. All Rights Reserved.

</div>
