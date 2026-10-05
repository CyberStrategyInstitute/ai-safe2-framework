# AI SAFE² Repository UX Standard

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Standard](https://img.shields.io/badge/Docs-Repository_UX_Standard-820F1A?style=flat-square)](./REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## Assessment terminology and technology-review navigation

Use **AI Sovereign Maturity (AISM) Model** on first mention, then **AISM** or
**AISM Model**. AISM expands to AI Sovereign Maturity; Model follows the acronym.
The Sovereignty Score and Sovereignty Matrix retain their distinct names.
Preserve original terminology in historical records and asset filenames.

Keep organizational AISM maturity,
[technology contribution](./TECHNOLOGY-CONTRIBUTION-PROFILE.md),
[assurance v1.0](./EVIDENCE-ASSURANCE.md), Challenge Lab C0-C5, and native tool
scores visibly separate. Major review/implementation surfaces should link to
the method and [Technology Card](./templates/TECHNOLOGY-CARD.md) where relevant.
Do not present a candidate, design, or adoption backlog as a validated integration.
The [repository coverage review](./TECHNOLOGY-PROFILE-REPO-REVIEW.md) records affected
surfaces, unchanged contracts, and deferred runtime work.

## Purpose

Every user-facing README, guide, implementation page, research index, example landing page, and major module page should feel like part of one AI SAFE² repository rather than an unrelated collection of projects.

This standard defines the common visual and navigation grammar for AI SAFE² v3.1.

## Canonical topic homes

Repository information follows **one canonical topic home, many contextual
references**. When a dedicated directory exists, primary documentation,
implementation guidance, machine indexes, and topic-specific validation belong
inside that directory. Other surfaces link to the canonical source instead of
maintaining a second copy.

The machine-readable registry is
[`repository-topics.manifest.json`](../repository-topics.manifest.json).

| Topic | Canonical home | Primary entry point |
| --- | --- | --- |
| Framework and shared governance | repository root and `docs/` | `README.md`, `docs/README.md` |
| NEXUS | `NEXUS/` | `NEXUS/DOCUMENTATION.md` |
| SAFE2 CLI | `safe2/` | `safe2/README.md`, `safe2/docs/README.md` |
| Examples | `examples/` | `examples/README.md` |
| Research | `research/` | `research/README.md` |
| Challenge Lab | `challenges/` | `challenges/README.md` |
| AISM | `AISM/` | `AISM/README.md` |
| Scanner, gateway, dashboard, and skills | their named directories | the local `README.md` |
| Historical release records | `releases/` | `releases/README.md` |

A contextual page may remain beside the system that executes or evidences it—for
example, a challenge-local control record or an example README. It must link to
the canonical topic home and must not become a competing general-purpose guide.
Document kind resolves overlap: release records belong in `releases/`, examples
in `examples/`, research in `research/`, and product operating guidance in the
product directory.

## Human- and agent-ready content

Major topic entry points should provide, in this order where applicable:

1. a plain-language purpose and scope;
2. task- or audience-based navigation;
3. explicit text status and assurance boundaries;
4. a copyable quick start;
5. tables for repeated mappings, controls, compatibility, or comparisons;
6. lists for short actions and prerequisites;
7. limitations, evidence, and verification paths; and
8. machine-readable discovery through the repository manifest, a local
   manifest, `AGENTS.md`, or `llms.txt` when the topic is complex enough.

Color and icons are supplemental. A status, risk, decision, or instruction must
remain understandable in plain text, in a monochrome view, and to a parser.
Tables should not hide required steps in prose-only cells, and diagrams must
have an adjacent textual explanation.

## Brand and semantic colors

Use color to convey meaning consistently rather than decorating individual pages arbitrarily.

| Use | Color | Hex | Rule |
|---|---|---|---|
| Current release/version | Orange | `#F6921E` | Version and release badges only |
| Framework/governance/security identity | Maroon | `#820F1A` | Layer, module, governance, and security badges |
| Neutral/meta/documentation | Gray | `#808080` | Status, docs, compatibility, historical/meta context |
| Critical severity | Red | GitHub/Shields red | Security or governance severity only |
| High severity | Orange/amber | Standard severity orange | Risk severity only, not version identity |
| Medium severity | Yellow | Standard severity yellow | Risk severity only |
| Passing/verified | Green | Standard status green | Test/verification status only |

Do not introduce new badge colors for individual modules unless the color has a defined semantic meaning.

## Standard page header

Major pages should use this order:

1. H1 page/module title.
2. Short functional subtitle.
3. AI SAFE² current-version badge.
4. Layer/module badge.
5. Optional status/spec badge.
6. Repository navigation bar.
7. Previous/next navigation when the page belongs to an ordered sequence.
8. Horizontal rule.

Example:

```markdown
# Module Name
### Functional subtitle

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Layer](https://img.shields.io/badge/Layer-Module-820F1A?style=flat-square)](./README.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)
```

Relative paths must be adjusted for nesting depth.

## Standard repository destinations

GitHub release announcements should start from
[`RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md). Its structure prioritizes
the user outcome, a GitHub-safe before/after table, copyable quick start, evidence
boundaries, validation, invariants, and clearly separated roadmap items. Preview
the completed Markdown in GitHub before publishing and verify every link.

Release notes must also link directly to the relevant repository entry point,
changed guides/specifications, examples/templates, and validation evidence.
Keep these repository destinations separate from the note's section navigation.
Link material updates beside their descriptions, using concrete labels and
absolute GitHub URLs pinned to a verified release tag or merged commit. For a
documentation update, use a linked review workflow instead of installation
commands. Mark draft announcements and proposed methods explicitly.

Completed release announcements are prepared outside the repository for the
release owner to copy into GitHub. Do not commit announcement drafts unless
the owner explicitly requests a repository archive.

Major landing pages should make these destinations easy to reach:

- Framework Home
- Cross-Pillar Governance
- AISM
- NEXUS
- Dashboard

Context-specific pages should additionally link to their parent module and the most relevant adjacent implementation or specification.

## Ordered framework navigation

The canonical framework sequence is:

1. Framework Home
2. Pillar 1: Sanitize & Isolate
3. Pillar 2: Audit & Inventory
4. Pillar 3: Fail-Safe & Recovery
5. Pillar 4: Engage & Monitor
6. Pillar 5: Evolve & Educate
7. Cross-Pillar Governance
8. AISM
9. NEXUS / implementation surfaces

Pillar pages use explicit Previous and Next links.

## Version language

Distinguish **current version** from **historical introduction**.

Correct:

- `AI SAFE² v3.1` when describing the current framework.
- `Introduced in v3.0` when describing when CP.1-CP.10 or other controls entered the framework.
- `v3.0 core taxonomy` when a v3.1 component intentionally reuses an unchanged v3.0 data artifact.

Incorrect:

- blindly replacing every historical `v3.0` reference with `v3.1`;
- presenting v3.0 as current on a v3.1 landing page;
- implying profile sub-controls change the 161 core-control count.

## Control-count language

AI SAFE² v3.1 retains the **161-control core framework taxonomy**.

CP.5.MCP contains **19 profile controls, MCP-1 through MCP-19**. Those profile controls do not increase the core framework total to 180.

UAS is a 27-requirement regulatory profile extension composed from mapped controls across AI SAFE², NEXUS, and CSF. It does not create CP.11, and its requirements must not be added to the core framework total.

## Protocol and implementation language

AI SAFE² defines governance outcomes, controls, evidence, and conformance requirements.

NEXUS is Cyber Strategy Institute's first-party reference implementation for relevant east-west and agent-to-tool enforcement. NEXUS is not mandatory for AI SAFE² conformance when another implementation demonstrably satisfies the applicable controls and evidence requirements.

## Navigation integrity

Do not link to renamed or nonexistent paths. In particular:

- Cross-Pillar Governance is `00-cross-pillar/`, not `cross-pillar/`.
- The canonical MCP profile is `00-cross-pillar/cp5_mcp_server_security.md`.
- The machine-readable MCP profile is `skills/mcp/data/mcp-profile-v3.1.json`.

## Footer

Major landing pages should close with a compact navigation block and:

```markdown
*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
```

Nested implementation pages may identify their own component version when that component version differs from the framework version.

## Documentation review rule

When changing framework version, architecture, control count, terminology, a canonical path, or a protocol profile, review at minimum:

- root README;
- framework pillar READMEs;
- Cross-Pillar README;
- AISM README and matrices;
- NEXUS README and schemas;
- scanner README/rules;
- gateway README;
- skills and MCP README;
- examples index and affected example README;
- dashboard README/generated data;
- research index and affected research notes;
- Challenge Lab README/evidence/specification;
- release and evolution documents;
- contribution/PR templates.

A release is not documentation-complete merely because the canonical specification file changed.

---

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
