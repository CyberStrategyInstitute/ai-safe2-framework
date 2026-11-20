# CP.5.GATEWAY | v3.5 candidate profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## CP.11 | C01

Discovery, installation, change, use and revocation span CP.4 and CP.5. A shared objective prevents each profile inventing its own state model. It adds ownership and migration cost.

- **CP.11.R01** Establish separate trust decisions at discovery, installation, initial approval, material change, task admission, action commitment and revocation.
- **CP.11.R02** Bind each decision to the component version, owner, purpose, permitted effects and expiry; invalidate affected grants after a material change.
- **CP.11.R03** Record the evidence and outcome of each gate and verify that retirement, offboarding and restore cannot reactivate stale authority.

**Acceptance** Trust between discovery and retirement. Compare install, update, dormant schedules and restoration. Show which decision expires at each transition.

[Research](../research/025_v35_c01.md)

## CP.12 | C03

The action can become inadmissible after approval even with correct identity and tool permissions. CP.4 remains the supporting control plane. A standalone requirement costs adapter and commit-boundary work.

- **CP.12.R01** Immediately before committing a consequential effect, an enforcement point outside the acting model shall validate principal, delegation, action, resource, environment, recipient, purpose, time, limits and required approval.
- **CP.12.R02** Bind approval to canonical action parameters and current policy/state versions; a changed material condition requires a new decision.
- **CP.12.R03** Refuse missing, expired, conflicting or unverified mandatory conditions and protect the gate and credentials from the governed agent.
- **CP.12.R04** Define atomic check/commit or destination-enforced version checks, replay resistance and the behavior for an unavailable authority service.

**Acceptance** Authority at commitment. Compare EFA, FlowSignal and AI SAFE2 using changed state, changed target, and an independently observed effect.

[Research](../research/027_v35_c03.md)

## CP.5 | C26

Gateways need policy/admin separation, upstream attribution, verified fallback and egress boundaries. Reuse C01, C03, C16 and C17. A separate core would duplicate policy authority.

- **CP.5.R03** For inference gateways, separate administrative policy, upstream credentials and execution authority from model responses.
- **CP.5.R04** Record actual routing and prevent unapproved endpoint or model substitution and permissive fallback.

**Acceptance** Inference routing and gateway trust. Measure actual provider attribution and enforcement across approved routes.

[Research](../research/050_v35_c26.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
