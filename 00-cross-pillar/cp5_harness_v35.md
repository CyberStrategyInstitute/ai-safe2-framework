# CP.5.HARNESS | v3.5 candidate profile

This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.

## S1.8 | C02

The boundary precedes normal task authorization. A generic sandbox control can miss startup behavior. A distinct control introduces a separate platform verification burden.

- **S1.8.R01** Before trust is established, prevent project or externally supplied hooks, helpers, plugins, package scripts, credential reads and network callbacks from executing.
- **S1.8.R02** Separate preview and discovery from execution and credential access; inventory all enabled startup paths.
- **S1.8.R03** Exercise hostile synthetic projects and preserve process, file and network observations together with a valid trusted-project control.

**Acceptance** Pre-trust execution in harnesses. Verify synthetic untrusted project opening has zero prohibited effects and trusted opening still works.

[Research](../research/026_v35_c02.md)

## CP.5 | C25

C02 owns the universal pre-trust rule. Coding and IDE profiles need startup, workspace, skill and permission-change checks. A profile improves specificity at the cost of version tracking.

- **CP.5.R01** For coding harnesses, enumerate and gate project startup, hooks, skills, helpers, credentials and configured subprocesses.
- **CP.5.R02** Bind changed workspace, skill and endpoint permissions to a reviewed trust decision.

**Acceptance** Harness startup and skill composition. Document which launch and update paths are actually covered.

[Research](../research/049_v35_c25.md)

[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)
