<!-- AI-SAFE2-UX:START -->
[![AI SAFE² v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface: Research](https://img.shields.io/badge/Surface-Research-820F1A?style=flat-square)](./README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE² v3.1. This research note preserves its original publication date, evidence, and historical framework references. Use current v3.1 normative control and profile documents for implementation or conformance decisions.
<!-- AI-SAFE2-UX:END -->

# Research Note: Runtime Isolation & The "Glass Box"
**ID:** RN-2025-006 | **Related Control:** [P1.T2.1], [P1.T2.1_ADV] | **Status:** Verified

## 🚨 The Threat Vector
**Container Breakouts:** Standard Docker containers share the host kernel. If an Agent has code-execution capabilities (e.g., Python REPL), a kernel exploit allows it to escape the container and compromise the host infrastructure.
*   **Research Basis:** *NIST Container Security Guide (SP 800-190)*.

## 🛡️ The AI SAFE² Solution
For Tier 3 (Agentic) systems, standard containerization is insufficient. We mandate **User-Space Kernels**.

### 1. gVisor / Firecracker Enforcement [P1.T2.1]
All agents capable of writing code must run in **gVisor (runsc)** or **AWS Firecracker** microVMs. This provides a distinct kernel boundary, mitigating escape vulnerabilities.

### 2. Ephemeral Runtimes
Agents should not have persistent filesystems. Containers must be destroyed and rebuilt after every task execution to prevent malware persistence.

## 📚 References
*   [Google gVisor Documentation](https://gvisor.dev/)
*   [AWS Firecracker MicroVMs](https://firecracker-microvm.github.io/)

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Research navigation

[Previous research note](./005_memory_injection_minja.md) | [Research Index](./README.md) | [Next research note](./007_jit_privilege_access.md)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [NEXUS](../NEXUS/) | [Challenge Lab](../challenges/)

*AI SAFE² v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
