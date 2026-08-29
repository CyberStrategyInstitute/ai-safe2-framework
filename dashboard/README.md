# AI SAFE² Framework Dashboard
### Interactive explorer for the core framework and profile overlays

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../README.md)
[![Surface](https://img.shields.io/badge/Surface-Dashboard-820F1A?style=flat-square)](./README.md)
[![Core](https://img.shields.io/badge/Core-161_controls-808080?style=flat-square)](./public/data/controls.json)

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Scanner](../scanner/README.md)

**Launch:** [AI SAFE² Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

## What the Dashboard Represents

The dashboard visualizes the **161-control AI SAFE² core taxonomy** across five operational pillars and the core Cross-Pillar Governance layer.

AI SAFE² v3.1 also includes **CP.5.MCP profile controls MCP-1 through MCP-19**. Those are profile controls, not 19 additional core controls. Dashboard data should therefore keep the core taxonomy and profile overlays separate rather than silently changing the framework count.

```text
dashboard/public/data/controls.json          161-control core taxonomy
dashboard/public/data/mcp-profile-v3.1.json CP.5.MCP profile overlay
```

---

## Features

- Persona-routed views for executive, architect, builder, GRC, researcher, and explorer use cases.
- ACT Tier classification and governance guidance.
- Search and filtering across the core taxonomy.
- Cross-Pillar Governance visibility.
- Compliance mapping across the repository's supported framework crosswalks.
- Risk-calculation and implementation guidance surfaces.
- Light/dark presentation and responsive browser use.

The dashboard is an exploration and decision-support surface. Canonical normative control language remains in the framework source files.

---

## v3.1 Data Model

### Core controls

[`public/data/controls.json`](./public/data/controls.json) remains the generated/core dataset for the 161-control taxonomy.

### MCP profile

[`public/data/mcp-profile-v3.1.json`](./public/data/mcp-profile-v3.1.json) mirrors the v3.1 MCP profile data maintained with the MCP server.

Canonical source:

[`skills/mcp/data/mcp-profile-v3.1.json`](../skills/mcp/data/mcp-profile-v3.1.json)

Normative specification:

[CP.5.MCP v3.1](../00-cross-pillar/cp5_mcp_server_security.md)

Keeping these datasets separate prevents the dashboard from reporting 180 framework controls when the correct v3.1 core count remains 161.

---

## Quick Start

### Framework users

1. Open the [live dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/).
2. Select the view that matches your role.
3. Use ACT Tier classification to identify autonomy-dependent governance requirements.
4. Open control details and follow links back to canonical source material when implementing or auditing.

### Developers

```bash
git clone https://github.com/CyberStrategyInstitute/ai-safe2-framework.git
cd ai-safe2-framework/dashboard
open index.html
```

The current dashboard is a static browser application and does not require a build server for basic local use.

---

## Framework Statistics

| Item | v3.1 value |
|---|---|
| Core framework controls | **161** |
| Operational pillars | **5** |
| Core Cross-Pillar controls | **CP.1 through CP.10** |
| MCP profile controls | **MCP-1 through MCP-19** |
| ACT capability tiers | **4** |
| Current MCP specification binding | **2026-07-28** |
| Legacy MCP compatibility binding | **2025-11-25** |

CP.11 UAS is a compliance overlay composed from mapped controls and should not be added to the 161 core count as though every module-level requirement were a new independent core control.

---

## Module Architecture

```text
dashboard/
├── index.html
├── public/
│   └── data/
│       ├── controls.json
│       └── mcp-profile-v3.1.json
└── README.md
```

`index.html` currently contains embedded data used by the browser UI. When core control data changes, update both the generated JSON and the embedded representation through the repository's generation/synchronization process.

Profile overlays should remain separately identifiable in both source and UI so users can distinguish framework controls from protocol-profile controls.

---

## Documentation and Implementation Links

- [Framework Overview](../README.md)
- [Cross-Pillar Governance](../00-cross-pillar/README.md)
- [MCP Profile](../00-cross-pillar/cp5_mcp_server_security.md)
- [AISM](../AISM/)
- [NEXUS](../NEXUS/)
- [MCP Server](../skills/mcp/README.md)
- [Scanner](../scanner/README.md)
- [Repository UX Standard](../docs/REPOSITORY-UX-STANDARD.md)

---

## 🔗 Navigation

[Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/) | [NEXUS](../NEXUS/) | [Scanner](../scanner/README.md) | [MCP Server](../skills/mcp/README.md)

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
