# MCP Server Security Profile

**Series:** AI SAFE2 v3.0 Research Foundation
**Topic:** Grounding CP.5.MCP — MCP Server as a First-Class Agent Attack Surface
**Controls Supported:** P1.T1.10, S1.3, S1.5, S1.6, A2.3, A2.5, A2.6, CP.3, CP.4, CP.5, CP.7, CP.8
**Date:** April 2026

---

## 1. Purpose

This research note grounds the CP.5.MCP sub-control added to CP.5 (Platform-Specific Agent Security Profiles) of AI SAFE2 v3.0.

CP.5 has always required that protocol-layer meshes be assessed as first-class supply chain components. MCP was implicitly included in that language. This note makes MCP explicit — and provides the technical rationale for why MCP requires its own named profile rather than inheriting generic protocol-mesh guidance.

The immediate trigger is the OX Security research published in April 2026, which documented RCE exposure in Anthropic's official MCP Python and TypeScript SDKs, demonstrated working tool response injection attacks that propagate payloads to every downstream implementation, and established tool squatting as a viable supply chain attack path. The research does not reveal a novel theoretical threat class. It documents a structural condition that has existed since MCP's design and maps it to working exploits.

The significance for AI SAFE2 v3.0 is architectural: MCP's threat profile is materially different from every other platform currently covered in CP.5. The differences are not superficial. They change which controls apply, where they apply, and what failure looks like.

---

## 2. The MCP Architecture Distinction

### 2.1 The STDIO Transport Model Eliminates the Network Boundary

Every other platform covered in CP.5 — Bedrock Agents, Azure AI Foundry, n8n, LangGraph, AutoGen, CrewAI — operates with a network boundary between the agent's execution environment and external tool services. That boundary is the foundation on which network-layer controls (egress filtering, TLS inspection, API gateway enforcement) are built.

MCP's default transport is STDIO. The MCP server process runs as a subprocess of the host agent process or AI IDE. There is no network hop. The tool service and the agent runtime share the same process space boundary.

The consequence is direct: the threat model is not "attacker communicates over a network to inject into the agent." The threat model is "attacker runs code in a process that has direct channel access to the agent's context window." Network-layer controls provide no coverage here. The attack surface is the inter-process communication layer.

This is the architectural basis for MCP-4 (STDIO Transport Integrity Binding) and MCP-6 (MCP Server Network Isolation). Neither control is redundant with existing network-layer controls — they address a surface those controls cannot reach.

### 2.2 The Return Path Is a First-Class Injection Surface

In standard agentic architectures, the injection surface is the input path: user messages, system prompts, retrieved documents. Output paths — what the agent writes — are governed as execution risk, not injection risk.

MCP inverts this assumption. When an agent calls an MCP tool, it sends a request and receives a response. That response is returned into the LLM's context window as trusted tool output. The agent has no native mechanism to distinguish a legitimate tool response from a crafted payload embedded in a tool response.

The OX Security research demonstrated this concretely: a malicious MCP server returns a tool result containing an instruction-override payload. The calling LLM processes it as authoritative context and executes the embedded instruction. The attack requires no access to the agent's system prompt, no session hijacking, and no user interaction beyond the tool call the agent initiated itself.

This is the architectural basis for MCP-2 (Output Sanitization Before LLM Return). The sanitization requirement is not an input-side control applied to outputs — it is a recognition that the return channel from MCP tools is a prompt injection surface that must be treated with the same scrutiny as user input.

This threat maps to P1.T1.10 (Indirect Injection Surface Coverage) and S1.3 (Semantic Isolation Boundary Enforcement) in AI SAFE2 v3.0. CP.5.MCP operationalizes those controls at the platform layer.

### 2.3 SDK-Level Vulnerability Propagation

The OX Security research identified the RCE vector in `StdioServerParameters`: when user-controlled or tool-response-controlled input is passed into the command parameter, the MCP SDK executes it as a system command without sanitization. The vulnerability exists in the official Anthropic Python and TypeScript SDKs.

The supply chain implication is structural. Every MCP server built on the official SDKs inherits this vulnerability unless the developer explicitly avoids the dynamic command construction pattern. It is not a vulnerability that requires finding a specific CVE in a specific version — it is a pattern vulnerability that exists wherever the unsafe pattern is used.

At 150M+ downloads, the downstream blast radius of a widely distributed MCP server using this pattern is enterprise-scale. A single poisoned third-party MCP server in an organization's agent tool configuration is sufficient to compromise the host agent's execution context.

