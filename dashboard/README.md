# 🧭 AI SAFE² Taxonomy Explorer & Dashboard

Welcome to the official visual control plane and interactive taxonomy explorer for the **AI SAFE² Framework**. 

Rather than reading through static documentation, this dashboard provides Security Architects, GRC Officers, and AI Engineers with a dynamic, interactive interface to navigate the framework's pillars, maturity models, and agentic AI guardrails.

---

## 🚀 Access the Live Dashboard

You do not need to download this repository to use the dashboard. It is hosted live via GitHub Pages.

👉 **[Launch the AI SAFE² Taxonomy Explorer](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)**

*(Note: If the link returns a 404, please ensure GitHub Pages is enabled in the repository settings targeting the `main` branch).*

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
