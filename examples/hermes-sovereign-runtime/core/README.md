# Core Governance Files
### Hermes Sovereign Runtime · AI SAFE² v3.0

These files are the semantic layer of the sovereign runtime.
They load into Hermes' memory system and establish governance directives
at the highest memory priority — before any skill, session content, or retrieved data.

---

## Deployment

### Docker Compose (automatic)

The `docker-compose.yml` mounts all core files as read-only into the Hermes container:

```yaml
volumes:
  - ./core/hermes_memory_vaccine.md:/home/hermes/.hermes/memories/000_VACCINE_sovereign.md:ro
  - ./core/IDENTITY.md:/home/hermes/.hermes/memories/001_IDENTITY.md:ro
  - ./core/SOUL.md:/home/hermes/.hermes/memories/002_SOUL.md:ro
  - ./core/SUBAGENT-POLICY.md:/home/hermes/.hermes/memories/003_SUBAGENT-POLICY.md:ro
```

The `000_` prefix ensures the vaccine loads first alphabetically (before any user memory files).

### Manual deployment

```bash
# Create memories directory if it doesn't exist
mkdir -p ~/.hermes/memories/

# Copy all governance files (vaccine must be alphabetically first)
cp core/hermes_memory_vaccine.md ~/.hermes/memories/000_VACCINE_sovereign.md
cp core/IDENTITY.md ~/.hermes/memories/001_IDENTITY.md
cp core/SOUL.md ~/.hermes/memories/002_SOUL.md
cp core/SUBAGENT-POLICY.md ~/.hermes/memories/003_SUBAGENT-POLICY.md
cp core/HEARTBEAT.md ~/.hermes/memories/004_HEARTBEAT.md

# Verify
ls -la ~/.hermes/memories/ | head -10
```

### Verify vaccine is loaded

```bash
hermes status --memory
# Look for: 000_VACCINE_sovereign loaded
```

---

## File Priority and Load Order

| Filename | Priority | Purpose |
|---|---|---|
| `000_VACCINE_sovereign.md` | **HIGHEST** | Security directives — loads before everything |
| `001_IDENTITY.md` | High | Identity anchor — prevents replacement attacks |
| `002_SOUL.md` | High | Alignment constitution (Love Equation) |
| `003_SUBAGENT-POLICY.md` | High | Subagent delegation governance |
| `004_HEARTBEAT.md` | Standard | Scheduled health check protocol |

---

## Files

| File | What It Does |
|---|---|
| `hermes_memory_vaccine.md` | **The most critical file.** 8 security directives covering credential protection, injection immunity, skill boundaries, filesystem limits, subagent governance, approval gates, identity anchor, and multi-platform security. Loads before ALL other memory. |
| `IDENTITY.md` | Minimal 5-line identity anchor. Establishes who the agent is before any session content loads. Prevents "you are now a different agent" attacks. |
| `SOUL.md` | Alignment constitution. Love Equation integration: defines cooperation/defection events, operational bands, and what it means for the agent to remain aligned under adversarial conditions. |
| `SUBAGENT-POLICY.md` | Subagent governance. Spawn protocol, capability inheritance rules (no parent capability inheritance), scope limits, attestation requirements, and termination triggers. |
| `HEARTBEAT.md` | Health check protocol. What the agent verifies every 30–60 minutes: security posture, memory vaccine status, gateway connectivity, alignment score. |

---

## Modifying Core Files

**Do not modify the vaccine without understanding what you're removing.**

The vaccine's directives are defense-in-depth. Removing a directive because it
"seems overly restrictive" is how defenses get slowly eroded to nothing.

If you need to customize:
1. Add directives — don't remove existing ones
2. Adjust scope boundaries (e.g., wider `HERMES_READ_SAFE_ROOT`) only with documented justification
3. Version control all changes

---

*Core Governance Files · Cyber Strategy Institute · AI SAFE² v3.0*
