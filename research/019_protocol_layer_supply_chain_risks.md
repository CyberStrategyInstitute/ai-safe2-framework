# Research Note 4: Protocol-Layer Supply Chain Risks in Agentic AI

**Series:** AI SAFE2 v3.0 Research Foundation  
**Topic:** MCP, A2A, ACP, and NEXUS as First-Class Supply Chain Components  
**Controls Supported:** CP.4, CP.5, P2 (A2.3), P2.T3.10 (modification)  
**Date:** April 2026

---

## 1. Purpose

This research note grounds the CP.5 (Platform-Specific Agent Security Profiles) requirement that:

> *"Platform profiles MUST explicitly include protocol-layer meshes (A2A, MCP, ACP, NEXUS, and equivalent protocols) as first-class supply-chain components. These protocols SHOULD be assessed with the same depth as SaaS vendors and libraries, including identity, delegation, logging, and update channels."*

This requirement is a structural change in how AI supply chain governance is conceptualized. Existing supply chain controls in AI governance frameworks (including SAFE2 v2.1) focus on model artifacts, datasets, and software libraries. Protocol-layer meshes — the communication protocols that agents use to interact with tools and other agents — have not been treated as supply chain components. This research note explains why they should be, and what that means operationally.

---

## 2. The Protocol Layer as Supply Chain Infrastructure

### 2.1 What Protocol-Layer Meshes Are

In agentic AI deployments, agents do not interact directly with tools and APIs. They interact via protocols that mediate that communication:

- **MCP (Model Context Protocol)**: Defines how agents discover and invoke tools exposed by MCP servers. An MCP server is an intermediary that an agent connects to and queries for available tools.
- **A2A (Agent-to-Agent, Google)**: Defines how agents discover other agents, negotiate capabilities, and delegate tasks to each other.
- **ACP (Agent Communication Protocol)**: An emerging open standard for agent-to-agent communication with additional security properties.
- **NEXUS-A2A**: A protocol-layer mesh that extends A2A/MCP/ACP with DID/VC-anchored agent identity, mandate-based delegation, and NOR (Non-Repudiation of Record) audit logs.

These protocols are infrastructure. Every agent in a production deployment depends on the protocol stack through which it communicates. A compromised MCP server, a poisoned A2A agent directory, or a protocol that lacks identity verification is equivalent to a compromised library or dependency — except its blast radius can extend to every agent that relies on it.

### 2.2 Why Protocols Are Not Currently Treated as Supply Chain

Current supply chain governance frameworks focus on three artifact types: code (libraries, dependencies), models (weights, fine-tuned variants), and data (training datasets, RAG corpora). Protocols are not artifacts in this traditional sense — they are specifications implemented by software and operated as services. This category mismatch causes them to fall between supply chain governance and network security governance, receiving complete coverage from neither.

The gap is operationally significant:

- A compromised MCP server injecting adversarial tool descriptions to all connecting agents is a supply chain attack with the blast radius of a compromised dependency
- An A2A agent directory returning false agent capabilities (tool squatting at the protocol layer) is a supply chain attack with no current SAFE2 control explicitly governing it in v2.1
- A protocol specification update that introduces a new capability without adequate security review is equivalent to a silent library update with unknown side effects

---

## 3. Protocol-Specific Threat Models

### 3.1 MCP Threat Model

**NeighborJack-style binding**: MCP servers that bind to all network interfaces (0.0.0.0) rather than localhost expose themselves to any process or container on the same network. Production discovery revealed MCP servers installed alongside development tooling running in shared cloud environments. Result: all stored credentials accessible to any co-located process.

**Tool descriptor injection**: MCP tool descriptors (the JSON schema describing what a tool does and its parameters) can contain arbitrary text. Adversarial content embedded in tool descriptors — including invisible characters, instruction sequences, or role-assignment text — is passed to the LLM when it reads tool definitions, enabling indirect prompt injection without any user interaction.

**Update channel integrity**: MCP servers are typically distributed as npm packages or Python packages. A compromised package update silently changes tool behavior or injects adversarial content into tool descriptors for all connecting agents.

**Supply chain assessment criteria for MCP servers**:
- Does the server bind only to expected interfaces?
- Are tool descriptors validated against a schema before being passed to agents?
- Is the distribution channel cryptographically signed?
- Are update events logged and reviewed?
- What is the blast radius if this server is compromised — how many agents connect to it?

### 3.2 A2A Threat Model

**Agent card poisoning**: In Google A2A, agents advertise their capabilities via "agent cards" — JSON documents describing what the agent can do. An adversary who can modify or inject false agent cards can cause orchestrating agents to delegate tasks to malicious agents instead of legitimate ones. This is tool squatting at the protocol layer.

**Capability inflation**: A malicious agent claiming broader capabilities than it has will receive delegated tasks beyond what it should handle, enabling it to collect sensitive task context it was not intended to see.

**Discovery service compromise**: A2A uses a discovery mechanism to find available agents. Compromising the discovery service is equivalent to compromising a DNS server for agent networks — it can redirect all agent-to-agent communication.

