# Review And Mapping

Use this reference for architecture reviews, code reviews, and compliance-oriented responses.

## Five Pillars Plus Cross-Pillar Governance

### P1: Sanitize and Isolate

Focus on input validation, indirect injection, trust boundaries, memory write controls, credential compartmentalization, and sensitive-data handling.

### P2: Audit and Inventory

Focus on execution traces, model and tool lineage, agent inventories, state changes, and evidence quality.

### P3: Fail-Safe and Recovery

Focus on recursion limits, abort paths, rollback, kill switches, and containment of multi-agent cascades.

### P4: Engage and Monitor

Focus on misuse detection, anomaly detection, human approval flows, monitoring, and operational alerting.

### P5: Evolve and Educate

Focus on red-team cadence, evaluation libraries, capability reviews, and iterative control hardening.

### CP: Cross-Pillar Governance

Focus on ACT tiers, HEAR, catastrophic-risk thresholds, replication governance, and organization-wide control-plane decisions.

## Architecture Review Workflow

For design reviews, walk the system in this order:

1. Identify trust boundaries, tool boundaries, memory boundaries, and regulated data.
2. Determine the ACT tier and whether the system delegates to other agents.
3. Check whether the design has traceability, human approval, and fail-safe behavior.
4. Identify which controls need to exist before deployment versus after launch.
5. Name the evidence artifacts the team should produce.

## Code Review Workflow

When reviewing code, findings should be the main output.

Check for:

- Prompt injection and indirect injection
- Secret leakage into prompts, context, traces, or logs
- Unsafe tool access or over-broad permissions
- Ungoverned memory writes or retrieval poisoning paths
- Missing execution tracing
- Missing recursion limits or abort conditions
- Missing approval gates for high-impact actions

Each finding should include:

- The control ID
- The concrete issue
- The user or business risk
- The code or config fix
- The evidence artifact created by the fix

## Compliance Mapping Pattern

For compliance requests:

1. Translate the requirement into one or more AI SAFE2 controls.
2. Explain the operational implementation, not just the policy statement.
3. Name the evidence the implementation produces.
4. Note the framework family impacted, such as ISO 42001, NIST AI RMF, EU AI Act, SOC 2, HIPAA, GDPR, PCI-DSS, FedRAMP, CMMC 2.0, or DORA.

## Evidence Examples

Common evidence artifacts include:

- ACT tier classification records
- HEAR designation records
- Replication governance policies and lineage logs
- Semantic execution trace logs
- Agent inventory snapshots
- Prompt and memory safety policies
- Approval workflow records
- Monitoring and incident response procedures
