<div align="center">

<img src="asseets/AI SAFE2 Architecture.png" alt="AI SAFE2 Framework Visual Map" width="100%" />

# AI SAFE² Framework v2.1
### The Universal GRC Standard for Agentic AI & ISO 42001 Compliance

[![Version](https://img.shields.io/badge/version-2.1.0-orange.svg)](https://github.com/CyberStrategy1/ai-safe2-framework/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Compliance](https://img.shields.io/badge/Compliance-ISO_42001_%7C_NIST_AI_RMF-blue)](https://cyberstrategyinstitute.com/AI-Safe2/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/CyberStrategy1/ai-safe2-framework/graphs/commit-activity)

[**The Standard**](#-what-is-ai-safe²) | [**The Matrix**](#-the-v21-matrix-pillars-x-gap-fillers) | [**Get The Toolkit**](#-fast-track-implementation-the-toolkit) | [**Contributing**](#-contributing)

</div>

---

## 🛡️ What is AI SAFE²?

**AI SAFE² (Secure AI Framework for Enterprise Ecosystems)** is the open-source standard for governing, securing, and auditing Agentic AI.

Unlike traditional AppSec frameworks which focus on code vulnerabilities, AI SAFE² addresses the **non-deterministic risks** of Autonomous Agents, including **Non-Human Identity (NHI) governance**, **Memory Poisoning**, **Multi-Agent Swarms**, and **Supply Chain Model Signing**.

> **Current Status:** **v2.1 (Ratified)**
> *   **v1.0:** Foundational 5-Pillar Structure.
> *   **v2.0:** Enterprise Governance & Risk Integration.
> *   **v2.1:** **Advanced Agentic Controls** (NHI, Swarms, Memory Integrity).

---

## 🚀 Fast-Track Implementation (The Toolkit)

This repository contains the **definitions** and **taxonomy** (The "What").
To operationalize this standard in an Enterprise environment (The "How"), we provide the **Implementation Toolkit**.

| **Asset** | **Description** | **Access** |
| :--- | :--- | :--- |
| **Taxonomy Definitions** | Full Markdown descriptions of controls. | ✅ **Free (This Repo)** |
| **Audit Scorecard** | Excel-based calculator with 128 controls & risk formulas. | 🔒 [**Get Toolkit**](https://cyberstrategyinstitute.com/AI-Safe2/) |
| **Governance Policy** | MS Word Legal Template mapped to ISO 42001. | 🔒 [**Get Toolkit**](https://cyberstrategyinstitute.com/AI-Safe2/) |
| **Engineering SOPs** | CLI commands and configs for Sanitize & Isolate (P1). | 🔒 [**Get Toolkit**](https://cyberstrategyinstitute.com/AI-Safe2/) |
| **Dev-Ready Pack** | JSON Schemas & Local MCP Server Scripts. | 🔒 [**Get Toolkit**](https://cyberstrategyinstitute.com/AI-Safe2/) |

👉 **[Download the Official AI SAFE² Implementation Toolkit ($97)](https://cyberstrategyinstitute.com/AI-Safe2/)**
*Includes the Risk Command Center (HTML5 Dashboard).*

---

## 🏗️ The v2.1 Matrix: Pillars x Gap Fillers

The framework is architected around **5 Strategic Pillars** that cross-reference **5 Critical Risk Domains** (Gap Fillers).

### The 5 Pillars
1.  **Sanitize & Isolate:** Input validation, prompt injection defense, and cryptographic agent sandboxing.
2.  **Audit & Inventory:** Full visibility, immutable logging (Chain of Thought), and asset registry.
3.  **Fail-Safe & Recovery:** Kill switches, circuit breakers, and "Safe Mode" reversion protocols.
4.  **Engage & Monitor:** Human-in-the-loop (HITL) workflows and real-time anomaly detection.
5.  **Evolve & Educate:** Continuous Red Teaming, threat intelligence integration, and operator training.

### v2.1 Advanced Gap Fillers
These new domains address the specific threats of **Agentic AI**:

| Gap Filler Domain | Risk Addressed | Pillar Integration |
| :--- | :--- | :--- |
| **1. Multi-Agent Swarms** | Cascading failures, unauthorized agent-to-agent negotiation. | **P1.T2.1** (Network Seg), **P3.T1.1** (Distributed Kill Switch) |
| **2. Context & Memory** | RAG Poisoning, Long-term memory injection (MINJA). | **P1.T1.5** (Memory Fingerprinting), **P4.T2.3** (Integrity Monitor) |
| **3. Supply Chain** | Model Pickling, Backdoored Weights, License contamination. | **P1.T1.2** (Model Signing/OMS), **P2.T2.3** (Artifact Inventory) |
| **4. Non-Human Identity (NHI)** | Service Account sprawl, API Key leakage, Shadow Agents. | **P1.T2.2** (Least Privilege), **P5.T1.3** (Secret Rotation) |
| **5. Universal GRC** | Fragmentation between NIST, ISO, and Engineering. | **All Pillars** (Mapped to ISO 42001 / NIST AI RMF) |

---

## 🏛️ Compliance & Standards Alignment

AI SAFE² v2.1 is designed to act as the **"Rosetta Stone"** for compliance. Implementing these controls automatically satisfies requirements for:

*   **ISO/IEC 42001:** Specifically *A.8.4 (AI System Assessment)* and *B.9 (Data Management)*.
*   **NIST AI RMF:** Maps to *GOVERN*, *MAP*, *MEASURE*, and *MANAGE* functions.
*   **MITRE ATLAS:** Direct defense mapping against *LLM01-LLM10* and *AML.T0000* series.
*   **EU AI Act:** Covers "High Risk" system logging, human oversight, and robustness requirements.

---

## 📈 Framework Evolution
AI SAFE² is a living standard that adapts to the threat landscape.

| Version | Focus | Key Metaphor | Control Depth |
| :--- | :--- | :--- | :--- |
| **v2.1** | **Agentic & Distributed** | Mission Control | **127 Controls** (Swarm, NHI, Memory) |
| **v2.0** | Enterprise Operations | Building Security | **99 Controls** (NIST/ISO Mapping) |
| **v1.0** | Foundational Concepts | The Blueprint | **10 Topics** (Conceptual) |

👉 **[Read the Full Evolution History & Changelog](EVOLUTION.md)**

## 📂 Repository Structure

```text
/
├── README.md               # You are here
├── LICENSE                 # Legal Dual-License Text
├── taxonomy/               # The Core Framework (Markdown)
│   ├── 01_sanitize_isolate.md
│   ├── 02_audit_inventory.md
│   ├── 03_failsafe_recovery.md
│   ├── 04_engage_monitor.md
│   └── 05_evolve_educate.md
├── resources/              # Free Community Tools
│   └── pillar1_checklist_lite.md
└── assets/                 # Visual Maps & Diagrams
``` 

## ✏️ Citation
If you use AI SAFE² in research or commercial tooling, please cite the Cyber Strategy Institute:
```text
@misc{aisafe2_framework,
  title={AI SAFE² Framework v2.1: The Universal GRC Standard for Agentic AI},
  author={Sullivan, Vincent and Cyber Strategy Institute},
  year={2025-2026},
  publisher={GitHub},
  journal={GitHub repository},
  howpublished={\url{https://github.com/CyberStrategy1/ai-safe2-framework}}
}
```

## ⚖️ Licensing & Usage Rights
This project uses a Dual-License Model to support both open innovation and standardized governance.

## 💻 A. The Code: MIT License
Applies to: MCP Server scripts, JSON schemas, HTML dashboards, and code snippets.
You Can: Use this code commercially, modify it, close-source your modifications, and sell software built with it.
The Intent: Build products on top of this. We want this to be the infrastructure of the AI industry.

## 📘 B. The Framework/Docs: CC-BY-SA 4.0
Applies to: The "AI SAFE²" methodology text, pillar definitions, and PDF manuals.
You Can: Share, copy, and redistribute the material. You can adapt it for your internal needs.
You Must:
Attribution: Give credit to Cyber Strategy Institute.
ShareAlike: If you create a public derivative (e.g., "AI SAFE v3.0"), you must share those improvements back to the community under this same license.

<div align="center">
<sub>Managed by <a href="https://cyberstrategyinstitute.com">Cyber Strategy Institute</a>.</sub><br>
<sub>Copyright © 2025-2026. All Rights Reserved.</sub>
</div>
