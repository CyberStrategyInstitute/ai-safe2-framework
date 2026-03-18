# 🧭 AI SAFE² Taxonomy Explorer & Dashboard

Welcome to the official visual control plane and interactive taxonomy explorer for the **AI SAFE² Framework**. 

Rather than reading through static documentation, this dashboard provides Security Architects, GRC Officers, and AI Engineers with a dynamic, interactive interface to navigate the framework's pillars, maturity models, and agentic AI guardrails.

---

## 🎯 Interactive Dashboard
 
**Explore all 128 AI SAFE² controls through our live, interactive taxonomy explorer.**
 
### 👉 **[Launch Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)** 👈
 
The AI SAFE² Dashboard provides security architects, GRC officers, and AI engineers with a dynamic, filterable interface to navigate the framework's complete control catalog.
 
**Features:**
- 🔍 **Real-time search** across all control metadata
- 🎨 **Pillar-based filtering** for strategic domain focus  
- 📊 **Risk-level visualization** (Critical, High, Medium, Low)
- 💼 **Executive summaries** with business impact statements
- 🏷️ **Framework mappings** to OWASP, MITRE, NIST, ISO standards
- 🆕 **v2.1 highlights** for next-generation controls (Agents, Memory, NHI)
- 📱 **Responsive design** optimized for all devices
 
**No installation required** — the dashboard runs entirely in your browser with zero dependencies.
 
![AI SAFE² Dashboard Preview](assets/dashboard-preview.png)  
*Interactive taxonomy explorer with 128 controls across 5 strategic pillars*
 
---
 
## 📚 Documentation
 
- **[Dashboard User Guide](dashboard/README.md)** - Complete usage documentation
- **[Release Notes v2.1.0](RELEASE-NOTES-v2.1.0.md)** - Latest features and improvements
- **[Framework Overview](README.md)** - Methodology and strategic approach *(link to your existing docs)*
- **[Control Schema](dashboard/public/data/controls.json)** - Machine-readable control definitions
 
---
 
## 🚀 Quick Start
 
### For Framework Users
1. Visit the **[live dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)**
2. Use the search bar or pillar filters to find relevant controls
3. Click any control card to view detailed implementation guidance
4. Reference the decision-maker impact for stakeholder communications
 
### For Developers
```bash
# Clone the repository
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
 
# Navigate to dashboard
cd ai-safe2-framework/dashboard
 
# Open locally (no build required)
open index.html
```
 
### For Integration
```bash
# Fetch controls programmatically
curl https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/dashboard/public/data/controls.json
```
 
---
 
## 🎯 Who Should Use This
 
| Role | Use Case |
|------|----------|
| **Security Architects** | Design AI system controls and threat models |
| **GRC Officers** | Map to compliance frameworks and audit requirements |
| **AI Engineers** | Access implementation guidance and technical references |
| **Executive Leadership** | Understand business impact and risk prioritization |
| **Consultants** | Navigate the framework efficiently during assessments |
| **Researchers** | Explore the taxonomy for academic study |
 
---
 
## 📊 Framework Statistics
 
- **128 Controls** across **5 Strategic Pillars**
- **4 Risk Levels** for prioritization (Critical → Low)
- **20+ Framework Mappings** (OWASP, MITRE ATLAS, NIST, ISO, etc.)
- **v2.1 Additions** covering Agents, Memory, NHI, Multi-Agent systems
- **Gap Filler Controls** for threats unique to AI systems
 
---
 
*For detailed release information, see [RELEASE-NOTE 2026-3-18 AI SAFE² Framework Dashboard v2.1.0](https://github.com/CyberStrategyInstitute/ai-safe2-framework/releases/tag/2026-3-18-AI-SAFE%C2%B2-Framework-Dashboard-v2.1)*

---

## 🛠️ Local Usage & Development

If you are contributing to the framework or want to test modifications to the UI locally, no complex build process or CLI is required.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
   ```

2. **Navigate to the dashboard module:**
   ```bash
   cd ai-safe2-framework/dashboard
   ```

3. **Run locally:** Simply double-click the `index.html` file to open it in your default web browser. No local web server is strictly necessary for static HTML/JS/CSS inspection.

---

## 📂 Module Architecture

This folder serves as the UI/Presentation layer for the framework.

```
dashboard/
├── index.html          ← NEW standalone file
├── public/
│   └── data/
│       └── controls.json   ← Your existing data
└── README.md           ← Quick Start
```

---

## 🤝 Modifying the Taxonomy

As the AI SAFE² framework evolves, the dashboard must be updated to reflect the latest GRC standards and architectural guardrails.

* **UI/UX Changes:** Modify the core `index.html` and corresponding CSS.
* **Data Updates:** (Update this line based on how your app is built - e.g., "Modify the JSON objects within the `js/` directory to update pillar definitions and maturity scoring requirements.")

---

Part of the Cyber Strategy Institute open-source initiative. **Engineering Certainty for the AI Era.**
