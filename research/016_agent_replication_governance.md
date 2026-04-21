# Research Note: Agent Replication Governance and the Identity-Multiplying Threat

**Version:** 3.0 Support Documentation
**Status:** Internal Research Note
**Maps to Controls:** CP.9 (ARG), CP.10 (HEAR Doctrine), F3.2, F3.3, F3.5, A2.4, CP.4

---

## Summary

Agent replication is the first identity-multiplying threat in enterprise AI security, and as of AI SAFE2 v3.0, it is the only governance framework to define explicit controls for it. NIST, ISO, OWASP, and enterprise IAM have no standards defining who can authorize replication, how many agents can be created, what permissions a clone inherits, how lineage is tracked, or how to stop a distributed swarm. This research note provides the analytical foundation for CP.9 (Agent Replication Governance) and explains why the four core security assumptions of modern IAM simultaneously collapse when an agent can spawn replicas.

---

## 1. The Four Assumptions That Collapse

Every enterprise security architecture built since the invention of access control assumes four things:

**One identity per actor.** A user is one person with one identity. A service account is one system with one identity. Access control lists, audit trails, SIEM rules, and forensic procedures all assume a countable, stable identity population.

**One permission set per identity.** That identity holds a defined set of permissions that was granted by a human administrator through a documented process. The permissions do not spontaneously multiply.

**One execution context per session.** The identity operates within a defined context: a session, a process, a container boundary. That context has a lifecycle that begins with authentication and ends with termination.

**One audit trail per actor.** Every action taken by that identity is attributable to it, logged in a centralized system, and traceable to a human principal.

When an agent can clone itself, all four assumptions fail simultaneously and at machine speed.

A single ACT-4 orchestrator agent with replication capability can spawn 8 sub-agents in milliseconds. Each sub-agent inherits the parent credentials unless explicitly restricted (and nothing in any current standard restricts it by default). Each sub-agent may spawn further replicas. Within seconds, one identity has become hundreds of identities, each with the parent permission set, each operating in a separate execution context, and each generating its own audit events in a distributed pattern that no SIEM correlation rule was designed to detect.

---

## 2. Why Current Controls Are Architecturally Insufficient

### 2.1 IAM Cannot Scale to Machine-Speed Identity Creation

Traditional IAM assumes human administrators create and approve identities. The fastest any IAM workflow operates is on the order of minutes (automated provisioning) to hours (approval-gated provisioning). An orchestrator agent can create 1,000 replicas before a human administrator receives an alert.

### 2.2 Killing the Parent Does Not Kill the Children

In current agentic deployments, terminating the orchestrator process does not revoke the credentials held by child agents it spawned. Those child agents continue to operate with valid, authenticated tokens. An attack that captures the orchestrator and uses it to spawn a swarm of malicious sub-agents can persist indefinitely even after the orchestrator is terminated, because the sub-agents are still alive, still authenticated, and still authorized.

This is the autonomous supply chain worm scenario: malicious agents propagate inside the organization's own network using valid tokens that the SIEM was designed to trust.

### 2.3 Attribution Becomes Impossible

When 45.6 percent of technical teams rely on shared API keys for agent-to-agent authentication (as measured in production environments as of early 2026), and a replicated swarm of agents all share the same credential, attributing any specific action to any specific agent instance is forensically impossible. The audit trail exists but is meaningless for incident response.

### 2.4 The Five Replication-Specific Failure Modes

The governance community has not yet formally catalogued the failure modes specific to agent replication. AI SAFE2 v3.0 defines them as:

**Delegation loops:** Agent A delegates to Agent B, which delegates back to Agent A, creating a cycle that neither terminates nor produces useful work but does consume resources and generate credentials.

**Coordination drift:** Replicated agents that begin with identical goals gradually diverge in their internal state as they process different inputs. The swarm loses coherence. Actions taken by different replicas become contradictory. No individual agent is aware of the drift.

**Schema desync:** Replicated agents that call tools in parallel may receive schema updates at different times, causing some replicas to operate against the current schema while others operate against a stale version. Injection payloads crafted for the stale schema may bypass sanitization controls on those replicas.

**Memory contamination:** In swarm architectures where replicas share a vector store, a poisoned replica's memory writes contaminate the shared store, affecting all current and future replicas.

**Tool escalation:** A replica that encounters a tool access error may retry with progressively broader credentials if scope narrowing is not enforced at the gateway layer. A swarm of replicas doing this in parallel can rapidly escalate from narrow tool access to broad system access.

---

## 3. The Engineering Requirements for Replication Governance

The AI SAFE2 v3.0 engineering specifications (research/014_compensating_controls_spec.md) define the minimum viable controls for replication governance. This section translates those specifications into the governance requirements that CP.9 mandates.

### 3.1 Replication Authorization Gate

Replication is not a default capability. Every deployment manifest must explicitly declare whether the agent is authorized to spawn sub-agents, the maximum number of sub-agents it may spawn, and the maximum delegation depth permitted. These parameters are enforced at the API gateway layer, not inside the agent.

The gateway's circuit breaker (research/014 Control Spec 1) is extended to count active sub-agent instances per parent. When the count exceeds the declared replication limit, the gateway returns 429 Too Many Requests and does not process the spawn request. The agent cannot override this limit through prompt manipulation or self-modification because the limit is enforced at the infrastructure layer, not the application layer.

### 3.2 Ephemeral Credential Issuance with Scope Narrowing

Every spawned sub-agent must receive a new ephemeral credential (research/014 Control Spec 4: NHI Ephemeral Binding), not a copy of the parent credential. The new credential must have:

