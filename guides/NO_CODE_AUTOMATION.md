# 🤖 No-Code Security Guide (Make.com / n8n)

**Target Audience:** Automation Engineers, Ops Managers, No-Code Builders.
**Goal:** Secure your AI workflows against injection and cost overruns without writing complex code.

---

## 🏗️ The Golden Rule: "Sandwich Architecture"

**Never** connect a User Input directly to an LLM Node. You must "sandwich" the AI between security layers.

**[ Trigger ]** -> **[ 🛡️ Security Filter ]** -> **[ 🤖 AI Agent ]** -> **[ 🔍 Output Validator ]** -> **[ Response ]**

---

## 🟠 Platform: Make.com (formerly Integromat)

Make.com does not allow custom Python scripts easily, so we use native modules to enforce security.

### 1. The Input Filter (Sanitization)
**Goal:** Stop "Ignore Previous Instructions" attacks before they cost you money.

*   **Step A:** Place a `Text Parser` or `Router` module immediately after your Trigger.
*   **Step B:** Set up a Filter condition between the Trigger and the AI Module.
    *   **Label:** `Security Check`
    *   **Condition 1:** `Length(User_Message)` < `2000` (Prevents Token Overload)
    *   **Condition 2:** `User_Message` Does not contain (Case Insensitive) `system:`
    *   **Condition 3:** `User_Message` Does not contain (Case Insensitive) `ignore previous`
*   **Fallback:** If the filter fails, route to a simple JSON response: `{"error": "Security Policy Violation"}`.

### 2. The Circuit Breaker (Cost Control)
**Goal:** Stop the scenario if the AI hangs or errors out.

*   **Step A:** Right-click your OpenAI/Anthropic module.
*   **Step B:** Select **"Add Error Handler"**.
*   **Step C:** Connect a `Break` directive.
    *   **Number of attempts:** `3`
    *   **Interval:** `5` seconds
*   **Why?** This prevents your scenario from getting stuck in an infinite loop if the API goes down, saving your operations budget.

---

## 🟢 Platform: n8n

n8n is more powerful because it allows JavaScript execution. We will use a **Code Node** to act as a firewall.

### 1. The Security Node (JavaScript)
Insert a **Code Node** *before* your AI Model node. Paste this script to sanitize inputs.

```javascript
// AI SAFE2 - Input Security Validator
// ----------------------------------
const input = items[0].json.body.message || ""; // Adjust based on your webhook structure

// 1. DOS Protection (Length Check)
const MAX_LENGTH = 2000;
if (input.length > MAX_LENGTH) {
  throw new Error(`Security Violation: Input exceeds ${MAX_LENGTH} characters.`);
}

// 2. Prompt Injection Blocklist
const blockedPatterns = [
  'system:', 
  'ignore previous', 
  '<script', 
  'drop table'
];

if (blockedPatterns.some(word => input.toLowerCase().includes(word))) {
   // Fail Closed: Stop execution immediately
   throw new Error('Security Violation: Malicious pattern detected.');
}

// 3. PII Redaction (Basic Example)
// Replace email addresses with [REDACTED]
const cleanInput = input.replace(/[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}/g, "[REDACTED_EMAIL]");

return [{json: { safe_message: cleanInput }}];
```
### 2. Audit Logging
Don't rely on n8n execution history (it gets deleted). Create a permanent audit trail.

*   **Action:** Add a `Google Sheets` or `Postgres` node *after* every AI interaction.
*   **Data to Log:**
    *   `Timestamp` (ISO format)
    *   `User_ID` (if available)
    *   `Input_Snippet` (First 50 chars)
    *   `Token_Usage` (From AI Node Output)
    *   `Status` (Success/Fail)

---

## 📥 Downloads & Next Steps

*   **Need the Blueprint?** [Download the n8n Secure Node JSON](../templates/n8n_secure_node.json) *(Coming Soon)*
*   **Need Client Policies?** If you are building this for a client, you need to hand them an **Acceptable Use Policy** and **Risk Assessment**. These are included in the [AI SAFE² Implementation Toolkit](https://cyberstrategyinstitute.com/AI-Safe2/).
*   **Stuck?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md).
