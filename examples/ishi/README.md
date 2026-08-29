<!-- AI-SAFE2-UX:START -->
[![AI SAFE2 v3.1](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Surface: Example](https://img.shields.io/badge/Surface-Example-820F1A?style=flat-square)](../README.md)
[![Context: v3.1 Current](https://img.shields.io/badge/Context-v3.1_Current-808080?style=flat-square)](../../docs/REPOSITORY-UX-STANDARD.md)

[Framework Home](../../README.md) | [Examples Index](../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

> **Current framework context:** AI SAFE2 v3.1. This example may preserve historical component versions or earlier framework references where they describe when the implementation was created. For current conformance, use the v3.1 framework and applicable profile requirements.
<!-- AI-SAFE2-UX:END -->

<!-- stack: Supervisory agent -->
<!-- description: Reviews agent plans and enforces governance decisions before high-risk actions execute. -->

# AI SAFE² for Ishi

**Complete security toolkit for Ishi desktop agent users**

---

## 🚀 Quick Start

**New to Ishi security?** → [10-Minute Hardening Guide](../../guides/ishi-hardening.md)

**Having issues?** → [Troubleshooting Guide](./troubleshooting-ishi.md)

**Windows 11 setup?** → [Ishi + OpenClaw Integration](./ishi-openclaw-integration.md)

## 🎯 Use Cases

**Quick Start:** [5 Essential Integrations](./examples/ishi/ishi-openclaw-integration.md)

**Complete Guide:** [30 Use Case Implementations](./examples/ishi/USE_CASE_IMPLEMENTATION_GUIDE.md)

**Categories:**
- Personal: Life-OS, health tracking, travel automation
- Business: CRM, content, customer support
- Infrastructure: Multi-persona, local LLM, advanced ops
---

## What's Included

### 1. Memory Protocol (5 minutes)
**File:** [`ishi_memory.md`](./ishi_memory.md)

**What it does:** Persistent safety controls embedded in Ishi's context memory.

**Installation:**
```powershell
# Windows
cd $env:APPDATA\ishi\memories\
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi_memory.md" -OutFile "ishi_memory.md"
# Restart Ishi
```

```bash
# macOS/Linux
cd ~/.ishi/memories/
curl -O https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi_memory.md
# Restart Ishi
```

**Key protections:**
- ✅ Permission slider enforcement (3 levels)
- ✅ Ghost file protection (no auto-commits)
- ✅ Token budget tracking (free tier aware)
- ✅ AgenticFlow workflow validation
- ✅ OpenClaw integration safety

---

### 2. Security Scanner (2 minutes)
**File:** [`ishi-scanner.py`](./ishi-scanner.py)

**What it does:** Audits your Ishi installation for 10 security risks.

**Installation:**
```powershell
# Windows
cd $env:USERPROFILE\Downloads
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi-scanner.py" -OutFile "ishi-scanner.py"
python ishi-scanner.py
```

```bash
# macOS/Linux
curl -O https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi-scanner.py
python3 ishi-scanner.py
```

**Checks:**
- Memory protocol deployed
- Permission slider configured
- Token tracking enabled
- Credentials secured
- Ghost file settings
- AgenticFlow/OpenClaw integrations

**Output:** Risk score 0-100 + specific fixes

---

### 3. Troubleshooting Guide
**File:** [`troubleshooting-ishi.md`](./troubleshooting-ishi.md)

**20+ common issues with copy-paste fixes:**
- CRITICAL: Auto-commits, token limits, credential leaks
- HIGH: Memory protocol not loading, scanner issues
- MEDIUM: Performance, integrations
- EMERGENCY: Runaway operations, compromised keys

**Platform-specific:** Windows PowerShell scripts included

---

## Integration Guides

### Ishi + OpenClaw (Windows 11)
**File:** [`ishi-openclaw-integration.md`](./ishi-openclaw-integration.md)

**Architecture:**
- Ishi (Windows native) = Command center
- OpenClaw (WSL2) = 24/7 execution arm
- AI SAFE² = Security layer for both

**Time:** 2 hours setup  
**Cost:** $0/month (free tier works)

---

## Quick Reference

| File | Purpose | Time | Required? |
|------|---------|------|-----------|
| `ishi_memory.md` | Safety protocol | 5 min | ⭐ Yes |
| `ishi-scanner.py` | Vulnerability scan | 2 min | ⭐ Yes |
| `troubleshooting-ishi.md` | Issue fixes | Reference | As needed |
| `ishi-openclaw-integration.md` | Full integration | 2 hours | Optional |

---

## GitHub Structure

```
ai-safe2-framework/
├── examples/
│   ├── ishi/                           # You are here
│   │   ├── README.md                   # This file
│   │   ├── ishi_memory.md              # Memory protocol
│   │   ├── ishi-scanner.py             # Security scanner
│   │   ├── troubleshooting-ishi.md     # Issue resolution
│   │   └── ishi-openclaw-integration.md # Integration guide
│   └── openclaw/                       # OpenClaw security
│       ├── README.md
│       ├── openclaw_memory.md
│       ├── scanner.py
│       ├── troubleshooting.md
│       └── gateway/                    # Control gateway
└── guides/
    ├── ishi-hardening.md               # 10-min setup
    └── openclaw-hardening.md
```

---

## Free Tier Operation

**Works with:**
- ✅ Gemini (Google AI Studio): 1,500 requests/day, $0
- ✅ OpenRouter free models: Unlimited, $0
- ✅ Your own API keys: Use existing tokens

**Token tracking prevents:**
- Unexpected rate limits
- Overage charges
- Service disruptions

**Auto-switches providers when limits hit**

---

## Platform Support

| Platform | Memory Protocol | Scanner | Notes |
|----------|----------------|---------|-------|
| Windows 11 | ✅ | ✅ | PowerShell scripts included |
| macOS | ✅ | ✅ | Native support |
| Linux | ✅ | ✅ | Ubuntu/Debian tested |

---

## Common Issues

### Memory protocol not loading
**Fix:**
```powershell
# Windows
Test-Path "$env:APPDATA\ishi\memories\ishi_memory.md"
# Should return: True

# If False, re-download
cd $env:APPDATA\ishi\memories\
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/examples/ishi/ishi_memory.md" -OutFile "ishi_memory.md"
```

### Scanner not finding Ishi
**Fix:**
```powershell
python ishi-scanner.py --path "$env:APPDATA\ishi"
```

### Ghost files auto-committing
**Fix:**
```
In Ishi: /config ghost_files
Set: Auto-commit = DISABLED
```

**Full troubleshooting:** [troubleshooting-ishi.md](./troubleshooting-ishi.md)

---

## Support

**Documentation:** [AI SAFE² Framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)  
**Issues:** [GitHub Issues](https://github.com/CyberStrategyInstitute/ai-safe2-framework/issues)  
**Security:** [Report vulnerability](https://github.com/CyberStrategyInstitute/ai-safe2-framework/security)  
**Ishi Community:** [Discord](https://qra.ai/discord)

---

## Next Steps

1. **Deploy memory protocol** (5 min)
2. **Run scanner** (2 min)
3. **Fix CRITICAL/HIGH issues** (varies)
4. **Optional: Integrate with OpenClaw** (2 hours)

**Start here:** [10-Minute Hardening Guide](../../guides/ishi-hardening.md)

---

**Built by:** [Cyber Strategy Institute](https://cyberstrategyinstitute.com)  
**License:** MIT (code) + CC-BY-SA 4.0 (documentation)  
**Version:** 2.1

<!-- AI-SAFE2-UX-FOOTER:START -->
---

### Repository navigation

[Examples Index](../README.md) | [Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [NEXUS](../../NEXUS/) | [Scanner](../../scanner/README.md) | [MCP Profile](../../00-cross-pillar/cp5_mcp_server_security.md)

*AI SAFE2 v3.1 | Cyber Strategy Institute*
<!-- AI-SAFE2-UX-FOOTER:END -->
