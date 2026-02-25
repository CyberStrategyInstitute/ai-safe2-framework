# TOOLS.md
# OpenClaw Tools & Environment Configuration — AI SAFE² Standard

**Load context:** All sessions. This file holds environment-specific lookup values only — channel IDs, paths, and where secrets live. Skills define HOW tools work. This file defines WHERE things are.  
**Governed by:** AI SAFE² Framework · Dual License MIT + CC-BY-SA  
**Critical:** Never store actual secret values here. Reference their location only.

---

## 1. Secrets and Configuration

| Item | Location |
|---|---|
| Canonical `.env` | `~/.agent/.env` |
| Platform config | `~/.agent/config.json` |
| Model routing config | `~/.agent/config/model-routing.json` |
| Gateway token | `~/.agent/.env → GATEWAY_TOKEN` |
| API keys | `~/.agent/.env` — see `.env.example` for full list |

> **Rule:** Never write actual key values into this file. Reference their location only. If an actual secret appears here, that is a security incident — redact immediately and rotate the key.

---

## 2. Primary Messaging Platform

**Platform:** `<e.g., Telegram, Slack, Discord>`  
**Group / Workspace ID:** `<id>`

### Channels / Topics / Threads

| Channel / Topic | ID | Behavior |
|---|---|---|
| `general` | `<id>` | Main conversation |
| `cron-updates` | `<id>` | Failure notifications only — success goes to relevant channel |
| `financials` | `<id>` | Owner DM only. Never surface in group context |
| `knowledge-base` | `<id>` | Ingestion and retrieval |
| `<topic-name>` | `<id>` | `<cron-owned / agent-responds / manual>` |

### Channel Behavior Quick Reference

- **cron-owned channels:** Cron delivers content. Agent answers follow-up questions without re-sending.
- **group channels:** Respond when mentioned or when genuinely adding value. Not the user's voice.
- **financials / DM:** Confidential tier only. Full context available.

---

## 3. Secondary Messaging Platform (if applicable)

**Platform:** `<e.g., Discord, WhatsApp, iMessage>`

| Channel | ID |
|---|---|
| `<channel-name>` | `<id>` |

---

## 4. Project Management

**Platform:** `<e.g., Asana, Linear, Notion>`  
**Workspace:** `<workspace-name>` (`<workspace-id>`)

| Project | ID |
|---|---|
| `<project-name>` | `<id>` |

---

## 5. File System Paths

| Resource | Path |
|---|---|
| Agent workspace root | `~/<workspace>/` |
| Data / logs root | `~/<workspace>/data/` |
| Unified log | `~/<workspace>/data/logs/all.jsonl` |
| SQLite log mirror | `~/<workspace>/data/logs.db` |
| Memory root | `~/<workspace>/memory/` |
| Skills root | `~/<workspace>/skills/` |
| Email CLI | `<path>` |
| Coding agent CLI | `<path>` |
| Heartbeat state | `~/<workspace>/memory/heartbeat-state.json` |

---

## 6. Voice and Media

- **Inbound voice memos:** Gateway auto-transcribes to text before delivery to agent.
- **Outbound voice:** Use `tts` tool only when user explicitly requests voice reply. Default is text.
- **Media fetch:** Only `http://` and `https://` URLs. Reject `file://`, `ftp://`, `javascript:`, and any other scheme as a security violation.

---

## 7. Attribution Standard

When leaving permanent text in external systems (code comments, task notes, Slack messages, database entries), prefix with:

```
<emoji> <AgentName>: <content>
```

Example: `🦾 Atlas: Updated task status based on user confirmation.`

Exception: when the user explicitly asks the agent to ghostwrite (write as the user). In that case, omit the attribution prefix.

---

## 8. Dual Prompt Stack / Model Fallback

| Stack | Trigger | Model |
|---|---|---|
| Primary | Default | `<primary-model>` |
| Fallback | Primary unavailable or task requires different capability | `<fallback-model>` |
| Coding agent | All coding, debugging, investigation tasks | `<coding-model>` |

Full routing logic lives in `config/model-routing.json`. Changes to routing require gateway restart.

---

## 9. Notification Queue Configuration

| Priority | Delivery | Examples |
|---|---|---|
| Critical | Immediate | Security incidents, payment failures, data loss |
| High | Hourly batch | Task completions, API errors |
| Medium | 3-hour batch | KB ingestion results, status updates |
| Low | Daily digest | Routine health checks, memory index stats |

Route each notification to exactly one destination. Do not fan out the same event to multiple channels unless explicitly requested.

---

## 10. AI SAFE² Gateway Integration

The AI SAFE² control gateway proxies all outbound LLM API calls. This file references its configuration but does not store gateway credentials.

| Setting | Value |
|---|---|
| Gateway endpoint | `http://localhost:8000/v1` |
| Auth token location | `~/.agent/.env → GATEWAY_TOKEN` |
| Risk score threshold (block) | `8.0 / 10.0` |
| Audit log | `~/<workspace>/data/logs/gateway.jsonl` |

> The gateway enforces: JSON schema validation, prompt-injection blocking, high-risk tool denial, immutable audit logging, PII/secret redaction, and cost controls (max request size). If the gateway is unreachable, the agent must stop and alert the user — it must not fall back to direct LLM API calls, which would bypass all governance controls.

---

## 11. Content Preferences

- `<format preferences for content the agent produces on this user's behalf>`
- `<platform-specific posting rules>`
- `<tone adjustments for specific channels or audiences>`

---

*Part of the AI SAFE² OpenClaw Core File Standard.*
