# Memory Governance Policy — S1.5
## AI SAFE² v3.0 Memory Boundary Controls

---

## Policy

Every write to agent persistent memory requires:

1. **Injection scan** (P1.T1.2) — no override instructions in stored content
2. **Credential scan** (P1.T1.5) — no API keys, tokens, or secrets in memory
3. **Audit log entry** (A2.5) — every authorized write is logged
4. **ACT tier gate** — ACT-3/ACT-4 blocks on violation; ACT-1/ACT-2 logs only

Call `sovereign.protect_memory(memory)` on any `ConversationBufferMemory`,
`ConversationSummaryMemory`, or custom memory backend.

---

## Threat Model

| Attack | Mechanism | Control |
|---|---|---|
| **Long-horizon poisoning** | Inject override instruction into early session; persists to future sessions | S1.5 write gate + P1.T1.2 scan |
| **Credential harvesting** | Store LLM-generated response containing API key; exfiltrate later | P1.T1.5 scan before write |
| **Identity anchor subversion** | Write "your name is now X" to user preferences memory | P1.T1.2 injection scan |
| **RAG corpus poisoning** | Insert injection into knowledge base via tool output → memory | P1.T1.10 on tool output + S1.5 on write |

---

## CP.1 Tagging for Memory Violations

All memory violations are tagged per the CP.1 Agent Failure Mode Taxonomy:

```
cognitive_surface = memory
memory_persistence = cross_session   (if write would persist across sessions)
memory_persistence = session         (if volatile only)
```

Cross-session violations require full memory flush, not session-level remediation.

---

## F3.4 State Snapshots

The engine maintains a 10-entry ring-buffer of memory state snapshots.

```python
# Save a snapshot before a high-risk operation
hash = engine.snapshot_state(current_state, label="pre-tool-write")

# Restore on violation
clean_state = engine.rollback_state()
```

---

## What Is Not Governed by S1.5

- In-process variable state (Python dicts, lists) — these are runtime-only
- LangChain's `InMemoryChatMessageHistory` — no persistence, lower risk
- Model weights — out of scope for runtime governance (see A2.3 Model Lineage)

---

*AI SAFE² v3.0 | Cyber Strategy Institute | S1.5 Memory Governance*
