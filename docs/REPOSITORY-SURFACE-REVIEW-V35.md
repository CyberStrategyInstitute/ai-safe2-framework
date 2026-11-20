# Repository surface review for v3.5

[Framework home](../README.md) | [Full disposition CSV](data/repository-surface-review-v35.csv) | [Adoption guide](V35-ECOSYSTEM-ADOPTION.md) | [Page map](../PAGE_MAP.md)

## Scope and interpretation

Inventory: **86 README files, 13 HTML files and 35 other root files**. README/HTML counts are distinct categories; a root README is counted as a README. This is structural/documentation review, not runtime conformance or independent incident verification.

Every surfaced path has a disposition. Current topic READMEs share a navigation rail; module-specific headings, quickstarts and evidence boundaries remain local. Frozen challenges, dated assessments, release records, adversarial fixtures and separate policy material retain their meanings. Uniform navigation does not require identical bodies or images on fixtures.

| Disposition | Paths |
| --- | --- |
| current-entrypoint | 5 |
| current-topic-surface | 65 |
| generator-template | 1 |
| historical-or-frozen | 21 |
| root-owning-source | 31 |
| separate-policy-material | 9 |
| test-fixture | 2 |

## Root files

Root licenses, schemas, build configuration, lock files and component contracts are retained when their owning semantics are unchanged. A framework update does not justify rewriting every root file. The CSV enumerates each root path rather than calling untouched contracts updated.

## HTML and guide decisions

The control dashboard and generated Rosetta explorer are current source projections. The Claude Code HTML guide retains version-specific feature/incident context with an explicit revalidation notice. FORGE policy pages receive shared navigation without changing political content. The Gateway v3.0 release HTML remains historical. The Rosetta template is an internal generator input.

Added guides: [v3.5 adoption and validation](../guides/V35-ADOPTION-AND-VALIDATION.md), [mapping validation](ROSETTA-STONE-V35.md), [source-family index](ROSETTA-SOURCE-INDEX.md), and [ecosystem adoption](V35-ECOSYSTEM-ADOPTION.md). Existing stack hardening/troubleshooting guides remain discoverable. No historical guide is deleted to obtain version uniformity.

## Review passes and path checks

1. Inventory all tracked/current README, HTML and root surfaces; classify historical, fixture, policy, generator and owning-source exceptions.
2. Inspect current framework counts, catalog selection, guide/index routes, component boundaries and visual entry points.
3. Validate local Markdown files, primary anchors, HTML file/anchor links, source/control/child-clause projections and generated freshness.
4. Exercise human and agent journeys through source mapping, current control requirements, research, implementation acceptance and version boundaries. Browser observations and executed test results are recorded in the PR description for the reviewed head.

Passing route checks establish structural navigation. They do not verify external URLs, the substantive truth of mapping claims, deployment conformance, or every interaction on every historic page.
