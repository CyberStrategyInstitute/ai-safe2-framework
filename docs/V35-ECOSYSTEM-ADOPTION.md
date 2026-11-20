# v3.5 ecosystem adoption

[Framework Home](../README.md) | [Controls](CONTROLS-V3.5.md) | [Research](../research/README.md) | [Machine adoption register](data/v35-ecosystem-adoption.json)

## What changes for existing users

The framework now asks implementations to establish authority and current conditions at the moment an effect commits, account for delegated consumption, and verify outcomes independently. Existing components retain their own versions and evidence. A new framework label does not qualify an older runtime.

This register separates source behavior, guidance, scaffolding and prospective studies. It is an implementation work register, not a conformance certificate.

## Choose the right boundary

| Surface | Source status | What works or exists | Required next work |
| --- | --- | --- | --- |
| [Core Gateway](../gateway/README.md) | compatible-reference | Provider proxy; existing v3.0 component evidence remains scoped to its observed boundary. | Bind the final provider request to current principal, task, policy and environment; reserve aggregate consumption atomically; verify bypass and outage behavior. |
| [NEXUS](../NEXUS/README.md) | partial-reference | SDK authority, evidence, memory and payment building blocks retain their own qualification boundaries. | Qualify subtree stop, delegated identity, current attestation, shared budgets and independent effect evidence across hosts before a v3.5 production claim. |
| [NEXUS MCP adapter](../NEXUS/adapters/mcp/README.md) | scaffolding | Interface methods fail closed until implemented; this adapter is not a deployable security control. | Implement and qualify the twelve MCP child requirements, including pre-trust initialization, current audience/resource binding, authority attenuation, state provenance and final-effect verification. |
| [SAFE2 CLI](../safe2/README.md) | implemented-bounded | Source CLI exposes current catalogs, exact lookup, mapping audit and declared-evidence readiness checks. | Integrating deployments must authenticate observers, decide applicability and attach independent boundary evidence. Preserve existing score semantics. |
| [Developer Workflow](../developer-workflow/README.md) | contract-preview | Change routing and evidence receipts retain human merge/release decisions; v3.5 adoption guidance is explicit. | Bind consequential plans to exact revision, target, delegated scope, success criteria and rollback. A plan or review cannot authorize a runtime effect. |
| [Skills and provider guidance](../skills/README.md) | guidance | Current source guidance must load v3.5 clauses, cite exact IDs and preserve unverified evidence states. | Reinstall or refresh copied skill packages. Run skill trust checks and evaluate tool-call behavior; reading guidance does not enforce the runtime boundary. |
| [MCP knowledge server](../skills/mcp/README.md) | implemented-bounded | Serves 173 core controls and the 19-control MCP profile with twelve child requirements from packaged source data. | Keep knowledge lookup separate from execution authorization. Qualify authentication, audience/resource binding and tool actuation in the deployment; refresh cached/copy-installed data. |
| [Sovereign runtime examples](../examples/README.md) | mixed-reference | The v3.5 authority example demonstrates synthetic local transactions. Existing runtime examples retain individual limits. | For each runtime, test exact action binding, direct-path bypass, stale state, child budgets, stop propagation, duplicate effects and independent outcomes before extending claims. |
| [Scanner and MCP toolkit](../scanner/README.md) | implemented-bounded | The current catalog is available; static detection coverage remains the implemented rule set. | Map each rule to its actual clause and test. Report unassessed runtime requirements instead of treating absent static findings as a v3.5 pass. |
| [AISM and UAS](../AISM/README.md) | implemented-bounded | AISM v1 arithmetic is retained; scoped readiness and UAS v2 acceptance interpretation remain separate. | Reassess v2 human/fairness evidence in context. Validate real intervention capability and applicability; declare unknowns and preserve owner authorization. |
| [Challenge Lab](../challenges/README.md) | prospective | Challenge 002 is prospective; Challenge 001 retains its frozen baseline and evidence identity. | Freeze the complete design before confirmatory runs, then report safety, utility, opportunity counts and unknown outcomes separately. Independent L2 execution is pending. |
| [Dashboard](../dashboard/README.md) | implemented-bounded | The branch dashboard projects 173 controls and canonical requirements; deployed Pages may reflect another revision. | Check the deployed revision before presenting a live dashboard as v3.5. Mapping labels and maturity views must retain their evidence limits. |

## Adoption order

1. Establish the complete system identity, owner, task, target environment and success criteria. Resolve applicable control IDs and profiles before declaring coverage.
2. Put current-condition authorization at each real side-effect boundary. Inventory direct APIs, tool subprocesses, browser actions and alternate paths that bypass the gateway.
3. Bind delegated identity, current grants, aggregate budget reservation and revocation to the same authority tree. Refuse ambiguous or stale state.
4. Bind retries to a side-effect ledger and verify the resulting state independently. Preserve committed, uncommitted, partial and unknown effects.
5. Connect receipts, monitoring, human intervention and recovery without allowing an evidence plane to grant authority.
6. Run negative cases and legitimate work under the same declared scope. Report safety, utility and unknown outcomes separately.
7. Update deployment-specific claims only after the relevant evidence passes. Preserve version, owner, dependencies, residual risk and rollback.

This is dependency order, not a time-based rollout. Production changes require the owner's normal deployment and risk decisions.

## Acceptance by mechanism