This is the architectural basis for MCP-1 (No Dynamic Command Construction) and MCP-3 (Registry Provenance Verification). Both controls address the supply chain propagation path, not just the individual vulnerability instance.

---

## 3. The Supply Chain Dimension

### 3.1 Scale Creates Systemic Risk

MCP's adoption trajectory changes the supply chain risk calculus relative to other protocol-layer meshes. A2A, ACP, and equivalents are in active adoption but have not reached the same breadth of third-party server proliferation. MCP has a public registry of hundreds of third-party servers, active package distribution channels, and integration into AI IDEs (Cursor, VS Code with Copilot, Claude Code) as a default configuration mechanism.

The threat that CP.5.MCP addresses at MCP-3 (Registry Provenance Verification) is not theoretical — tool squatting, where a malicious MCP server is named to be confused with a legitimate server, is a documented attack path with no existing platform-level control in any governance framework. CP.7 (Deception and Active Defense Layer) provides detection via honeypot tool endpoints. CP.5.MCP provides prevention via allowlist enforcement before the server is ever added to agent configuration.

The relationship between CP.5.MCP and CP.7 is complementary: CP.7 catches squatted or compromised tools at invocation time; CP.5.MCP prevents unauthorized tools from reaching invocation. Both are required. Neither is sufficient alone.

### 3.2 Temporal Profile of MCP Supply Chain Attacks

Per the temporal profiling requirement in CP.2 (Adversarial ML Threat Model Integration), MCP supply chain attacks have a distinct temporal profile that separates them from other attack classes in the AISM threat matrix:

| Attack Vector | Temporal Profile | Detection Window |
| :--- | :--- | :--- |
| Direct tool response injection | immediate | Single tool call |
| Tool squatting via registry confusion | delayed\_days | Time between server addition and first invocation |
| Slow behavioral conditioning via poisoned outputs | delayed\_weeks | Multiple sessions before behavioral baseline deviation |
| SDK-level RCE via dynamic command construction | immediate | First execution of vulnerable pattern |

The delayed\_weeks profile for slow conditioning is the highest-risk category from an organizational detection standpoint. It maps to the `both / cross_session` cognitive surface and memory persistence combination defined in CP.1 and grounded in Research Note 001. An MCP server that returns subtly manipulated outputs over multiple sessions can produce behavioral drift indistinguishable from model drift without the audit trail required by MCP-5.

### 3.3 MCP in the ACT Tier Framework

The ACT tier applicability of CP.5.MCP reflects the relationship between agent autonomy and MCP exposure surface:

At ACT-1, the human reviewer sees all agent outputs before action. A tool response injection payload is visible before it causes harm. The control requirement is correspondingly lighter.

At ACT-2, the agent acts with human checkpoints. Tool call results are processed between checkpoints. MCP-1, MCP-2, and MCP-5 are mandatory because the injection-to-action window exists between human review cycles.

At ACT-3 and ACT-4, the agent operates with post-hoc review or orchestrates other agents. A tool response injection at ACT-3 can produce irreversible actions before review. At ACT-4, the injected payload propagates through the orchestrated agent network. All 7 controls are mandatory. At ACT-4, CP.9 lineage token propagation through MCP delegation chains is additionally required because any ACT-4 agent spawning sub-agents that call MCP tools creates a replication surface where the tool response injection can inherit the full delegation tree's authority.

---

## 4. Control Rationale

The following table maps each CP.5.MCP control to the threat vector it addresses, the AI SAFE2 v3.0 controls it operationalizes at the platform layer, and the failure mode it prevents:

| Control | Threat Vector | Controls Operationalized | Failure Mode Prevented |
| :--- | :--- | :--- | :--- |
| MCP-1: No Dynamic Command Construction | SDK-level RCE via `StdioServerParameters` | P1.T1.10 | Arbitrary code execution on host via crafted tool configuration |
| MCP-2: Output Sanitization Before LLM Return | Tool response prompt injection | S1.3, S1.6 | Instruction-override payloads executing as agent directives |
| MCP-3: Registry Provenance Verification | Tool squatting, supply chain substitution | A2.3, CP.7 | Unauthorized MCP server gaining agent tool access |
| MCP-4: STDIO Transport Integrity Binding | Tampered server binary post-installation | A2.3 | Modified server executing in place of verified implementation |
| MCP-5: Tool Invocation Audit Log | Undetected behavioral change, forensic gap | A2.5, A2.6, F3.4 | Inability to trace agent behavior change to MCP tool invocation |
| MCP-6: MCP Server Network Isolation | Data exfiltration via MCP server outbound | S1.5 | Agent memory or context exfiltrated via compromised tool server |
| MCP-7: Zero-Trust Client Configuration | Malicious server in IDE/agent config | CP.4 | Untrusted server configuration executing with agent-level trust |

