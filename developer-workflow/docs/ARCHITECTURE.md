# Architecture

## Architectural decision

AI SAFE2 Core is the policy, evidence, provenance, and decision engine. The CLI
is one interface to that core. NEXUS, Skills, MCP, SDKs, and product workflows
are other interfaces or deployment surfaces.

```mermaid
flowchart TB
    O[Outcome requested] --> C[AI SAFE2 Core]
    C --> P[Policy and change classification]
    C --> E[Evidence validation and provenance]
    C --> D[Decision state and replay record]

    CLI[CLI] --> C
    NX[NEXUS] --> C
    SK[Skills] --> C
    MCP[MCP surfaces] --> C
    API[SDK and API] --> C

    DEV[Developer Workflow] --> CLI
    PRO[MCP Pro] --> MCP
    AC[Agency Check] --> API

    AD[Replaceable adapters] --> E
    AD --> CX[Codex]
    AD --> CL[Claude]
    AD --> SR[Sovereign Runtime]
    AD --> DL[Drift and Love Equation]
    AD --> DT[Deterministic tools]

    D --> H[Named human decision]
```

## Stable core contracts

The first release stabilizes four contracts:

1. **Subject:** repository, revision, scope, and change class.
2. **Evidence:** producer, execution state, observations, findings,
   limitations, provenance, and artifacts.
3. **Adapter:** capability, data boundary, permissions, output schema, and
   upgrade policy.
4. **Decision record:** required evidence, observed evidence, unresolved risk,
   human authority, and replay inputs.

Providers may change without changing these contracts. Additive schema fields
are permitted within v1. Removing or changing the meaning of a required field
requires a new major schema version.

## Modular developer stack

The Developer Workflow is assembled around capabilities, not brands. A team
can replace a provider without rewriting its decision contract.

```mermaid
flowchart LR
    GOAL[Repository goal and risk profile] --> ROUTE[Change route]
    ROUTE --> METHOD[Development method]
    ROUTE --> CHECKS[Deterministic checks]
    ROUTE --> REVIEW[Semantic and security review]
    ROUTE --> RUNTIME[Runtime or deployment evidence]

    METHOD --> M1[Superpowers or team method]
    CHECKS --> M2[Tests, build, lint, CodeQL, Semgrep, Gitleaks]
    REVIEW --> M3[Codex, Claude, Greptile, human specialist]
    RUNTIME --> M4[NEXUS, Sovereign Runtime, MCP or service receipts]

    M1 --> E[Normalized evidence]
    M2 --> E
    M3 --> E
    M4 --> E
    E --> STATE[Hold or ready for human decision]
    STATE --> HUMAN[Named human decision]
```

| Module | Question it answers | Default posture |
|---|---|---|
| Product profile | What does this kind of repository need reviewed? | Required and repository-specific |
| CLI decision routing | Which review plan follows from deterministic state and policy? | Required, pinned core capability |
| Human decision record | What evidence, gaps, risks, and owner decision apply to this revision? | Required; starts at `hold` |
| Development method | How should the work be planned, tested, debugged, and verified? | Optional; Superpowers is one supported method |
| Deterministic checks | Did repeatable tests and scanners pass on this revision? | First evidence to integrate |
| Semantic code review | What correctness, design, and maintainability risks remain? | Proportionate to route |
| Security review | Can the change violate a trust boundary or security property? | Required only when policy says so |
| Runtime adapter | What happened when an agent or production system acted? | Add when runtime actions are in scope |
| Strategic reviewer | Would a second opinion materially improve a major integration or release decision? | Selective, not an every-change default |

The repository template ships a game profile. Optional adapter manifests live
in the full package at `developer-workflow/adapters/manifests.json`; copy the
selected declarations separately when adding an integration. A manifest is a
declared integration boundary, not proof that the provider is connected or
operational.

## Product surfaces

### Developer Workflow

For software teams. It classifies changes, invokes proportionate engineering
and security controls, and prepares evidence for merge or release decisions.

### MCP Pro

For builders and security teams operating inside Claude Code, Cursor, Codex,
and other MCP-capable tools. It exposes governance and implementation-review
capabilities at the execution boundary. The public product page describes free
and paid capabilities; this repository does not duplicate entitlement logic.

### Agency Check

For people making everyday decisions with an agent. It translates the same
evidence discipline into one Decision Card with `ready_to_review`,
`clarify_one_thing`, or `pause_and_verify`. It is advisory and never labels an
action safe or authorizes the action.

Agency Check is planned to live at `agency-check.app`. The domain is a
deployment endpoint, not a dependency of AI SAFE2 Core.

## Adapter boundary

Adapters observe or translate. They do not inherit authority from the core.
Every adapter declares:

- capabilities and supported subject types;
- whether source or evidence leaves the local boundary;
- permissions and secrets required;
- normalized output contract;
- version pin and upgrade policy;
- failure behavior;
- whether it observes, recommends, enforces existing policy, or authorizes.

Version 0.1 permits `observe` and `recommend`. No bundled adapter may
`authorize` merge, release, deployment, purchase, message, booking, or risk
acceptance.

## Superpowers boundary

Superpowers is an optional development-method module. It improves how an agent
brainstorms, plans, isolates work, tests, debugs, requests review, and verifies
completion. AI SAFE2 determines which evidence is required and whether the
result supports a human decision. The project links to Superpowers rather than
copying its skill text.

## Compatibility rule

Claude and Codex instructions remain separate, thin entry points over the same
repository policy:

- `AGENTS.md` supplies provider-neutral and Codex-compatible instructions.
- `CLAUDE.md` points Claude to the same policy and evidence contracts.
- neither file changes the developer's model, login, hooks, MCP configuration,
  or provider secrets;
- provider adapters can be enabled, disabled, or upgraded independently.