| Mechanism | Challenge case | Evidence needed |
| --- | --- | --- |
| Trust lifecycle / S1.8, CP.11 | A server or skill executes before trust, or changes after approval | Initialization trace, pinned provenance, revalidation and blocked unauthorized execution |
| Final effect / CP.12, F3.7 | Valid approval reaches another target or conditions change before commit | Exact action/target/revision binding and observed protected-state result |
| Aggregate authority / F3.6 | Concurrent children each fit a local limit but exceed the root budget | Atomic reservation, contention results, spent-state accounting and outage behavior |
| Delegation and stop / CP.11-CP.12 | Parent authority is revoked while a child continues | Authority lineage, propagation delay, observed effect boundary and residual effects |
| Outcome and retries / A2.7-A2.9 | A retry duplicates a payment, or a tool claims success without changing state | Idempotency ledger, independent state check, uncertain-state handling and recovery |
| Evidence independence / CP.13 | An agent forges its receipt or persuades its monitor | Independent collector boundary, tamper tests, custody and contradiction handling |
| Coordination / CP.15 | Composed permitted actions achieve a prohibited root effect | Root-task policy, role graph, handoff and termination evidence |
| Declared success / E5.5 | A grader changes the definition after seeing results | Versioned criteria, frozen protocol, legitimate-work outcomes and unknowns |

## Human and machine evidence

Use shared evidence identifiers to connect the machine boundary to Cognitive Sovereignty Framework observations. Preserve four separate questions: did the operator understand the scope, was reliance justified, could they intervene, and did they retain capability? Pair those with actual authority, action, stop and outcome records.

[UAS v2](../00-cross-pillar/unbiased-ai/STANDARD-V2.md), [CP.10](../00-cross-pillar/README.md), and [AISM readiness](../AISM/DEPLOYMENT-READINESS-V35.md) own their respective requirements. A reciprocal CSF link is a route to evidence, not equivalence or a psychological score.

## Source and verification routes

| Surface | Owning source | Verification route | Version boundary |
| --- | --- | --- | --- |
| Core Gateway | [gateway/main.py](../gateway/main.py) | [gateway/test_gateway.py](../gateway/test_gateway.py) | gateway v3.0 |
| NEXUS | [NEXUS/sdk/python/nexus_sdk/guardian.py](../NEXUS/sdk/python/nexus_sdk/guardian.py) | [NEXUS/sdk/python/tests](../NEXUS/sdk/python/tests) | NEXUS 0.6.0 source version |
| NEXUS MCP adapter | [NEXUS/adapters/mcp/adapter.py](../NEXUS/adapters/mcp/adapter.py) | [NEXUS/sdk/python/tests](../NEXUS/sdk/python/tests) | NEXUS 0.6.0 source version |
| SAFE2 CLI | [safe2/framework.py](../safe2/framework.py) | [tests/test_framework_v35.py](../tests/test_framework_v35.py) | CLI 1.1.0 source |
| Developer Workflow | [developer-workflow/docs/ARCHITECTURE.md](../developer-workflow/docs/ARCHITECTURE.md) | [developer-workflow/tests](../developer-workflow/tests) | Developer Workflow 0.1.0 preview |
| Skills and provider guidance | [skills/ai-safe2-secure-build-copilot/SKILL.md](../skills/ai-safe2-secure-build-copilot/SKILL.md) | [scripts/validate_skill_card.py](../scripts/validate_skill_card.py) | Skill package version is separate from framework version |
| MCP knowledge server | [skills/mcp/src/mcp_server/controls_db.py](../skills/mcp/src/mcp_server/controls_db.py) | [skills/mcp/tests](../skills/mcp/tests) | MCP server 3.1.0 source; framework 3.5 candidate |
| Sovereign runtime examples | [examples/v35-authority/demo.py](../examples/v35-authority/demo.py) | [tests/test_framework_v35.py](../tests/test_framework_v35.py) | Example-specific; no blanket certification |
| Scanner and MCP toolkit | [scanner/scanner.py](../scanner/scanner.py) | [scanner/tests](../scanner/tests) | Scanner package/component version remains separate |
| AISM and UAS | [safe2/data/deployment-readiness-v1.schema.json](../safe2/data/deployment-readiness-v1.schema.json) | [tests/test_aism.py](../tests/test_aism.py) | AISM v1; UAS v2 candidate |
| Challenge Lab | [challenges/002-v35-commit-boundary/preregistration.json](../challenges/002-v35-commit-boundary/preregistration.json) | [tests/test_framework_v35.py](../tests/test_framework_v35.py) | Study/protocol versions are independent |
| Dashboard | [dashboard/public/data/controls.json](../dashboard/public/data/controls.json) | [scripts/check_v35_contracts.py](../scripts/check_v35_contracts.py) | Branch candidate; deployment not implied |

## What this update does and leaves open

This PR updates navigation, source catalogs, skills guidance, MCP knowledge content and adoption contracts. The SQLite fixture remains a bounded local implementation. It does not retrofit every sovereign runtime, gateway or remote service with distributed v3.5 enforcement. Those integrations must meet the acceptance cases above before their claims change.

Refresh copied skills and client caches from the reviewed revision. Keep the knowledge server read-only with respect to operating authority. Keep paid-tier access, model agreement, human approval, runtime admissibility and verified effect evidence as different concepts.

[Framework Home](../README.md) | [Migration](../MIGRATION.md) | [Component versions](COMPONENT-VERSIONS.md) | [Complete page map](../PAGE_MAP.md)
