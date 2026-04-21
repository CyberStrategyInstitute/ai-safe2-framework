# 🧭 AI SAFE² Framework Dashboard — v3.0

Interactive control plane and taxonomy explorer for the **AI SAFE² v3.0 Framework** — 161 controls across 5 operational pillars and a 10-control Cross-Pillar Governance OS.

---

## 🎯 Interactive Dashboard

**[→ Launch Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)**

**Features:**
- 👤 **Persona-routed lenses** — Executive, Architect, Builder, GRC, Researcher, Explorer
- 🤖 **ACT Tier Classifier** — 6 questions → ACT tier + mandatory controls + HEAR/CP.9/CP.8 flags  
- 🛡 **CP.1-CP.10 Governance OS** — 3 first-in-field controls (HEAR, Agent Replication, Active Defense)
- 🔍 **Real-time search** across all 161 control specifications
- 🎨 **Pillar matrix** — filter by priority, version, framework; CP governance band at top
- ⚖ **Compliance crosswalk** — 32 frameworks; select any to see mapped controls
- 📊 **v3.0 Risk Calculator** — CVSS + Pillar + AIVSS AAF live formula
- 🌙 **Dark / light mode** with localStorage persistence
- ✅ **Pre-Flight Checklist CTA** — 35-question builder readiness checklist (free)
- 📱 **Responsive** — no installation, runs entirely in browser

**No installation required.**

---

## 📚 Documentation

- **[Framework Overview](README.md)**
- **[Controls Schema](dashboard/public/data/controls.json)** — machine-readable, 161 controls, v3.0 schema
- **[MCP Server](skills/mcp/README.md)** — Claude Code integration
- **[Scanner](scanner/README.md)** — CI/CD code scanning
- **[Release Notes](RELEASE-NOTES-v3.0.0.md)**

---

## 🚀 Quick Start

### For Framework Users
1. Visit the **[live dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)**
2. Select your role — the dashboard routes you to the right view
3. Run the ACT Tier Classifier to understand your governance requirements
4. Click any control card for the full specification

### For Developers
```bash
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
cd ai-safe2-framework/dashboard
open index.html  # no build required
```

### For Integration
```bash
# 161 controls, v3.0 schema — includes builder_problem, act_minimum, 
# compliance_frameworks (32), version_added, first_in_field
curl https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/dashboard/public/data/controls.json
```

---

## 🎯 Who Should Use This

| Role | What the dashboard shows you |
|------|------------------------------|
| **Board / Executive** | Hexagonal posture radar, 32-framework compliance coverage, CP.1-CP.10 Governance OS in plain English |
| **Security Architect** | Full 161-control matrix, filter by pillar / priority / version / framework, CP governance band at top |
| **Developer / Builder** | ACT Tier Classifier → mandatory controls + HEAR / CP.9 / CP.8 flags, builder-problem framing on every control |
| **GRC / Compliance** | Compliance crosswalk (32 frameworks), self-assessment scorecard, live v3.0 risk calculator |
| **Security Researcher** | CP.1-CP.10 deep dive, MITRE ATLAS crosswalk, attack surface map, 23 new v3.0 controls |
| **Consultant / Assessor** | Explorer mode — search all 161 controls, filter by any dimension |

---

## 📊 Framework Statistics — v3.0

- **161 Controls** — 151 pillar controls + 10 Cross-Pillar Governance OS (CP.1-CP.10)
- **5 Operational Pillars** — Sanitize & Isolate, Audit & Inventory, Fail-Safe & Recovery, 
  Engage & Monitor, Evolve & Educate
- **CP.1-CP.10 Governance OS** — all new in v3.0; CP.7, CP.9, CP.10 are first-in-field standards
- **32 Compliance Frameworks** — ISO 42001, NIST AI RMF, EU AI Act, SOC 2, HIPAA, GDPR, 
  FedRAMP, CMMC 2.0, DORA, SEC Disclosure + 22 more
- **4 ACT Capability Tiers** — governance requirements that scale with agent autonomy level
- **v3.0 Additions** — 23 new pillar controls + CP.1-CP.10, HEAR Doctrine (CP.10), 
  Agent Replication Governance (CP.9), AIVSS AAF composite risk scoring

---

## 📂 Module Architecture
dashboard/
├── index.html              ← Standalone dashboard — 161 controls embedded inline
│                             (CONTROLS_DATA const ~70KB, no runtime fetch required)
├── public/
│   └── data/
│       └── controls.json   ← v3.0 schema — for programmatic/curl access
└── README.md

## 🤝 Modifying the Dashboard

- **UI changes:** Edit `dashboard/index.html` — Alpine.js + Tailwind CDN, no build step required
- **Control data updates:** 
  1. Replace `dashboard/public/data/controls.json` with the new controls JSON
  2. Search for `const CONTROLS_DATA =` in `index.html` and replace the embedded array
     (the dashboard reads from the embedded constant, not the external JSON file)