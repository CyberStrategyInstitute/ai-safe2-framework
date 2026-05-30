# Migration Guide
**Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0**
**Cyber Strategy Institute**

This guide covers migration from an unprotected Hermes installation to the full Hermes Sovereign Runtime.

---

## Migration Paths

| Your Starting Point | Target State | Estimated Time |
|--------------------|-------------|----------------|
| No Hermes installed | Fresh HSR deployment | 30-45 minutes |
| Hermes (local, no Docker) | Full HSR stack | 2-4 hours |
| Hermes (Docker, no security) | Full HSR stack | 1-2 hours |
| OpenClaw with AI SAFE² | HSR (pattern is the same) | 30-60 minutes |
| Hermes (partial hardening) | Full HSR stack | 1-2 hours |

---

## Priority 0: Critical Immediate Fixes

Before anything else, apply these three fixes to any running Hermes deployment. These address the Critical severity findings from the April 2026 independent audit.

### Fix 1: Override the Container Approval Bypass

```bash
# In your .env or docker-compose.yml environment block
HERMES_FORCE_APPROVAL=true
```

**Why:** `tools/approval.py` unconditionally skips all approval checks in containerized environments. Every Docker deployment has zero approval gates until this is set.

### Fix 2: Install the Memory Vaccine

```bash
# Copy the vaccine file into Hermes' memory directory
# The 000_ prefix ensures it loads first alphabetically
cp hermes-sovereign-runtime/core/hermes_memory_vaccine.md \
   ~/.hermes/memories/000_VACCINE_sovereign.md

# Restart Hermes to load
hermes restart
```

**Why:** Without the vaccine, a single successful prompt injection can write adversarial instructions to persistent memory that execute in all future sessions.

### Fix 3: Disable the WeChat Work Adapter

```bash
# In .env
WECOM_ENABLED=false
```

**Why:** CVE-2026-7396 — unauthenticated remote filesystem read via path traversal.

---

## Step-by-Step Migration

### Step 1: Backup Current State

```bash
# Backup existing Hermes data before migration
mkdir -p ~/hermes-backup-$(date +%Y%m%d)
cp -r ~/.hermes ~/hermes-backup-$(date +%Y%m%d)/
```

### Step 2: Clone HSR Package

```bash
git clone https://github.com/CyberStrategyInstitute/hermes-sovereign-runtime.git
cd hermes-sovereign-runtime
```

### Step 3: Configure Environment

```bash
# Copy template and configure
cp .env.example .env
chmod 600 .env

# Open .env and set at minimum:
# - ANTHROPIC_API_KEY (or other LLM provider key)
# - HERMES_FORCE_APPROVAL=true
# - HERMES_READ_SAFE_ROOT=/opt/hermes/workspace
# - ANTHROPIC_BASE_URL=http://localhost:8000/v1
# - WECOM_ENABLED=false
nano .env
```

### Step 4: Install Core Governance Files

```bash
# Create Hermes memory directory if it doesn't exist
mkdir -p ~/.hermes/memories

# Install governance files (000_ prefix = load first)
cp core/hermes_memory_vaccine.md ~/.hermes/memories/000_VACCINE_sovereign.md
cp core/IDENTITY.md ~/.hermes/memories/IDENTITY.md
cp core/SOUL.md ~/.hermes/memories/SOUL.md
cp core/SUBAGENT-POLICY.md ~/.hermes/memories/SUBAGENT-POLICY.md
cp core/HEARTBEAT.md ~/.hermes/memories/HEARTBEAT.md
```

### Step 5: Run Static Validation

```bash
chmod +x validation/*.sh scripts/*.sh
./validation/pass1_static.sh
# Fix any FAIL items before proceeding
```

### Step 6: Deploy the Gateway

```bash
# Install Python dependencies
pip install flask pyyaml requests --break-system-packages

# Start the gateway (it must be running before Hermes)
cd gateway
python3 gateway.py &
cd ..

# Verify gateway is running
curl http://localhost:8000/hsr/health
```

### Step 7: Deploy Full Docker Stack (Recommended)

```bash
# If using Docker Compose (recommended for production)
docker-compose up -d

# Verify all services running
docker-compose ps

# Check gateway health
curl http://localhost:8000/hsr/health
```

### Step 8: Run Runtime Validation

```bash
./validation/pass2_runtime.sh
# All FAIL items must be resolved before production use
```

### Step 9: Run Compliance Check

```bash
./validation/pass4_compliance.sh
```

### Step 10: Final Readiness Gate

```bash
./validation/pass5_readiness.sh
# Review operator attestation checklist at end of output
```

---

## Migrating from OpenClaw AI SAFE²

If you're already running the OpenClaw sovereign runtime from the AI SAFE² framework, the migration is straightforward — same pattern, different agent:

| OpenClaw Component | HSR Equivalent |
|-------------------|---------------|
| `openclaw_memory.md` | `core/hermes_memory_vaccine.md` |
| `IDENTITY.md` | `core/IDENTITY.md` (identical format) |
| `SOUL.md` | `core/SOUL.md` (same Love Equation) |
| `scanner.py` | `gateway/scanner.py` (extended for skills hub + plugins) |
| `gateway.py` | `gateway/gateway.py` (same pattern, Hermes-specific filters) |
| Ishi supervisor | `supervisor/ishi_config.yaml` (enhanced with subagent governance) |

Key differences:
- HSR adds `SUBAGENT-POLICY.md` (Hermes has subagent delegation; OpenClaw does not)
- HSR scanner.py checks for 6+ platform adapter security (Telegram, Discord, etc.)
- HSR cron governance is more extensive (Hermes has native cron scheduler)

---

## Migrating Skills

Any skills installed from agentskills.io require review before running in HSR:

```bash
# Scan all installed skills for security issues
python3 gateway/scanner.py --target ~/.hermes/skills/ --strict

# For each skill flagged, you have three options:
# 1. Remove it: rm ~/.hermes/skills/skill_name.md
# 2. Review + whitelist: add to skills-registry/approved/
# 3. Sandbox it: move to quarantine and test in isolated environment

# Generate provenance manifest for approved skills
cp skills-registry/skill_manifest_template.yaml \
   skills-registry/approved/your_skill_name.yaml
# Fill in the template with skill details
```

---

## Rollback Procedure

If HSR causes issues with existing workflows:

```bash
# Stop HSR stack
docker-compose down

# Restore backup
cp -r ~/hermes-backup-$(date +%Y%m%d)/.hermes ~/.hermes

# Run Hermes without gateway (removes HSR protection)
# Remove ANTHROPIC_BASE_URL override from .env
hermes chat
```

**Note:** Rolling back removes all HSR security controls. The Critical findings (container approval bypass, unrestricted file read) return immediately.

---

## Getting Help

- **GitHub Issues:** github.com/CyberStrategyInstitute/hermes-sovereign-runtime/issues
- **Security Issues:** See SECURITY.md for responsible disclosure
- **AI SAFE² Framework:** github.com/CyberStrategyInstitute/ai-safe2-framework

---

*Migration guide version: 1.0 | AI SAFE² v3.0 | Cyber Strategy Institute*
