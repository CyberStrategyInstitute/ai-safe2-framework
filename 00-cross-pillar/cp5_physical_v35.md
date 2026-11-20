# CP.5.PHYSICAL | v3.5 candidate profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## CP.5 | C31

A local controller, safety envelope and safe degraded state differ materially from ordinary digital tools. Generalize final-effect authorization while keeping physical assurance domain-specific.

- **CP.5.R13** For physical effects, enforce a domain-specific safety envelope and a locally available safe degraded state.
- **CP.5.R14** Exercise connectivity loss, cloud outage and agent termination without introducing unsafe controller behavior.

**Acceptance** Physical action and degraded operation. Use synthetic device states and measure recovery and human intervention.

[Research](../research/055_v35_c31.md)

## F3.7 | C34

Isolation alone does not establish which environment an authorized action targets. A distinct effect gate makes production/development assertions independently testable. Environment identity management and emergency procedures add operational cost.

- **F3.7.R01** Bind action authority to a verified environment, tenant and resource identity.
- **F3.7.R02** Require an independently issued environment assertion for destructive or material operations.
- **F3.7.R03** Refuse a mismatched, expired or unknown environment assertion and prevent agent self-issuance.
- **F3.7.R04** Revalidate after a route, account, region, resource alias or environment change.

**Acceptance** Run synthetic development/production twins and verify that changed endpoint or account cannot redirect an approval. Validate the cited incidents individually before attributing their causes.

[Research](../research/058_v35_c34.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
