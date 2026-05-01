# CP.5.MCP: MCP Server Security Profile
**Full Control Specification | April 2026 | AI SAFE2 v3.0**

**Status:** `Active` &nbsp;|&nbsp; **Priority:** `HIGH` &nbsp;|&nbsp; **Pillar:** Cross-Pillar Governance OS (CP.5)

**Research foundation:**
[Research Note 023 — MCP Server Security Profile](../research/023_mcp-server-security-profile.md) &nbsp;|&nbsp;
[Research Note 024 — MCP Consumer Protection](../research/024_mcp_consumer_protection.md)

**Reference implementation:** [AI SAFE2 MCP Security Toolkit](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/mcp-security-toolkit)

---

## Navigation

**Controls**

[MCP-1: No Dynamic Command Construction](#mcp-1-no-dynamic-command-construction) &nbsp;|&nbsp;
[MCP-2: Output Sanitization](#mcp-2-output-sanitization-before-llm-return) &nbsp;|&nbsp;
[MCP-3: Registry Provenance](#mcp-3-registry-provenance-verification) &nbsp;|&nbsp;
[MCP-4: STDIO Integrity](#mcp-4-stdio-transport-integrity-binding) &nbsp;|&nbsp;
[MCP-5: Tool Audit Log](#mcp-5-tool-invocation-audit-log) &nbsp;|&nbsp;
[MCP-6: Network Isolation](#mcp-6-mcp-server-network-isolation) &nbsp;|&nbsp;
[MCP-7: Zero-Trust Config](#mcp-7-zero-trust-client-configuration) &nbsp;|&nbsp;
[MCP-8: Session Economics](#mcp-8-session-economics-controls) &nbsp;|&nbsp;
[MCP-9: Context-Tool Isolation](#mcp-9-context-tool-isolation) &nbsp;|&nbsp;
[MCP-10: Delegation Edge Monitoring](#mcp-10-multi-agent-provenance-and-delegation-edge-monitoring) &nbsp;|&nbsp;
[MCP-11: Schema Temporal Profiling](#mcp-11-schema-temporal-profiling) &nbsp;|&nbsp;
[MCP-12: Swarm C2 Detection](#mcp-12-swarm-c2-detection-controls) &nbsp;|&nbsp;
[MCP-13: Failure Taxonomy Extension](#mcp-13-mcp-failure-mode-taxonomy-extension)

**Reference**

[ACT Tier Applicability](#act-tier-applicability) &nbsp;|&nbsp;
[Compliance Mapping](#compliance-mapping) &nbsp;|&nbsp;
[Consumer Protection Controls](#consumer-protection-controls) &nbsp;|&nbsp;
[Reference Implementation](#reference-implementation) &nbsp;|&nbsp;
[Cross-Pillar Dependencies](#cross-pillar-dependencies)

---

## Overview

CP.5 requires that protocol-layer meshes be assessed as first-class supply chain components. MCP's threat profile is materially different from every other platform currently covered in CP.5. The differences are not superficial — they change which controls apply, where they apply, and what failure looks like.

Three structural conditions drive the distinct profile:

**The STDIO transport model eliminates the network boundary.** Every other platform in CP.5 operates with a network boundary between the agent execution environment and external tool services. MCP's default transport runs the server as a subprocess of the host agent process. No network hop exists. The tool service and the agent runtime share the same process space boundary. Network-layer controls provide no coverage here.

**The return path is a first-class injection surface.** Standard agentic architectures treat the input path as the injection surface. MCP inverts this. Tool responses are returned into the LLM's context window as trusted output. The agent has no native mechanism to distinguish a legitimate response from a crafted payload embedded in a response body. The OX Security April 2026 disclosure demonstrated working exploits against this surface across 200,000+ instances.

**SDK-level vulnerability propagation is structural, not versioned.** The RCE pattern in `StdioServerParameters` exists wherever the unsafe dynamic command construction pattern is used, across every downstream implementation built on the official SDKs. At 150M+ downloads, a single widely distributed MCP server using this pattern has enterprise-scale blast radius.

The 13 controls in this profile address these conditions as a unified posture. Controls MCP-1 through MCP-7 address the foundational supply chain, injection, and transport surfaces established at v3.0 release. Controls MCP-8 through MCP-13 address four threat classes confirmed post-release: API billing amplification, context-tool isolation failure, multi-agent lateral movement, schema mutation, Swarm C2, and failure taxonomy gaps. Both sets are mandatory at their respective ACT tiers.

---

## MCP Controls

---

### MCP-1: No Dynamic Command Construction

**Problem addressed:** The OX Security April 2026 disclosure documented RCE exposure in the official Anthropic MCP Python and TypeScript SDKs via `StdioServerParameters`. When user-controlled or tool-response-controlled input is passed into the command parameter, the SDK executes it as a system command without sanitization. This is a pattern vulnerability — it is not bound to a specific version or CVE. It exists wherever the unsafe pattern appears. A single widely distributed MCP server using this pattern is sufficient to compromise the host agent's execution context across every organization that has added that server to their agent configuration.

**Required implementation:**

User-controlled input and tool-response-controlled input MUST NOT be passed into `StdioServerParameters`, `subprocess`, `os.system`, or equivalents. Server command parameters MUST be statically defined at build time. Any MCP server receiving dynamic input MUST validate against a strict allowlist of permitted values before using it in any system call context. The allowlist MUST be defined at build time, not at runtime.

> [!IMPORTANT]
> This control MUST be enforced via static analysis in CI/CD. A build that introduces dynamic command construction MUST fail the gate before deployment. Manual code review is insufficient — the pattern is easy to introduce and difficult to catch in review.

**AI SAFE2 controls operationalized:** P1.T1.10 (Indirect Injection Surface Coverage)
**MITRE ATLAS:** AML.T0005 (Exploit Public-Facing Application)
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-2: Output Sanitization Before LLM Return

**Problem addressed:** MCP inverts the standard injection threat model. In standard agentic architectures, the injection surface is the input path. In MCP, the return path from tool calls is a first-class injection surface. The OX Security research demonstrated that a malicious or compromised server returns a tool result containing an instruction-override payload that the calling LLM processes as authoritative context. The attack requires no access to the agent's system prompt, no session hijacking, and no user interaction beyond the tool call the agent initiated. Tool responses carrying zero-width characters, role-confusion markers, or instruction-override phrases are indistinguishable from legitimate responses at the transport layer.

This threat maps to S1.3 (Semantic Isolation Boundary Enforcement): tool output is not trusted context by default, and the boundary between trusted and untrusted context must be enforced at the transport layer.

**Required implementation:**

All MCP tool results MUST be scanned for prompt injection patterns before returning to any calling client. Scan scope must include instruction-override phrases, role-confusion markers, zero-width characters, and target LLM special tokens. Apply `sanitize_value()` from `aisafe2_mcp_tools.shared.patterns` or an equivalent implementation validated against the same pattern library. Detected patterns MUST be logged and redacted before the response reaches the model's context window.

> [!IMPORTANT]
> The Agentic Control Plane (CP.4) MUST enforce this boundary at the orchestration layer. Delegation to individual tool implementations is not sufficient. Consumer-side tooling (`mcp-safe-wrap`) provides a complementary layer but does not substitute for server-side enforcement.

**AI SAFE2 controls operationalized:** S1.3 (Semantic Isolation Boundary Enforcement), S1.6
**MITRE ATLAS:** AML.T0051 (Prompt Injection)
**OWASP LLM:** LLM01 (Prompt Injection), LLM02 (Insecure Output Handling)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-3: Registry Provenance Verification

**Problem addressed:** Tool squatting is a documented supply chain attack path with no existing platform-level control in any governance framework prior to AI SAFE2 v3.0. An attacker publishes a malicious MCP server named to be confused with a legitimate one. The server enters an organization's agent configuration via registry confusion — no compromise of the legitimate server is required. The MCP public registry lists hundreds of third-party servers with no mandatory provenance controls. Integration into AI IDEs (Cursor, VS Code with Copilot, Claude Code) as a default configuration mechanism amplifies the attack surface: a single poisoned `.mcp.json` committed to a repository triggers automatic server installation across every developer who pulls it.

**Required implementation:**

All third-party MCP servers MUST be verified against the official GitHub MCP Registry before being added to any agent configuration. A manifest-based allowlist of approved server commands MUST be maintained and enforced. Any server not on the allowlist MUST be rejected before reaching agent configuration. Allowlist updates MUST be treated as change management events — not ad hoc configuration changes — and must include provenance verification, integrity check, and documented approval.

> [!NOTE]
> The relationship to CP.7 is complementary and both are required. CP.7 honeypot endpoints catch squatted or compromised servers that reach invocation. MCP-3 prevents unauthorized servers from reaching invocation at all. Neither control is sufficient alone. CP.7 coverage MUST include at least one honeypot MCP tool endpoint in any deployment where third-party servers are in use.

**AI SAFE2 controls operationalized:** A2.3 (Model Lineage Provenance Ledger), CP.7
**MITRE ATLAS:** AML.T0002 (Backdoor ML Model)
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-4: STDIO Transport Integrity Binding

**Problem addressed:** The STDIO transport model that eliminates the inbound network boundary also eliminates network-layer detection for post-installation binary tampering. A verified MCP server binary replaced or modified after installation gains direct channel access to the agent's context window without triggering any network-layer control. Standard file integrity monitoring addresses this only if it is already deployed and scoped to the specific binary path — most agent deployment configurations do not include this.

The attack surface is the inter-process communication layer between the host agent and the MCP server subprocess. Any verification that operates at the network layer cannot reach this surface.

**Required implementation:**

For STDIO-mode deployments, the source file hash MUST be verified against an approved manifest before the server process is granted elevated tier access. The hash manifest MUST be maintained outside the server process and outside any path writable by the server process. Hash verification MUST occur at each session startup, not only at installation time. The manifest update process MUST follow the same change management requirements as MCP-3.

> [!WARNING]
> This control MUST fail closed on integrity failure. An unverifiable binary MUST NOT execute. Execution of an unverified binary is treated as a supply chain compromise event and triggers CP.8 review.

**AI SAFE2 controls operationalized:** A2.3 (Model Lineage Provenance Ledger)
**MITRE ATLAS:** AML.T0002 (Backdoor ML Model), AML.T0005 (Exploit Public-Facing Application)
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-5: Tool Invocation Audit Log

**Problem addressed:** Behavioral change in MCP-connected agents is forensically undetectable without a tool invocation audit trail. The slow behavioral conditioning attack profile (Research Note 023, Section 3.2) operates over multiple sessions. A compromised server returning subtly manipulated outputs produces behavioral drift that is indistinguishable from model drift unless tool call history is captured with response-level granularity.

Standard agent audit logs capture reasoning traces but not the tool call results that informed that reasoning. This creates a forensic gap: when behavioral change is detected, no record links it to specific MCP tool invocations. The Postmark supply chain incident (Research Note 024) demonstrates the operational consequence — silent exfiltration operating over an extended period with no detectable signals because tool behavior was functionally correct throughout.

**Required implementation:**

Every MCP tool call MUST generate an immutable audit record capturing tool name, parameters, response hash, timestamp, and calling agent identity. Records MUST be consistent with A2.5 (Semantic Execution Trace Logging). Each record MUST be cross-referenced against the behavioral baseline (F3.4) to detect unexpected invocations. Deviations MUST trigger alert before the next human review checkpoint.

> [!IMPORTANT]
> The audit log MUST be stored outside the agent process and outside any filesystem path accessible to MCP server processes. Writability by the server process would allow a compromised server to tamper with its own audit trail. The minimum format standard is the immutable JSONL log implemented by `mcp-safe-wrap` (Research Note 024). For ACT-3 and ACT-4 deployments, audit log coverage MUST be verified before deployment approval.

**AI SAFE2 controls operationalized:** A2.5 (Semantic Execution Trace Logging), A2.6, F3.4
**MITRE ATLAS:** AML.T0043 (Craft Adversarial Data)
**OWASP LLM:** LLM08 (Excessive Agency)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-6: MCP Server Network Isolation

**Problem addressed:** MCP servers running as subprocesses of the host agent inherit the host's network capabilities by default. A compromised server has a direct exfiltration path to any endpoint reachable from the host process. The STDIO transport model creates symmetric risk on the outbound path: outbound traffic from a compromised server is not subject to API gateway inspection or standard egress controls.

The September 2025 Postmark supply chain incident (Research Note 024) demonstrated silent exfiltration operating undetected over an extended period. Tool behavior was functionally correct throughout — every processed payload was forwarded to an attacker-controlled server while returning legitimate results to the calling agent. No consumer-visible signals were present because the exfiltration channel was the server's unrestricted outbound access.

**Required implementation:**

MCP servers MUST NOT have unrestricted outbound network access unless that access is explicitly required for their defined function and documented in the approved manifest. Allowlist-based egress filtering MUST be applied. Any outbound connection not on the approved egress allowlist MUST be blocked and logged as a potential exfiltration event. For STDIO deployments, process-level network namespace isolation MUST be applied where the host OS supports it.

> [!NOTE]
> The `mcp-safe-wrap` SSRF URL blocking (Research Note 024) provides the consumer-side complement to this control. Server-side egress control is independently required and does not become optional when consumer-side controls are present.

**AI SAFE2 controls operationalized:** S1.5
**MITRE ATLAS:** AML.T0048 (Resource Denial of Service), AML.T0005
**OWASP LLM:** LLM02 (Insecure Output Handling), LLM10 (Model Theft / Exfiltration)
**ACT Tier:** ACT-3+ mandatory

[↑ Navigation](#navigation)

---

### MCP-7: Zero-Trust Client Configuration

**Problem addressed:** AI IDE integrations (Cursor, VS Code with Copilot, Claude Code) treat repository-sourced MCP configurations as trusted by default. A malicious `.mcp.json` or `claude_desktop_config.json` committed to any repository the operator does not control executes with agent-level trust on the next session startup.

The rug pull attack vector (temporal profile `delayed_weeks`, Research Note 023 Section 3.2) operates through this surface. A server with established trust mutates its tool descriptions between sessions. The consumer's AI client has no native mechanism to detect that schemas changed. Injected instructions arrive as trusted tool metadata at the next session startup. Research Note 024 further documents cross-server OAuth token reuse exposure (CVE-2025-69196, CVE-2026-27124 class) as a direct consequence of default client behavior with untrusted server configurations.

**Required implementation:**

Any MCP server configuration sourced from a repository the operator does not control MUST be treated as an untrusted artifact. Proxy wrapping MUST be applied to all third-party STDIO connections. Tool schema hashes MUST be recorded at initial trust establishment. On every subsequent session startup, the current `tools/list` response hash MUST be compared against the recorded baseline. Any hash change not accompanied by a documented release event MUST trigger MCP-11 temporal profiling review and require human authorization before the new schema is trusted.

> [!CAUTION]
> Servers scoring below 50 on `mcp-score` assessment (Research Note 024) MUST NOT be connected to production systems. Servers scoring below 70 MUST be proxied through `mcp-safe-wrap`. The AI SAFE2 MCP badge (70+ score) is the verifiable signal that a server meets the minimum CP.5.MCP standard.

**AI SAFE2 controls operationalized:** CP.4 (Agentic Control Plane)
**MITRE ATLAS:** AML.T0002 (Backdoor ML Model)
**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities)
**ACT Tier:** ACT-3+ mandatory

[↑ Navigation](#navigation)

---

### MCP-8: Session Economics Controls

**Problem addressed:** The Phantom framework (November 2025) demonstrated 658x API cost amplification via tool response steering with a 97% miss rate from standard defenses. Standard defenses check inputs. Phantom operates in tool response bodies — a surface MCP-2 addresses at the content level but not the economics level. The November 2025 incident produced a $47,000 API bill from four agents in an infinite retry loop. API billing amplification is a consumer-borne loss: the server operator carries no financial consequence regardless of whether the amplification was intentional (ATPA) or a configuration failure.

**Required implementation:**

Every MCP-enabled agent session MUST carry a declared token budget (maximum tokens allowed per session) and a cost ceiling (maximum dollar spend per session). Sessions exceeding either threshold MUST halt execution and require human authorization to continue. Per-tool rolling call frequency baselines MUST be maintained at the orchestration layer. Deviations exceeding 3 standard deviations from the rolling baseline MUST trigger CP.8 review and potential session suspension.

> [!WARNING]
> API billing events exceeding 3x expected daily spend are classified as potential Phantom amplification attacks. These MUST trigger CP.1 incident tagging with `cognitive_surface = model`, `memory_persistence = session`. Detection of anomalous tool call frequency must be implemented at the orchestration layer — individual tool implementations cannot be relied upon to self-report.

**MITRE ATLAS:** AML.T0048 (Resource Denial of Service via Cost Exhaustion)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-9: Context-Tool Isolation

**Problem addressed:** MCP-UPD (Parasitic Toolchain Attacks, Zhao et al. September 2025) demonstrated that external data retrieved via MCP tools can carry injected instructions into the LLM context as trusted content. 92.9% of MCP server categories can participate as attack capabilities in an MCP-UPD chain. The attack requires zero direct victim interaction. The root architectural cause: MCP does not separate untrusted external content from executable instructions. Tool metadata and retrieved data occupy the same context segment with no isolation boundary.

**Required implementation:**

External data retrieved via MCP tools (documents, web pages, database records, API responses, email content) MUST be classified as untrusted data-plane content. This content MUST be processed through a semantic firewall before reaching the model's instruction context. Tool metadata (descriptions, parameter definitions) and retrieved data-plane content MUST occupy separate, isolated context segments. Apply `sanitize_value()` from `aisafe2_mcp_tools.shared.patterns` or equivalent to all externally-sourced content. The Agentic Control Plane (CP.4) MUST enforce this boundary — it cannot be delegated to individual tool implementations.

> [!IMPORTANT]
> Monitor for the MCP-UPD three-phase pattern: (1) retrieval tool invocations (`get_file`, `read_document`, `search_db`) followed by (2) disclosure tool invocations (`send_email`, `post_webhook`, `write_file`) (3) without an explicit human-authorized workflow connecting phases 1 and 2. Detection of this sequence without an authorized workflow is a CP.8-class event.

**MITRE ATLAS:** AML.T0002 (Backdoor ML Model), AML.T0051 (Prompt Injection)
**OWASP LLM:** LLM01 (Prompt Injection), LLM02 (Insecure Output Handling)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-10: Multi-Agent Provenance and Delegation Edge Monitoring

**Problem addressed:** Multi-agent lateral movement propagates through delegation edges — the handoffs between agents — not through individual agent compromise. Each individual agent behaves normally. The anomaly is in the pattern of delegation. Per-agent monitoring cannot detect this. The ARMO April 2026 research identifies delegation edges, shared context and memory layers, and orchestrator nodes as the three surfaces per-agent sensors cannot cover.

**Required implementation:**

In multi-agent deployments, every MCP tool call MUST carry a provenance chain identifying the originating agent identity, the full delegation path from origin to current executor, and the delegation depth (hop count). A cryptographic lineage token (per AI SAFE2 v3.0 CP.9 ARG specification) MUST travel with every agent through MCP delegation chains. Tool server invocations without a traceable originating agent request MUST be flagged as anomalous and reviewed. Instrument delegation edges, not individual agents. Build baselines for inter-agent handoff patterns and alert on chains that deviate from expected topology.

> [!IMPORTANT]
> For ACT-4 deployments: CP.9 lineage token propagation through all MCP delegation chains is mandatory, with a maximum delegation depth of 3 hops. Kill switch MUST sever the full delegation tree within 500ms — not just the offending agent.

**MITRE ATLAS:** AML.T0015 (Evade ML Model), AML.T0043 (Craft Adversarial Data)
**ACT Tier:** ACT-3+ mandatory; ACT-4 requires full CP.9 lineage token integration

[↑ Navigation](#navigation)

---

### MCP-11: Schema Temporal Profiling

**Problem addressed:** CP.2 (Adversarial ML Threat Model Integration) requires temporal profiling for all known threats. MCP-specific threats have distinct temporal signatures that CP.2 records must capture. Without MCP-specific temporal entries, the threat model omits the time dimension of MCP attacks. The rug pull (`delayed_weeks`) and persistent memory injection (`chronic`) profiles are the highest-risk categories from an organizational detection standpoint — both are indistinguishable from model drift without the audit trail required by MCP-5 and the temporal classification required here.

**Required implementation:**

For all ACT-2 and above MCP deployments, the CP.2 threat model MUST include MCP-specific entries with temporal profiles:

| Threat | Required `temporal_profile` |
| :--- | :--- |
| Rug pull attack | `delayed_weeks` — trust established before attack activates |
| Persistent memory injection | `chronic` — effect accumulates over sessions |
| ATPA (response-body steering) | `immediate` — activates on next tool invocation |
| API billing amplification | `immediate\|delayed_days` — billing begins immediately; detection may lag |
| Supply chain compromise | `delayed_days` — compromise precedes detection by days |
| Swarm C2 establishment | `immediate` — operational as soon as server is deployed |

Schema change detection MUST be implemented as a baseline-and-diff process: record the `tools/list` response hash at deployment, and alert on any change detected at session startup that was not accompanied by a documented release event.

> [!NOTE]
> Schema temporal profiling is the detection complement to MCP-7's prevention posture. MCP-7 prevents unauthorized schema changes from being trusted. MCP-11 ensures the threat model captures the time-delayed attack patterns that make schema mutation effective as a stealth vector.

**OWASP LLM:** LLM05 (Supply Chain Vulnerabilities)
**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

### MCP-12: Swarm C2 Detection Controls

**Problem addressed:** Vectra AI February 2026 research demonstrated that MCP can be weaponized as a C2 fabric for offensive agent swarms. MCP-based C2 traffic is semantically indistinguishable from legitimate enterprise AI tool use at the per-request level. Traditional C2 detection (beaconing signatures, connection patterns) does not apply. The only detection surface is behavioral topology analysis at the inter-agent level.

**Required implementation:**

Network monitoring for MCP deployments MUST include semantic traffic analysis capabilities that can distinguish legitimate agent-to-agent coordination from adversarial Swarm C2 patterns. Behavioral baselines for inter-agent communication topology MUST be established at deployment and updated as the legitimate workflow evolves. CP.7 honeypot tool endpoints MUST be deployed as canaries within multi-agent environments. Invocations of honeypot tools by unexpected agents are immediate CP.8 threshold events. Communication topology deviations MUST trigger CP.1 incident taxonomy tagging with `cognitive_surface = both`, `memory_persistence = cross_session`.

> [!CAUTION]
> This control requires coordination with CP.7 (honeypot deployment), CP.8 (threshold escalation), and CP.4 (control plane baseline). It cannot be implemented in isolation. A partial implementation that deploys honeypots without CP.8 threshold configuration produces detection events with no escalation path.

**MITRE ATLAS:** AML.T0008 (Develop Capabilities), AML.T0043 (Craft Adversarial Data)
**ACT Tier:** ACT-3+ mandatory

[↑ Navigation](#navigation)

---

### MCP-13: MCP Failure Mode Taxonomy Extension

**Problem addressed:** CP.1 (Agent Failure Mode Taxonomy) requires all agentic incidents to be tagged with `cognitive_surface` and `memory_persistence`. Without an MCP-specific extension, MCP incidents are miscategorized. MCP-UPD is a cross-session memory concern — not a session-bounded prompt injection. Multi-agent lateral movement involves both model and memory surfaces. The wrong taxonomy tag produces the wrong remediation path: an MCP-UPD incident tagged as session-bounded receives session-level remediation while the actual cross-session memory vector remains unaddressed.

**Required implementation:**

MCP-specific failure events MUST be tagged with the following CP.1 cross-cutting dimensions:

| MCP Failure Class | `cognitive_surface` | `memory_persistence` | Remediation Path |
| :--- | :--- | :--- | :--- |
| Tool description injection (TPA) | `model` | `session` | Output sanitization (MCP-2) |
| Persistent memory injection | `memory` | `cross_session` | Full memory flush across all agents |
| MCP-UPD parasitic toolchain | `model` | `cross_session` | Context-tool isolation (MCP-9) |
| Multi-agent lateral movement | `both` | `cross_session` | Delegation edge monitoring (MCP-10) |
| Supply chain / rug pull | `model` | `session` | Schema temporal profiling (MCP-11) |
| Billing amplification | `model` | `session` | Session economics (MCP-8) |
| Swarm C2 | `both` | `cross_session` | Swarm detection (MCP-12) |

> [!WARNING]
> The `cross_session` tag for MCP-UPD and persistent memory injection mandates full memory flush across all agents in the chain — not session-level remediation. Without this taxonomy tag enforced at triage, incident response addresses the wrong layer and the attack surface remains active.

**ACT Tier:** ACT-2+ mandatory

[↑ Navigation](#navigation)

---

## ACT Tier Applicability

| Control | ACT-1 | ACT-2 | ACT-3 | ACT-4 |
| :--- | :---: | :---: | :---: | :---: |
| MCP-1 No Dynamic Commands | Recommended | **Mandatory** | Mandatory | Mandatory |
| MCP-2 Output Sanitization | Recommended | **Mandatory** | Mandatory | Mandatory |
| MCP-3 Registry Provenance | Recommended | **Mandatory** | Mandatory | Mandatory |
| MCP-4 STDIO Integrity | Recommended | **Mandatory** | Mandatory | Mandatory |
| MCP-5 Tool Audit Log | Recommended | **Mandatory** | Mandatory | Mandatory |
| MCP-6 Network Isolation | -- | Recommended | **Mandatory** | Mandatory |
| MCP-7 Zero-Trust Config | -- | Recommended | **Mandatory** | Mandatory |
| MCP-8 Session Economics | -- | **Mandatory** | Mandatory | Mandatory |
| MCP-9 Context-Tool Isolation | -- | **Mandatory** | Mandatory | Mandatory |
| MCP-10 Delegation Edge Monitoring | -- | -- | **Mandatory** | Mandatory + CP.9 |
| MCP-11 Schema Temporal Profiling | -- | **Mandatory** | Mandatory | Mandatory |
| MCP-12 Swarm C2 Detection | -- | -- | **Mandatory** | Mandatory |
| MCP-13 Failure Taxonomy Extension | -- | **Mandatory** | Mandatory | Mandatory |

[↑ Navigation](#navigation)

---

## Compliance Mapping

| MCP Control | AI SAFE2 v3.0 CP | NIST SP 800-53 | CMMC 2.0 | OWASP LLM | EU AI Act |
| :--- | :--- | :--- | :--- | :--- | :--- |
| MCP-1 | CP.3 ACT enforcement | SC-8, SI-7, SI-10 | SC.L2-3.13.8 | LLM05 | Art. 9 |
| MCP-2 | CP.2 temporal profiling | SI-10, SC-3, AC-4 | SI.L2-3.14.6 | LLM01 | Art. 9 |
| MCP-3 | CP.5, CP.6 IICR | SA-12, SR-3, SR-6 | SR.L3-3.17.4 | LLM05 | Art. 9 |
| MCP-4 | CP.4 control plane | SI-7, SA-12 | SI.L2-3.14.6 | LLM05 | Art. 9 |
| MCP-5 | CP.1 failure taxonomy | AU-2, AU-12 | AU.L2-3.3.1 | LLM08 | Art. 14 |
| MCP-6 | CP.8 CRT controls | SC-5, SC-7 | SC.L2-3.13.1 | LLM02 | Art. 9 |
| MCP-7 | CP.4, CP.5 | IA-2, AC-17 | IA.L2-3.5.3 | LLM05 | Art. 14 |
| MCP-8 | CP.8 CRT, CP.1 | SC-5, AU-12 | SC.L2-3.13.1 | -- | Art. 9 |
| MCP-9 | CP.4 control plane | SC-3, SI-10 | AC.L2-3.1.3 | LLM01 | Art. 9 |
| MCP-10 | CP.9 ARG, CP.4 | AC-4, AU-12 | AU.L2-3.3.1 | ASI03 | Art. 14 |
| MCP-11 | CP.2 AMLTM | SI-7, SI-4 | SI.L2-3.14.6 | LLM05 | Art. 9 |
| MCP-12 | CP.7, CP.8 | SI-3, SI-4 | SI.L2-3.14.2 | -- | Art. 14 |
| MCP-13 | CP.1 taxonomy | IR-4, AU-6 | IR.L2-3.6.1 | LLM08 | Art. 9 |

[↑ Navigation](#navigation)

---

## Consumer Protection Controls

Research Note 024 establishes that the consumer threat model is structurally different from the server operator's. Consumers cannot audit server source code, cannot verify what happens to their tool call parameters after they leave the proxy, and cannot inspect the server's output sanitization implementation. They are trusting a black box connected to their most capable AI system.

Five confirmed incident classes target consumers specifically: supply chain compromise without visible signals (Postmark, September 2025), rug pull without notification, billing amplification as consumer loss ($47,000, November 2025), cross-server OAuth token reuse (CVE-2025-69196, CVE-2026-27124 class), and persistent memory poisoning that persists across all future sessions.

The `mcp-safe-wrap` tool provides three runtime consumer protections regardless of what the connected server does:

**Output scanning** intercepts tool responses before they reach the LLM client. Injection payloads are redacted. This defends against both supply chain compromise and rug pull attacks (MCP-2 consumer-side complement).

**SSRF URL blocking** prevents any string value in tool call parameters matching a known SSRF target (AWS IMDS, RFC 1918, loopback, `file://`) from reaching the server (MCP-6 consumer-side complement).

**Immutable audit log** records every tool invocation and every injection detection to a JSONL file on the consumer's local filesystem. This is the only reliable forensic record when server-side logs are unavailable (MCP-5 consumer-side complement).

```bash
# Assess any external server before connecting
mcp-score https://server.example/mcp

# Proxy an external server through safe-wrap
mcp-safe-wrap proxy https://external-server.example/mcp --token your-token
```

> [!CAUTION]
> Servers scoring below 50 must not be connected to any production system. Servers scoring below 70 must be proxied through `mcp-safe-wrap`. Consumer-side controls reduce impact when compromise occurs. They do not substitute for server-side controls that reduce the probability of compromise.

Full consumer configuration checklist: [Research Note 024 — MCP Consumer Protection](../research/024_mcp_consumer_protection.md)

[↑ Navigation](#navigation)

---

## Reference Implementation

The AI SAFE2 MCP Security Toolkit implements CP.5.MCP controls as a verifiable open-source reference:

| Tool | Controls Verified | Mode |
| :--- | :--- | :--- |
| `mcp-score` | MCP-2, MCP-4, MCP-5, MCP-6, MCP-7 | Remote assessment |
| `mcp-scan` | MCP-1, MCP-2, MCP-3, MCP-4, MCP-5, MCP-6 | Static analysis |
| `mcp-safe-wrap` | MCP-2, MCP-6, MCP-7, MCP-9 | Consumer-side enforcement |

**Toolkit:** [github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/mcp-security-toolkit](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/mcp-security-toolkit)

**AI SAFE2 MCP Server (v3.0.1):** [github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/skills/mcp](https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/skills/mcp)

[↑ Navigation](#navigation)

---

## Cross-Pillar Dependencies

MCP controls interact with the following CPs. Implementing MCP controls in isolation without the referenced CPs produces incomplete coverage.

| MCP Control | Depends On | Relationship |
| :--- | :--- | :--- |
| MCP-3 | CP.7 | MCP-3 prevents unauthorized server configuration; CP.7 honeypots detect squatted servers that reach invocation |
| MCP-5 | CP.1, A2.5, F3.4 | Audit records feed CP.1 taxonomy tagging and F3.4 behavioral baseline |
| MCP-8 | CP.8, CP.1 | Billing threshold events are CP.8 class; incident tagging uses CP.1 taxonomy |
| MCP-9 | CP.4 | Context isolation boundary must be enforced at the CP.4 Agentic Control Plane |
| MCP-10 | CP.9 ARG | Lineage token propagation is defined in CP.9; MCP-10 extends it to delegation edges |
| MCP-12 | CP.4, CP.7, CP.8 | Cannot be implemented in isolation; requires CP.7 honeypots, CP.8 thresholds, CP.4 baseline |
| MCP-13 | CP.1 | Extends CP.1 taxonomy with MCP-specific failure classes and cross-session memory persistence tagging |

[↑ Navigation](#navigation)

---

*AI SAFE2 v3.0 | Cyber Strategy Institute | [cyberstrategyinstitute.com/ai-safe2/](https://cyberstrategyinstitute.com/ai-safe2/)*
