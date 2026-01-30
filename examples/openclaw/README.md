# AI SAFE² for OpenClaw formerly Moltbot/Clawdbot

**Complete security toolkit for Openclaw users**

---

## 🚨 Quick Navigation

**Just want to secure your Openclaw?** → Start with [10-Minute Hardening Guide](../../guides/openclaw-hardening.md)

**Having issues?** → Check [Troubleshooting Guide](./troubleshooting.md)

**Technical deep-dive?** → See [Full Hardening Guide](../../guides/openclaw-hardening.md)

---

## What's Included

### 1. Memory Protocol (5 minutes)
**File:** [`openclaw_memory.md`](./openclaw_memory.md)

**What it does:** Drop-in file that embeds AI SAFE² safety controls into Openclaw's persistent memory.

**Installation:**
```bash
cd ~/.openclaw/memories/
curl -O https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/openclaw/openclaw_memory.md
# Restart OpenClaw - safety controls now active
```

**Key protections:**
- ✅ Blocks external communications without approval
- ✅ Detects prompt injection attempts  
- ✅ Redacts secrets from outputs
- ✅ Requires human approval for high-risk actions

---

### 2. Security Scanner (2 minutes)
**File:** [`scanner.py`](./scanner.py)

**What it does:** Scans your Openclaw installation for vulnerabilities and generates risk score.

**Installation:**
```bash
curl -O https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/openclaw/scanner.py
python3 scanner.py --path ~/.openclaw
```

**Checks for:**
- Network exposure (0.0.0.0 bindings)
- File permissions (world-readable configs)
- Dangerous tools enabled (exec, browser)
- Log redaction disabled
- Missing audit logs

**Output:** Risk score (0-100) + specific remediation steps

---

### 3. Control Gateway (10 minutes)
**Directory:** [`gateway/`](./gateway/)

**What it does:** Runs as reverse proxy enforcing AI SAFE² policies between Openclaw and Anthropic API.

**Installation:**
```bash
cd ~/.openclaw/
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
cd ai-safe2-framework/examples/openclaw/gateway/
./start.sh
```

**Features:**
- ✅ JSON schema validation
- ✅ Prompt injection blocking
- ✅ High-risk tool denial
- ✅ Immutable audit logging
- ✅ Risk scoring (0-10)
- ✅ Circuit breakers

---

## Quick Start (Choose Your Path)

### Path 1: Individual User (Fastest)
**Goal:** Secure your personal Openclaw in 10 minutes

1. Run scanner: `python3 scanner.py --path ~/.openclaw`
2. Fix CRITICAL issues (typically: close public exposure)
3. Add memory protocol to `/memories/` folder
4. Re-run scanner to verify

**Time:** 10 minutes  
**Difficulty:** Easy  
**Protection Level:** Medium

---

### Path 2: Power User (Recommended)
**Goal:** Full AI SAFE² protection with control gateway

1. Follow Path 1 steps
2. Deploy control gateway (runs on localhost)
3. Configure Openclaw to use gateway as proxy
4. Enable audit logging and monitoring

**Time:** 30 minutes  
**Difficulty:** Medium  
**Protection Level:** High

---

### Path 3: Enterprise/Team
**Goal:** Compliance-ready deployment (SOC 2, ISO 42001)

1. Follow Path 2 steps
2. Deploy gateway on dedicated server/VM
3. Integrate audit logs with SIEM
4. Implement access controls (SSO/MFA)
5. Generate compliance reports

**Time:** 2-4 hours  
**Difficulty:** Advanced  
**Protection Level:** Enterprise-grade

**Guide:** [Enterprise Deployment](../../guides/openclaw-enterprise.md)

---

## Common Issues

### "Gateway exposed on 0.0.0.0"
**Fix:**
```bash
pkill -f "openclaw gateway"
openclaw gateway --bind 127.0.0.1 --port 18789
```

### "API keys in logs"
**Fix:** Set `"redactSensitive": "all"` in `~/.openclaw/openclaw.json`

### "Control gateway won't start"
**Fix:** 
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cd gateway/
./start.sh
```

**Full troubleshooting:** [troubleshooting.md](./troubleshooting.md)

---

## Architecture

```
User Input (WhatsApp, Discord, etc.)
    ↓
Openclaw Message Router
    ↓
AI SAFE² Memory Protocol (persistent context)
    ↓
AI SAFE² Control Gateway (external proxy)
    ├─ Schema Validation
    ├─ Prompt Injection Check
    ├─ Risk Scoring
    ├─ Tool Policy Enforcement
    └─ Audit Logging
    ↓
Anthropic Claude API (if approved)
    ↓
Tool Execution (shell, files, browser)
    ↓
Response to User (secrets redacted)
```

**Key Principle:** AI SAFE² runs OUTSIDE Openclaw as independent enforcement layer.

---

## Files in This Directory

| File | Purpose | Required? |
|------|---------|-----------|
| `openclaw_memory.md` | Persistent safety controls | Recommended |
| `scanner.py` | Vulnerability scanner | Yes (for audit) |
| `troubleshooting.md` | Common issues + fixes | Reference |
| `gateway/` | Control gateway (proxy) | Recommended |
| `gateway/gateway.py` | Main server code | - |
| `gateway/config.yaml` | Configuration | - |
| `gateway/start.sh` | One-command deploy | - |
| `gateway/schemas/` | JSON validation schemas | - |

---

## Support & Community

**Documentation:** [AI SAFE² Framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)

**Issues:** [GitHub Issues](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues)

**Security:** [Report vulnerability](https://github.com/CyberStrategyInstitute/ai-safe2-framework/security)

**Blog:** [Openclaw Security Articles](https://cyberstrategyinstitute.com/tag/openclaw/)

**Resource Map:** [Industry Security Resources](../../resources/openclaw_security_resource_map.md)

---

## Next Steps

1. **Read:** [10-Minute Hardening Guide](../../guides/openclaw-hardening.md)
2. **Run:** `python3 scanner.py --path ~/.openclaw`
3. **Deploy:** Control gateway for continuous protection
4. **Learn:** [Full integration guide](../../guides/openclaw-integration-guide.md)

---

**Built by:** [Cyber Strategy Institute](https://cyberstrategyinstitute.com)  
**License:** MIT (code) + CC-BY-SA 4.0 (documentation)  
**Version:** 2.1

