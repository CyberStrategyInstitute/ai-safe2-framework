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