---

## 5. Control Implications

### 5.1 Controls Directly Grounded in This Research

**P1.T1.10 — Indirect Injection Surface Coverage:** The requirement for indirect injection surface enumeration was introduced in AI SAFE2 v3.0 specifically to capture tool response channels as injection surfaces. MCP-2 is the platform-specific implementation of P1.T1.10 for MCP deployments. An organization that has implemented P1.T1.10 generically without an MCP-specific sanitization pipeline has a coverage gap.

**S1.3 — Semantic Isolation Boundary Enforcement:** Semantic isolation between trusted and untrusted context must extend to MCP tool responses. Tool output is not trusted context by default. MCP-2 enforces this boundary at the transport layer.

**A2.5 — Semantic Execution Trace Logging:** MCP-5 extends the A2.5 audit requirement to the tool invocation layer. An audit trail that captures agent reasoning but not the tool calls that informed that reasoning is incomplete for forensic purposes.

**A2.3 — Model Lineage Provenance Ledger:** The provenance requirement in A2.3 applies to MCP server implementations as supply chain components. MCP-3 and MCP-4 operationalize this for the MCP tool layer.

**CP.7 — Deception and Active Defense Layer:** Honeypot tool endpoints defined in CP.7 are the detection complement to MCP-3's prevention posture. CP.7 should include at least one honeypot MCP tool endpoint in any deployment where third-party MCP servers are in use.

**CP.8 — Catastrophic Risk Threshold Controls:** CP.8 example path (b) — protocol-layer supply chain compromise of widely deployed A2A or MCP servers — is directly addressed by CP.5.MCP as the prevention control. An MCP supply chain compromise that propagates through an ACT-4 orchestrator network meets the CP.8 threshold for emergency agent suspension. CP.5.MCP is the prevention layer; CP.8 is the response layer.

### 5.2 Organizational Procedures Implied

Organizations deploying MCP-connected agents should:

- Audit all existing MCP server configurations for dynamic command construction patterns (MCP-1) before the next security review cycle. This is not a future control — the vulnerability class exists in current deployments.
- Add MCP tool response channels to their indirect injection surface inventory under P1.T1.10. Current surface enumerations that list user input, system prompts, and RAG retrievals without listing tool response channels are incomplete for MCP-connected agents.
- Establish a manifest-based MCP server allowlist (MCP-3) as a prerequisite for any new MCP server addition to production agent configurations. Treat the allowlist update as a change management event, not an ad hoc configuration change.
- Extend CP.7 honeypot coverage to include at least one tool endpoint that should never be invoked in normal operation, positioned to detect tool squatting and adversarial MCP server probing.
- For ACT-3 and ACT-4 deployments, verify that A2.5 audit logs capture MCP tool invocation events at the granularity required by MCP-5 before deployment approval.

---

## 6. References

- OX Security: MCP Security Threat Research (April 2026). Documents RCE via `StdioServerParameters` in Anthropic MCP Python and TypeScript SDKs; demonstrates tool response injection and tool squatting attack paths.
- MITRE ATLAS AML.T0002 (Backdoor ML Model). Supply chain modification of MCP server implementations.
- MITRE ATLAS AML.T0005 (Exploit Public-Facing Application). Direct exploitation of MCP server interfaces.
- MITRE ATLAS AML.T0051 (Prompt Injection). Tool response injection as indirect prompt injection channel.
- OWASP LLM Top 10, LLM05: Supply Chain Vulnerabilities. MCP server ecosystem as agent supply chain.
- OWASP LLM Top 10, LLM10: Model Theft / Exfiltration. MCP server outbound channel as exfiltration path.
- OWASP AIVSS v0.8, Risk #5: Supply Chain and Plugin Vulnerabilities.
- AI SAFE2 v3.0 Framework, Research Note 023: Cognitive Surface and Memory Drift (grounding for `both / cross_session` MCP conditioning attack profile).
- AI SAFE2 v3.0 Framework, Sections P1.T1.10, S1.3, S1.5, S1.6, A2.3, A2.5, A2.6, F3.4, CP.3, CP.4, CP.5, CP.7, CP.8, CP.9.

---

*This research note is part of the AI SAFE2 v3.0 research foundation series. All content is derived exclusively from the source frameworks reviewed for v3.0. Cyber Strategy Institute, 2026.*
