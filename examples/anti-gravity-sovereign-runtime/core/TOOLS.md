# TOOLS.md - Permitted Capabilities & Execution Rules

Aligned with **AI SAFE² Control: CP.5.MCP & S1.3 Tool Authorization**.

---

## 🛠️ Permitted Tools Whitelist

Below is the verified list of tools allowed for operation within this sovereign workspace runtime:

| Tool Name | Class | Sandbox Policy | Authorized Use Case |
| :--- | :--- | :--- | :--- |
| `view_file` | Read | Allowed (Scratch only) | Reading local project code files. |
| `write_to_file` | Write | Allowed (Scratch only) | Creating new project files. |
| `replace_file_content` | Edit | Allowed (Scratch only) | Modifying existing workspace files. |
| `multi_replace_file_content` | Edit | Allowed (Scratch only) | Batch edits across a single code file. |
| `run_command` | Execute | Ask (Prefix Whitelist) | Running shell compilations and tests. |
| `read_url_content` | Network | Ask (Domain Whitelist) | Accessing library documentation. |
| `invoke_subagent` | Spawning | Allowed (Sandbox mode) | Running research tasks in isolation. |

---

## 🚫 Restricted / Denied Tools

The following tools are flagged as **High Risk** and are restricted or completely denied:

- `unsandboxed`: **DENIED**. All execution must pass through sandboxed shell environments.
- `chrome_devtools/*`: **ASK**. Web evaluations are isolated to headless testing containers.
- `mcp/*` (custom plugins): **ASK**. Loading new Model Context Protocol plugins requires user static analysis review.

---

## 📝 Terminal Command Prefix Whitelist

When utilizing the `run_command` tool, only the following command prefixes are authorized to execute synchronously without a warning threshold:

1. `echo` - Standard logging.
2. `date` - Timestamp auditing.
3. `git diff` / `git status` - Safe version control inspection.
4. `agy-node` - Local verified Node.js executor.

*Any command containing un-whitelisted executable binaries (e.g. `curl`, `wget`, `bash`, `ssh`, `cmd.exe`) will trigger a manual verification prompt.*
