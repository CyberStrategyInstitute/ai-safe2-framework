# AI SAFE² v3.1: Protocol-Independent Governance, Three Enforcement Planes, and Agent-Ready Distribution

<p align="center">
  <img alt="AI SAFE2 v3.1" src="https://img.shields.io/badge/AI%20SAFE%C2%B2-v3.1.0-F6921E?style=for-the-badge">
  <img alt="Framework" src="https://img.shields.io/badge/Framework-161%20Controls-820F1A?style=for-the-badge">
  <img alt="MCP Profile" src="https://img.shields.io/badge/CP.5.MCP-19%20Controls-F6921E?style=for-the-badge">
  <img alt="Agent Ready" src="https://img.shields.io/badge/Agent%20Discovery-Validated-808080?style=for-the-badge">
</p>

**Cyber Strategy Institute | August 2026**

AI SAFE² v3.1 is the release where protocol governance stops depending on protocol-owned state.

The trigger was MCP `2026-07-28`. MCP moved to a stateless core and removed constructs that earlier AI SAFE² MCP controls had used as governance anchors. The result exposed a framework design defect: if a protocol owns the thing a control binds to, the protocol can remove that thing.

v3.1 fixes the defect at the architecture level, extends enforcement across the agent-to-tool plane, adds six MCP controls, formalizes a common persistence vocabulary, strengthens NEXUS compatibility behavior, expands scanner coverage, upgrades the Challenge Lab, standardizes the entire repository experience, and adds a deterministic machine entry point so agents and compliance bots can consume the framework without scraping prose.

The normative rule is now:

> **A CP.5 profile MUST NOT bind a control to a construct owned by the protocol it profiles.**

AI SAFE² v3.1 binds governance to framework-owned constructs: verified principals, capability grants, provenance baselines, delegation chains, governed state handles, policy decisions, and evidence.

---

## Fast Action

