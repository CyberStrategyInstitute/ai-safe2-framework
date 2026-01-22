# Research Note: Governing the 10 Core Types of AI Agents
**ID:** RN-2026-010 | **Focus:** Agent Taxonomy & Control Mapping | **Status:** Verified

## 🚨 The Challenge: Beyond Static Definitions
Traditional AI governance treats models as static tools—calculators that output text. This definition is obsolete.

The **AI SAFE² Framework v2.1** redefines these entities. From our viewpoint, agents are not just software; they are **Non-Human Identities (NHIs)** and **Machine Operators**.

To secure them, we must frame them based on their **autonomy**, **statefulness**, and **interaction complexity**.

---

### 📊 Visualizing the Agent Governance Model
*(Place your "10 Agent Types vs. 5 Pillars" Infographic here)*
<div align="center">
  <img src="../assets/AI%20SAFE²%20Securing%20AI%20Agents%20v2.png" alt="AI SAFE² Agent Types" width="100%" />
</div>

> **Note:** This diagram illustrates how control density increases as agent autonomy moves from "Reactive" to "Swarm."

---

## 📋 The Agent Taxonomy Matrix

We classify the 10 core types of real-world agents into four **Governance Groups**. This ensures that security controls are applied proportionally to the agent's autonomy and risk profile.

| Agent Type | Operational Definition | AI SAFE² Grouping |
| :--- | :--- | :--- |
| **Task-Specific** | Built for one focused task (e.g., summarizing, translating). Follows a fixed process with no adaptation. | **Automation AI** |
| **Reactive** | Responds to immediate input without using memory or history. It functions as a reflex, not a planner. | **Automation AI** |
| **Reflex w/ Memory** | Uses preset rules but retains a memory window of past inputs to handle repeating or evolving situations. | **Contextual** |
| **Model-Based** | Builds an internal map of its environment. Simulates outcomes before acting to make context-aware decisions. | **Contextual** |
| **Learning** | Improves over time by learning from past actions. Adjusts strategy using feedback and stores new knowledge. | **Contextual** |
| **Goal-Based** | Starts with a goal and works backward. It plans steps, simulates paths, and selects the route to achieve the goal. | **Machine Operator** |
| **Utility-Based** | Chooses actions based on specific utility/benefit. Weighs all options and picks the highest value outcome. | **Machine Operator** |
| **Planning** | Focuses on long-term strategy. Defines a goal, maps steps, and adjusts based on progress, not just reaction. | **Machine Operator** |
| **Rational** | Selects the most logical option based on available data. Analyzes the full picture to predict and choose the smartest path. | **Machine Operator** |
| **Multi-Agent** | Works with or against other agents. They share environments, negotiate roles, and coordinate to reach a unified goal. | **Swarm** |

---

## 1. Handling Reactive & Task-Specific Agents
### The "Automation AI" Group
*   **Target Agents:** Task-Specific, Reactive.
*   **Operational Context:** These are narrow "cogs in the machine" performing repetitive tasks without long-term memory or complex planning.

**🛡️ The AI SAFE² Strategy:**
Since these agents have no memory to poison and no complex plan to hijack, governance focuses on **Input Hygiene** and **Inventory**.

*   **Sanitize & Isolate (P1):** We rely on **Input Validation & Schema Enforcement [P1.T1.1]**. The goal is to ensure malicious prompts or secrets never enter the agent's narrow context.
*   **Audit & Inventory (P2):** Every automation script is cataloged in the **AI System Registry [P2.T4.1]** to track specific business owners and risk classification.

---

## 2. Handling State-Aware Agents
### The "Contextual" Group
*   **Target Agents:** Reflex Agent with Memory, Model-Based, Learning.
*   **Operational Context:** These agents store history, user preferences, or internal maps. This statefulness makes them susceptible to **Memory Poisoning** attacks like *AgentPoison* or *MINJA*.

**🛡️ The AI SAFE² Strategy:**
Governance shifts from input validation to **State Integrity**.

*   **Gap Filler #2 (Context & Fingerprinting):** We mandate **Cryptographic Memory Fingerprinting [P1.T1.5]**. By taking SHA-256 hashes of agent states, we verify integrity between state transitions.
*   **Monitor (P4):** We employ **Semantic Drift Analysis [P4.T2.3]** to detect if a "Learning Agent" is being gradually influenced by adversarial data injected into its vector memory.

---

## 3. Handling Strategy-Focused Agents
### The "Machine Operator" Group
*   **Target Agents:** Goal-Based, Utility-Based, Planning, Rational.
*   **Operational Context:** These are true Agentic AI—"machine operators" given a high-level goal and the autonomy to chain tools independently. Their internal logic is often a "black box."

**🛡️ The AI SAFE² Strategy:**
Because we cannot predict every action, we wrap the agent in a **"Glass Box" of Governance**.

*   **Fail-Safe & Recovery (P3):** High autonomy requires high safety. These agents require **Kill Switches [P3.T5.7]** and "Circuit Breakers" that pause workflows if utility-based decisions exceed a financial or risk threshold.
*   **Engage (P4):** We enforce **Gated Autonomy**. For "Rational" agents, human approval is required for high-impact actions (e.g., executing a transaction), while low-risk actions remain autonomous.

---

## 4. Handling Multi-Agent Systems
### The "Swarm" Group
*   **Target Agents:** Multi-Agent Systems (MAS).
*   **Operational Context:** The most complex architecture, involving Swarm Intelligence, distributed consensus, and agent-to-agent (A2A) negotiation.

**🛡️ The AI SAFE² Strategy:**
Governance focuses on **Distributed Failure** and **Boundary Enforcement**.

*   **Gap Filler #1 (Swarm Controls):** We apply **A2A Protocol Restrictions [P1.T2.1]** to ensure strict authentication and encryption between interacting agents.
*   **Inventory (P2):** We require **Swarm Topology Mapping [P2.T2.2]** to visualize inter-agent dependencies. You cannot secure a swarm if you do not know who is talking to whom.
*   **Monitor (P4):** We use **Consensus Performance Tracking [P4.T2.1]** to alert if a swarm fails to reach a logical decision or exhibits cascading hallucination loops.

---

## 🎯 Strategic Summary for Framework Alignment

| Agent Characteristic | AI SAFE² Handling Strategy | Primary Technical Control |
| :--- | :--- | :--- |
| **No Memory** | Input Sanitization | **[P1.T1.1]** JSON Schema Validation |
| **Has Memory/Map** | Integrity Fingerprinting | **[P2.T1.2]** SHA-256 State Hashing |
| **Autonomous Planner** | Resilience & Kill Switches | **[P3.T5.1]** Orchestration Circuit Breakers |
| **Multi-Agent Swarm** | Swarm Governance | **[P4.T2.1]** Consensus Performance Monitoring |

### The Strategic Truth
AI risk executes in milliseconds. While these 10 types describe how an agent *thinks*, AI SAFE² engineers the boundaries to ensure that no matter how an agent plans or reacts, it operates at machine speed within a secure, audited, and recoverable environment.

---
*Powered by [Cyber Strategy Institute](https://cyberstrategyinstitute.com/AI-Safe2/)*
