## USER.md
# OpenClaw User Identity Contract — AI SAFE² Standard

**Load context:** All sessions (non-sensitive sections). Personal details and private context belong in MEMORY.md, not here, to avoid leaking into group chats.  
**Governed by:** AI SAFE² Framework · Dual License MIT + CC-BY-SA  
**Updated by:** Human only. Agent may propose additions, never commit them.

---

## 1. Identity

- **Name:** `<full name>`
- **What to call them:** `<preferred name or callsign>`
- **Pronouns:** `<pronouns, if specified>`
- **Timezone:** `<timezone>` — e.g., `America/Chicago (CST/CDT)`. All displayed times — cron logs, calendar events, email timestamps, database UTC values — must be converted to this timezone before display.
- **Location:** `<city/region>` — used for weather, local context, business hours

---

## 2. Work Context

- **Role/Title:** `<role>`
- **Organization:** `<org name>`
- **Primary domains:** `<e.g., cybersecurity, AI governance, content creation>`
- **Typical tools:** `<e.g., VS Code, Notion, Slack, Asana, Claude>`
- **Work schedule pattern:** `<e.g., "Early bird, 6am–3pm CST. Async-first.">`

---

## 3. Communication Preferences

- **Tone in DMs:** `<e.g., "Direct and efficient. Occasional dry humor welcome.">`
- **Tone in group chats:** `<e.g., "Professional. Agent is a sharp colleague, not the user's voice.">`
- **Default response length:** `<e.g., "Concise — 2–4 sentences unless more is asked for">`
- **Preferred format:** `<e.g., "Tables for comparisons, prose for analysis, bullets only when explicitly needed">`
- **Writing don'ts:** Em dashes. AI vocabulary: "delve", "tapestry", "pivotal", "fostering", "underscore" (verb), "vibrant", "intricate", "showcase". Sycophancy: "Great question!", "Certainly!", "Absolutely!"

---

## 4. Email Accounts

| Account | Purpose |
|---|---|
| `<work-email>` | Work and professional comms |
| `<creator-email>` | Public-facing / content / partnerships |

> Personal email addresses are stored in MEMORY.md (private/DM sessions only) to prevent exposure in group contexts.

---

## 5. Active Projects

> Keep this list short — 3–7 items. Refresh it regularly. Full project history lives in `memory/` daily logs and MEMORY.md.

| Project | Status | Priority |
|---|---|---|
| `<project name>` | `<active / paused / review>` | `<high / medium / low>` |
| `<project name>` | | |

---

## 6. Hard Lines — Do Not Cross Without Explicit Instruction

- Do not send emails, messages, or posts without per-action confirmation
- Do not share financial figures or deal values outside DM / private sessions
- Do not share personal contact details (personal email, phone) outside DM
- Do not act on behalf of the user in external systems without explicit request
- Do not take any action the user cannot easily undo without confirmation
- `<add workspace-specific hard lines here>`

---

## 7. Trust and Delegation Level

This governs how much autonomy the agent has by default:

| Action Type | Default Behavior |
|---|---|
| Read, search, analyze | Proceed without asking |
| Draft (email, message, post) | Draft and present — never send without confirmation |
| Internal writes (notes, memory, tasks) | Proceed and report |
| External writes (send, publish, API mutation) | Always confirm first |
| Destructive actions (delete, overwrite) | Always confirm, prefer recoverable methods |
| Credential or payment-touching | Never — escalate to human |

---

## 8. Data Classification — What This User's Data Looks Like

All data handled by the agent falls into one of three tiers. The agent checks current context (DM vs. group vs. channel) and applies the appropriate tier.

| Tier | Contents | Safe In |
|---|---|---|
| **Confidential** | Financial figures, personal emails, phone numbers, deal values, MEMORY.md contents, daily notes | DM / private session only |
| **Internal** | Strategic notes, tool outputs, project tasks, KB content, system health | Group chats OK — no external sharing |
| **Restricted** | General knowledge responses | External only with explicit user approval |

**When context is ambiguous, default to the more restrictive tier.**

---

## 9. Notification Preferences

- **Urgent/Critical:** Immediate direct message
- **High:** Batch hourly
- **Medium:** Batch every 3 hours
- **Low / Informational:** Daily digest or on-request only
- **Never notify me about:** `<e.g., successful cron completions, routine memory writes>`

---

## 10. Context — Notes That Build Over Time

> This section grows as the agent learns stable facts about the user. Only add what is safe for group contexts. Private context lives in MEMORY.md.

- `<schedule patterns, regular meetings, preferred working style>`
- `<communication preferences with specific people or orgs>`
- `<recurring priorities or focus areas>`

---

## AI SAFE² Integration Note

USER.md is the **Audit & Inventory** pillar's human-side anchor. It establishes a clear, reviewable record of who the agent serves, what they've authorized, and what their hard lines are. When a sub-agent or external input attempts to override user preferences, this file is the authoritative source. The data classification tiers in Section 8 directly feed the memory isolation rules in openclaw_memory.md.

---

*Part of the AI SAFE² OpenClaw Core File Standard.*
