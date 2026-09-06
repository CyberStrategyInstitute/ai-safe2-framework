# Security Policy

## Supported Versions

Framework and CLI package versions are independent: the current framework is
AI SAFE² v3.1, while the distributable `ai-safe2` CLI is currently in its 0.x
beta series.

| Surface | Version | Security support |
| ------- | ------- | ---------------- |
| AI SAFE² Framework | 3.1.x | Current |
| `ai-safe2` CLI package | 0.1.x | Current beta |
| Older framework and package releases | Earlier | No routine fixes |

## Reporting a Vulnerability
Since this is a Governance Framework, a "vulnerability" is defined as:
1.  **Logical Flaw:** A control that, if implemented, introduces a security risk.
2.  **Code Flaw:** A bug in the `safe2_server.py` MCP script or JSON schema.
3.  **Missing Critical Vector:** A widely exploited attack (e.g., DeepSeek Jailbreak) not covered by the current taxonomy.

### How to Report
Please **DO NOT** open a public GitHub Issue for critical code exploits (Zero-Days).
*   **Email:** `security@cyberstrategyinstitute.com`
*   **Subject:** `[SECURITY] - AI SAFE2 Vulnerability Report`

We will acknowledge your report within 48 hours.