| If you want to... | Go here |
|:---|:---|
| **Understand v3.1 in 5 minutes** | [v3.1 Release Overview](guides/v3.1-release-overview.md) |
| **Start from the framework** | [AI SAFE² v3.1 README](README.md) |
| **Implement MCP controls** | [CP.5.MCP Security Profile](00-cross-pillar/cp5_mcp_server_security.md) |
| **Use the machine-readable MCP profile** | [MCP Profile JSON](skills/mcp/data/mcp-profile-v3.1.json) |
| **Use the 161-control core dataset** | [Core Control JSON](skills/mcp/data/ai-safe2-controls-v3.0.json) |
| **Integrate from an AI agent or bot** | [AGENTS.md](AGENTS.md) and [ai-safe2.manifest.json](ai-safe2.manifest.json) |
| **Assess code or deployments** | [Scanner](scanner/) |
| **Secure MCP implementations** | [MCP Security Toolkit](examples/mcp-security-toolkit/) |
| **Use CSI's reference implementation** | [NEXUS](NEXUS/) |
| **Review maturity and threat mapping** | [AISM](AISM/) |
| **See governed implementation patterns** | [Examples](examples/) |
| **Read the evidence base** | [Research](research/) |
| **Challenge or falsify the framework** | [Challenge Lab](challenges/) |
| **Explore controls interactively** | [AI SAFE² Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/) |
| **Review repository UX rules** | [Repository UX Standard](docs/REPOSITORY-UX-STANDARD.md) |
| **See the release history** | [GitHub Releases](https://github.com/CyberStrategyInstitute/ai-safe2-framework/releases) |

---

## What changed

### 1. MCP governance was re-anchored

MCP `2026-07-28` removed the protocol assumptions that exposed the flaw in our earlier CP.5.MCP design. Five existing controls were re-anchored from session concepts to verified principals and framework-owned state.

The MCP profile now contains **19 controls**, MCP-1 through MCP-19. The AI SAFE² framework total remains **161 controls**.

| Change | v3.1 result |
|:---|:---|
| **Re-anchored controls** | MCP-4, MCP-7, MCP-8, MCP-11, MCP-13 bind to framework-owned governance state rather than protocol session state |
| **MCP-14** | Extension Capability Negotiation |
| **MCP-15** | Header and Body Assertion Integrity |
| **MCP-16** | State Handle Binding and Lifecycle |
| **MCP-17** | MRTR Round-Trip Integrity and Replay Resistance |
| **MCP-18** | Catalog Cache Integrity and Provenance Revalidation |
| **MCP-19** | Authorization Chain Integrity, intended-resource/audience binding, and SSRF boundaries |
| **Primary binding** | MCP `2026-07-28` |
| **Legacy compatibility** | MCP `2025-11-25` for a twelve-month migration window |

`server/discover` is optional under the primary MCP binding. AI SAFE² does not require it and the scanner does not treat its absence as a failure.

`Mcp-Session-Id`, where encountered in the legacy binding, is a principal-scoped state handle. It is not identity and is not the authorization boundary.

### 2. Three enforcement planes are now explicit

AI SAFE² v3.1 treats agentic governance as a three-plane problem:

| Plane | Traffic | Primary governance problem |
|:---|:---|:---|
| **North-south** | Agent to model provider | Content, policy, spend, provider access |
| **East-west** | Agent to agent | Identity, delegation, lineage, authority |
| **Agent-to-tool** | Agent to MCP server or tool | Tool authorization, provenance, catalog trust, returned-content risk |

A successful control or challenge result on one plane does not automatically establish coverage on another.

### 3. Persistence vocabulary is protocol-independent

New evidence and integrations use:

- `request`
- `handle_scoped`
- `durable`
- `swarm_shared`

Legacy NEXUS values remain accepted as compatibility aliases:

- `SESSION` -> `request`
- `CROSS_SESSION` -> `handle_scoped`
- `PERMANENT` -> `durable`

This removes protocol session language from the governance boundary while preserving migration compatibility.

### 4. NEXUS is clearly positioned as the CSI reference implementation

**AI SAFE² is the governance and requirements standard. NEXUS is CSI's first-party reference implementation.**

Organizations may use NEXUS or another implementation that demonstrably satisfies the applicable AI SAFE² controls and evidence requirements.

NEXUS remains **v0.3** under the AI SAFE² v3.1 framework release. Gateway remains **v3.0** until a separately tested Gateway component release changes it.

The NEXUS MCP adapter is fail-closed scaffolding. **Status: not production-ready.** Unimplemented enforcement methods raise rather than silently allowing traffic.

### 5. Scanner coverage expanded

The v3.1 registry contains **64 scanner rules**:

- 52 pre-existing scanner rules
- 12 new grouped CP.5.MCP v3.1 rules

MCP-19 findings remain advisory where static analysis cannot prove deployment-specific intended-resource or audience binding.

### 6. MCP-19 now has an explicit conformance boundary

Opaque bearer-token possession does not prove audience or intended-resource validation.

A deployment must not claim MCP-19 audience/resource conformance unless it can evidence intended-resource, audience, or equivalent binding before protected dispatch.

This is intentionally stricter than "the token was accepted."

### 7. Challenge Lab is now scoped by enforcement plane

Challenge 001 and the broader Challenge Lab now separate:

- challenge maturity;
- framework/profile conformance;
- the enforcement plane actually exercised;
- evidence required to support a claim.

The v3.1 MCP cases include header/body desynchronization, catalog/schema drift, replay, audience/resource confusion, endpoint impersonation, SSRF, and legacy state-handle misuse.

[Open the Challenge Lab](challenges/)

### 8. The repository now has one human experience

The v3.1 consistency sweep standardizes the root framework, Pillar 1 through 5, Cross-Pillar Governance, AISM, NEXUS, Scanner, Gateway, Skills, MCP, Dashboard, Examples, Research, Challenge Lab, and UAS surfaces.

Repository color semantics are explicit:

- ![Release](https://img.shields.io/badge/Release-F6921E-F6921E) **CSI Orange `#F6921E`** for current release/version context
- ![Framework](https://img.shields.io/badge/Framework-820F1A-820F1A) **CSI Maroon `#820F1A`** for framework/module identity
- ![Neutral](https://img.shields.io/badge/Neutral-808080-808080) **Gray `#808080`** for neutral/status context
- red/amber/yellow remain reserved for risk and severity
- green remains reserved for verified/pass states

All 18 direct example README surfaces and all 24 numbered research notes now use the common v3.1 navigation and context shell while preserving legitimate historical provenance.

### 9. Agents and bots now have a first-class entry point

AI SAFE² v3.1 no longer requires an automated consumer to infer the repository structure from prose.

Start with:

1. [AGENTS.md](AGENTS.md)
2. [ai-safe2.manifest.json](ai-safe2.manifest.json)
3. [161-control core JSON](skills/mcp/data/ai-safe2-controls-v3.0.json)
4. [19-control MCP v3.1 profile JSON](skills/mcp/data/mcp-profile-v3.1.json)

The manifest exposes framework version, component versions, normative paths, control counts, enforcement planes, persistence vocabulary, conformance boundaries, implementation status, and machine-readable datasets.

A dedicated **Agent Discovery and Manifest Integrity** CI gate verifies those claims against the repository.

---

## What did not change

v3.1 is not a renumbering exercise.

- The **161-control core remains unchanged**.
- CP.1 through CP.10 remain the Cross-Pillar Governance layer.
- CP.11 UAS remains a compliance overlay rather than 27 new core controls.
- Historical v3.0 references remain where they accurately describe when a capability, research result, example, or component was introduced.
- NEXUS remains v0.3.
- Gateway remains v3.0.

The stable core dataset retains the filename `ai-safe2-controls-v3.0.json` because that dataset represents the unchanged 161-control taxonomy introduced in v3.0. The v3.1 MCP changes are maintained as a separate profile overlay.

---

## Release validation

The v3.1 release candidate is exercised by dedicated repository gates covering:

- repository UX and navigation consistency;
- examples and research index integrity;
- agent discovery and manifest integrity;
- scanner v3.1 invariants;
- NEXUS persistence compatibility;
- MCP profile/dashboard parity and 161/19 control-count invariants;
- NEXUS tests on Python 3.10, 3.11, and 3.12;
- release-critical Python correctness;
- NEXUS schema validation;
- NEXUS reference-example smoke tests;
- NEXUS v0.3 implementation/compliance checks;
- documentation validation;
- AI SAFE² Skill Trust Gate validation.

The release is designed to fail on incorrect claims and broken paths, not only on syntax.

---

## Read next

### Framework and governance

- [AI SAFE² v3.1 Framework](README.md)
- [Cross-Pillar Governance](00-cross-pillar/)
- [CP.5.MCP Security Profile](00-cross-pillar/cp5_mcp_server_security.md)
- [AISM](AISM/)
- [AISM Agent Threat and Control Matrix](AISM/agent-threat-control-matrix.md)
- [v3.1 Release Overview](guides/v3.1-release-overview.md)

### Implementation

- [NEXUS](NEXUS/)
- [Scanner](scanner/)
- [MCP Security Toolkit](examples/mcp-security-toolkit/)
- [AI SAFE² MCP Server](skills/mcp/)
- [Sovereign Runtime Examples](examples/)
- [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

### Evidence and validation

- [Research Index](research/)
- [Research 023: MCP Server Security Profile](research/023_mcp-server-security-profile.md)
- [Research 024: MCP Consumer Protection](research/024_mcp_consumer_protection.md)
- [Challenge Lab](challenges/)
- [Challenge 001](challenges/001-anthropic-multi-agent-turf-war/)

### Machine consumption

- [AGENTS.md](AGENTS.md)
- [AI SAFE² Manifest](ai-safe2.manifest.json)
- [Core Controls JSON](skills/mcp/data/ai-safe2-controls-v3.0.json)
- [MCP v3.1 Profile JSON](skills/mcp/data/mcp-profile-v3.1.json)

### External

- [AI SAFE²](https://cyberstrategyinstitute.com/ai-safe2/)
- [NEXUS](https://cyberstrategyinstitute.com/nexus/)
- [Implementation Toolkit](https://secure.cyberstrategyinstitute.com/ai-safe-implementation-toolkit/)
- [MCP 2026-07-28 Specification](https://modelcontextprotocol.io/specification/2026-07-28)
- [MCP 2026-07-28 Release Announcement](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)

---

## The operating principle

**Policy defines intent. Engineering must enforce reality.**

If governance is not enforced at runtime, it is not governance.

AI SAFE² v3.1 makes that contract more durable by making the governance boundary ours, not the protocol's.

---

Framework content CC-BY-SA 4.0. Code MIT. NEXUS Apache 2.0.

*Cyber Strategy Institute*
