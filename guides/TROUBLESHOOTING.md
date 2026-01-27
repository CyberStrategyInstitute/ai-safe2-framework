# 🔧 Troubleshooting & Common Issues

**The Philosophy of AI SAFE²:**
If the system fails, it must **Fail-Closed**. It is better to show an error message than to leak a secret or execute a malicious prompt.

---

## 🔍 Scanner & Audit Issues

### 🔴 Issue: Scanner Reports "False Positives"
**Symptom:** The `scanner.py` or `detect-secrets` tool flags a random string as an API key (e.g., a long CSS hash or a UUID).
**Cause:** The scanner looks for "High Entropy Strings" (randomness).
**Fix:**
1.  **Verify:** Manually check the line number. Is it a real secret?
2.  **Allowlist:** If it is safe, add the line to your `.secrets.baseline` file.
3.  **Do Not Delete:** Never simply ignore the report. Comment in the code why that string is safe (e.g., `# Safe: CSS Hash`).

### 🔴 Issue: `pip install` Fails
**Symptom:** `ModuleNotFoundError: No module named 'detect_secrets'`
**Cause:** You are likely in the wrong virtual environment or missing the package.
**Fix:**
```bash
pip install detect-secrets pyyaml
# If that fails, try:
python3 -m pip install detect-secrets pyyaml
```
## 🛡️ Gateway & Docker Issues

### 🔴 Issue: Connection Refused (`localhost:8000`)
**Symptom:** Your Python script or Agent fails with `ConnectionRefusedError` when trying to talk to the Gateway.
**Cause:** The Docker container is not running, or ports are not mapped.
**Fix:**
1.  **Check Status:** Run `docker ps`. Is `ai-safe-gateway` listed?
2.  **Check Ports:** Did you run the command with `-p`?
    *   ❌ Wrong: `docker run ai-safe-gateway`
    *   ✅ Right: `docker run -p 8000:8000 ai-safe-gateway`
3.  **Firewall:** Ensure port 8000 is open on your local machine.

### 🔴 Issue: Legitimate Prompts are Blocked
**Symptom:** You send a normal request like "Help me design a system," but get: `Security Policy Violation: Blocked Pattern`.
**Cause:** The Regex rules in `default.yaml` are too aggressive for your specific use case.
**Fix:**
1.  **Check Logs:** Look at the Docker terminal output. It will tell you *exactly* which regex triggered the block.
2.  **Tune Regex:**
    *   *Example:* If `system` is blocking "system design," change the regex from `system` to `system:` (looking for the prompt injection syntax specifically).
3.  **Override:** If using the SDK, pass a custom `validation_config
```python
# Allow 10 failures before breaking
api_breaker = pybreaker.CircuitBreaker(fail_max=10, reset_timeout=60)
```
### 🔴 Issue: Context Window Exceeded
**Symptom:** `InvalidRequestError: This model's maximum context length is 8192 tokens...`
**Cause:** You are not sanitizing input length. Users (or loops) are sending too much text.
**Fix:**
1.  **Enforce Limits:** Use the `InputValidator` class to truncate input *before* sending it.
    ```python
    if len(user_input) > 2000:
        user_input = user_input[:2000] # Truncate
    ```
2.  **Memory Management:** If using an Agent, ensure you are summarizing conversation history.

---

## 🆘 Still Stuck?

*   **Community Support:** Open an Issue in this GitHub Repository.
*   **Live Chat:** Join the "Vanguard" channel on our Discord.
*   **Enterprise Support:** Available for owners of the [AI SAFE² Implementation Toolkit](https://cyberstrategyinstitute.com/AI-Safe2/).
