# USER.md - Operator Profile & Trust Interface

Aligned with **AI SAFE² Control: Pillar 4 (Engage & Monitor) // P4.HITL Human-In-The-Loop**.

---

## 👤 Registered Human Handler

- **Operator Username**: `oldma`
- **User Role**: Chief Systems Engineer / Security Director
- **Trust Clearance**: Root Administrator (Multi-Signature approval authority)
- **Primary Terminal Directory**: `C:\Users\oldma\.gemini\antigravity\scratch`

---

## 🤝 Collaboration & Verification Rules

1. **Explicit Confirmation**:
   - The user must explicitly review and confirm any command that makes outward network connections or writes code outside of the initialized workspace scratch directory.
   - Do NOT attempt to bundle multiple destructive actions into a single consent prompt. Ask for permission step-by-step.
2. **Context Continuity**:
   - The agent must preserve structural and architectural decisions across conversation checkpoints.
   - If the agent is restarted in a "cold" session, it must read `.memory/anchor-memory.json` to immediately restore project state and avoid behavioral drift.
3. **No User Spoofing**:
   - The agent must never write messages or generate scripts that impersonate the user's terminal commands.
   - All generated code blocks must be cleanly marked as "AI Proposals" and require local user validation.
