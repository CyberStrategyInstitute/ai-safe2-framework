# CP.5.CUA | v3.5 profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## CP.5 | C28

Separate enterprise and personal purpose, account, bystander consent, browser state and offboarding. Core consent and isolation still apply.

- **CP.5.R07** For personal agents, separate personal and enterprise accounts, state, purposes, consent and offboarding.
- **CP.5.R08** Keep bystander data and derived-state reuse within explicitly recorded scope.

**Acceptance** Personal-agent authority and continuity. Verify account separation and derived-data revocation across session changes.

[Research](../research/052_v35_c28.md)

## CP.5 | C40

Browser interfaces and native apps have distinct observation and action semantics. A browser-only profile loses native computer-use evidence. Shared final-effect controls remain inherited. Image and accessibility observations can be incomplete.

- **CP.5.R15** Record target application, account, document or page identity and relevant state before a material action.
- **CP.5.R16** Require an observation fresh enough to identify the intended control and handle asynchronous state changes.
- **CP.5.R17** Recheck the target after focus, navigation, layout, modal or account changes.
- **CP.5.R18** Verify the resulting application or business state independently of the click or screenshot.
- **CP.5.R19** Declare unsupported surfaces and evidence limitations; keep native-app and browser fixtures distinct.

**Acceptance** Exercise stale screenshots, delayed page state, changed window focus, modal interception and a click that leaves the postcondition unmet. Preserve the source DOM-settle proposal as browser-specific treatment.

[Research](../research/064_v35_c40.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