**Supply chain assessment criteria for A2A participants**:
- Are agent cards signed by a verified identity?
- Is the discovery service operated by a trusted party with security SLAs?
- Are capability claims validated against observed behavior?
- Is agent-to-agent communication logged at the protocol layer?

### 3.3 ACP Threat Model

ACP is an emerging standard with a more explicit security model than A2A, including message authentication and structured capability negotiation. However, "emerging" means the security model is still being validated in production. Protocol-layer supply chain assessment of ACP deployments should explicitly evaluate:

- Message authentication implementation (are MACs or signatures validated, or only checked for presence?)
- Capability negotiation — can a receiver reject capabilities it doesn't support without silent downgrade?
- Logging: does the ACP implementation log protocol-level events to the organization's SIEM?

### 3.4 NEXUS-A2A as a Reference Implementation

NEXUS-A2A is the first agent coordination protocol designed from the ground up with the AI SAFE2 governance model in mind. Its security model addresses the primary supply chain risks in A2A and MCP:

- **DID/VC-anchored agent identity**: Agents are identified by Decentralized Identifiers with Verifiable Credentials — identity is cryptographically provable and not dependent on any central registry
- **Mandate-based delegation**: Delegated tasks are bound to explicit mandates (the scope of what the delegating agent is authorizing), preventing capability inflation attacks
- **NOR audit logs**: Non-Repudiation of Record logs provide tamper-evident protocol-level logging of all agent interactions
- **Cross-protocol coverage**: NEXUS-A2A operates across A2A, MCP, and ACP, providing unified governance coverage across the protocol stack

SAFE2 v3.0 scoring: NEXUS-A2A achieves 24/25 across SAFE2 CP.3 through CP.7 controls. Existing A2A and MCP implementations without the NEXUS security layer score 8-13/25 against the same controls.

---

## 4. The P2.T3.10 Modification: What Platform Scanning Must Now Include

AI SAFE2 v3.0 adds three bullets to P2.T3.10 (Vulnerability Scanning and Threat Assessment) specifically for protocol-layer scanning:

**MCP server security validation**: Scan for MCP servers bound to all network interfaces; validate tool descriptor integrity. This translates operationally to:
1. Enumerate all MCP servers in the environment (A2.4 agent state inventory should include MCP server connections)
2. For each server, check binding configuration (reject 0.0.0.0 bindings)
3. Validate tool descriptor schemas — tool names, descriptions, and parameters should not contain instruction sequences, system prompt language, or encoded payloads
4. Verify distribution channel signatures for MCP packages

**A2A protocol security review**: Validate agent card configurations for unauthorized tool definition injection. This translates to:
1. Enumerate all agents registered in A2A discovery (part of A2.4 registry)
2. Review agent cards for accuracy — capability claims should match observed behavior
3. Verify identity claims against the issuing identity provider

---

## 5. Vendor Assessment Framework for Agent Protocols

Organizations procuring or deploying agent coordination protocols should apply the same vendor security assessment depth used for SaaS vendors and critical libraries. A minimum protocol security assessment should cover:

### 5.1 Identity and Authentication
- How are agent identities established? (Self-asserted vs. cryptographically verified vs. DID/VC)
- Are identity claims validated at connection time, delegation time, and per-message?
- What happens when an agent's identity cannot be verified — fail open or fail closed?

### 5.2 Authorization and Delegation
- Does the protocol support scoped delegation (mandates)? Or is delegation all-or-nothing?
- Can a delegating agent revoke a delegation mid-task?
- What audit trail exists for all delegations?

### 5.3 Integrity of Protocol Artifacts
- Are tool descriptors, agent cards, and capability advertisements signed?
- Are protocol updates distributed via a signed channel?
- What is the process for reporting and patching security vulnerabilities in the protocol implementation?

### 5.4 Logging and Observability
- Does the protocol produce structured logs consumable by standard SIEM?
- Are protocol-layer events (connection, delegation, capability negotiation, tool invocation) logged with sufficient detail for incident forensics?
- Is there a documented correlation model between protocol events and application-layer agent behavior?

### 5.5 Blast Radius Assessment
- How many agents connect to this protocol stack?
- What is the maximum impact if the protocol's discovery service, identity provider, or central registry is compromised?
- Is there a migration path if a critical protocol vulnerability is discovered?

---

## 6. References

- NeighborJack vulnerability class (MCP servers binding to all interfaces) — production red-team findings.
- MITRE ATLAS (October 2025) — AI Agent Tools and Exfiltration via Agent Tool Invocation techniques.
- OWASP AIVSS v0.8, Risk #8 (Agent Supply Chain and Dependency Risk, 9.7/10).
- Google A2A protocol specification and security model analysis.
- CSA Agentic Control Plane framework — protocol assessment guidance.
- NEXUS-A2A protocol specification and SAFE2 compliance scoring.
- AI SAFE2 v3.0 Framework, Sections CP.4, CP.5, A2.3, P2.T3.10 modification.

---

*This research note is part of the AI SAFE2 v3.0 research foundation series. Cyber Strategy Institute, 2026.*