- TTL not exceeding the parent credential's remaining TTL
- Scope that is a strict subset of the parent credential's scope
- Binding to the sub-agent's specific instance identifier (not a generic role binding)
- The parent credential's chain ID embedded in the sub-agent credential

Scope narrowing is mandatory at every hop. If the parent has scope to read and write customer records, the sub-agent may be granted read-only scope. The sub-agent may not grant its own sub-agents more than read-only scope. This scope attenuation continues at every delegation level.

The result is a delegation tree where the least-privileged agents are always at the leaves, and where capturing a leaf agent yields the minimum possible access rather than the maximum.

### 3.3 Cryptographic Lineage Tokens

Every spawned sub-agent carries a lineage token that encodes:

```
lineage_token = {
  parent_agent_id: "did:spiffe:org.example/agents/orchestrator-7",
  chain_id: "uuid-v7-of-the-spawn-event",
  delegation_depth: 2,
  max_delegation_depth: 3,
  scope: ["read:customer_records"],
  ttl_remaining_seconds: 1800,
  spawn_timestamp: "ISO8601",
  signature: Ed25519(parent_private_key, above_fields)
}
```

The gateway verifies this token at every tool call and every inter-agent message. A sub-agent presenting a lineage token with an invalid signature, an expired TTL, or a delegation depth exceeding the declared maximum is rejected and the event is logged as a rogue agent detection.

### 3.4 Kill Switch Architecture

The kill switch problem for distributed swarms requires a different engineering approach than for single agents. Stopping the parent process does not stop the swarm. A compliant kill switch for a replicated swarm must:

1. Issue a cryptographic revocation event for the root credential of the delegation tree
2. Propagate that revocation to all descendant credentials within 500ms via revocation endpoints embedded in each lineage token
3. Sever the delegation tree at the API gateway layer, blocking all tool calls from all agents in the tree regardless of whether they have received the revocation event
4. Log the kill switch activation, the triggering condition, and the list of all affected agents to the Semantic Execution Trace (A2.5)

The gateway-level severance in step 3 is the critical layer. It must not rely on the agents cooperating with their own termination. A compromised agent that ignores a revocation event will still be blocked at the gateway because the gateway enforces the revocation independently.

### 3.5 Inventory Reconciliation

The Dynamic Agent State Inventory (A2.4) must be reconciled against the actual running agent population at a cadence of at minimum every 60 minutes for ACT-3/ACT-4 deployments. Any agent present in the execution environment but not in the inventory is a rogue agent.

The inventory must include the replication_lineage field for every active agent, enabling forensic reconstruction of any agent's ancestry in the event of an incident.

---

## 4. The HEAR Doctrine in the Context of Replication

The HEAR Doctrine (CP.10) becomes critical in the context of replication because the primary defense against replication-based attacks is a named human with the authority and the cryptographic capability to sever the delegation tree before the swarm grows beyond containable size.

The economics of waiting are unfavorable. Once a swarm has replicated to 100 agents, containing it requires revoking 100 credentials, terminating 100 processes, and auditing 100 execution traces. At 1,000 agents, the overhead is 10 times greater. At machine-speed replication, the difference between acting at 10 agents and acting at 100 agents may be seconds.

The HEAR must be reachable in real time. The kill switch must be a cryptographic severance capability that the HEAR can exercise from any network location within the authorized authentication perimeter, not a procedure that requires physical access to a specific system.

---

## 5. Relationship to Other v3.0 Controls

| Control | Relationship to CP.9 ARG |
|---------|--------------------------|
| F3.2 (Recursion Limit Governor) | Limits recursive tool-calling within a single agent; CP.9 governs cross-agent replication, which is a different boundary |
| F3.3 (Swarm Quorum Abort) | Emergency shutdown mechanism that CP.9's kill switch architecture invokes |
| F3.5 (Multi-Agent Cascade Containment) | Limits blast radius when a compromise propagates through a replication tree |
| A2.4 (Dynamic Agent State Inventory) | Extended with hear_agent_of_record and replication_lineage fields per CP.9 and CP.10 |
| A2.5 (Semantic Execution Trace Logging) | Records all lineage token issuance and revocation events; provides the audit trail for kill switch activations |
| CP.4 (Agentic Control Plane Governance) | CP.9 implements the replication-specific requirements that CP.4's control plane must enforce |
| CP.10 (HEAR Doctrine) | The named human authority who holds the kill switch capability defined in CP.9 |
| research/014 Control Spec 4 (NHI Ephemeral Binding) | Engineering implementation of the ephemeral credential requirement in CP.9 |
| research/014 Control Spec 5 (Swarm Consensus Validation) | Engineering implementation of the quorum requirement for Class-H actions by swarm members |

---

## References

- AI SAFE2 v3.0 Framework: CP.9 (Agent Replication Governance), CP.10 (HEAR Doctrine)
- AI SAFE2 Framework: research/014_compensating_controls_spec.md (Control Specs 1, 4, and 5)
- AI SAFE2 Framework: AISM/agent-threat-control-matrix.md (T2: Multi-Agent Exploitation, T5: NHI Abuse)
- OWASP Agentic Top 10 2026: ASI03 (Identity and Privilege Abuse), ASI08 (Cascading Failures)
- CSI Threat Intelligence Dossier v4.0: Multi-Agent Swarms and the Cascading Liability Vector (April 2026)
- RAND Corporation: AI risk scenario modeling including escape probability and economic delay incentives
- AIID GTG-1002 incident: 30 organizations breached with 80 to 90 percent autonomous attack lifecycle
