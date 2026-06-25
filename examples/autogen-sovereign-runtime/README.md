<div align="center">

# AutoGen 0.4 Sovereign Runtime
### AI SAFE² v3.0 Defense Package for AutoGen 0.4 (autogen_agentchat)

[![AI SAFE² v3.0](https://img.shields.io/badge/AI_SAFE²-v3.0-cc6600?style=for-the-badge&labelColor=black)](https://github.com/CyberStrategyInstitute/ai-safe2-framework)
[![Tests](https://img.shields.io/badge/Tests-15%2F15_passing-brightgreen?style=flat-square)](./smoke_test.py)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.4_only-blue?style=flat-square)](https://github.com/microsoft/autogen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

**Cyber Strategy Institute** · [cyberstrategyinstitute.com](https://cyberstrategyinstitute.com)

> **AutoGen 0.4 only.** 0.2 is end-of-life. If you're on 0.2, upgrade first.
> The API surface changed substantially; a 0.2 shim adds complexity without safety.

</div>

---

## This Is the Only Package in the Series With a Direct RCE Surface

Every other sovereign runtime package (LangChain, LangGraph, CrewAI, n8n) defends against prompt injection and data exfiltration. Important — but the worst case is a bad LLM response.

AutoGen's `CodeExecutorAgent` **actually runs code**. The worst case here is arbitrary code execution on your infrastructure.

```python
# What CodeExecutorAgent does without enforcement:
# LLM generates this → executor runs it → your files are gone
# rm -rf /home/user/production-data --no-preserve-root
```

**`CodeBlockGuard` is the primary defense.** It scans every code block before it reaches the executor. Code that fails the scan never runs — not after, before.

---

## Integration

```python
from enforcement import SovereignRuntime, ACTTier

sovereign = SovereignRuntime(act_tier=ACTTier.ACT3)

# Wrap AssistantAgent — message IPI scanning + NHI registration
assistant = sovereign.wrap_assistant(
    AssistantAgent("researcher", model_client=...),
    agent_id="researcher-prod-01",
)

# Wrap CodeExecutorAgent — MANDATORY, CP.8 required
# Never run a CodeExecutorAgent without this
executor = sovereign.wrap_code_executor(
    CodeExecutorAgent("executor", executor=LocalCommandLineCodeExecutor(...)),
    agent_id="executor-prod-01",
)

# Use normally in GroupChat
team = RoundRobinGroupChat([assistant, executor], termination_condition=...)
await team.run(task="Analyze the Q3 data and generate a report.")
```

---

## What Gets Blocked

### Python code blocks
| Pattern | Control | Severity |
|---|---|---|
| `eval(...)` | P1.T1.2 | CRITICAL |
| `exec(...)` | P1.T1.2 | CRITICAL |
| `__import__(...)` | P1.T1.2 | CRITICAL |
| `subprocess.run/Popen/call` | P1.T1.2 | CRITICAL |
| `os.system(...)` | P1.T1.2 | CRITICAL |
| `os.popen(...)` | P1.T1.2 | CRITICAL |
| `shutil.rmtree(...)` | P1.T1.2 | CRITICAL |

### Shell code blocks
| Pattern | Control | Severity |
|---|---|---|
| `rm -rf /...` | P1.T1.2 + CP.8 | FATAL |
| `sudo ...` | P1.T1.2 | CRITICAL |
| `curl ... \| bash` | P1.T1.2 | CRITICAL |
| `wget ... \| bash` | P1.T1.2 | CRITICAL |
| `kill -9 -1` | P1.T1.2 + CP.8 | FATAL |
| `dd if=/dev/zero of=/dev/sd*` | P1.T1.2 + CP.8 | FATAL |
| `shutdown -h now` | P1.T1.2 | CRITICAL |

CP.8 events are FATAL severity and reduce compliance score by 20 points regardless of whether the code is ultimately blocked.

---

## Async-First Architecture

All enforcement is async-native. Use `scan_message_content_async()` and `protect_code_block_async()` in async contexts:

```python
# In your async agent loop:
violation = await sovereign.scan_message_content_async(content, "tool_response")
if violation:
    raise AISAFE2Violation("Injection detected")

await sovereign.protect_code_block_async(code, "python")
# If this returns without raising, the code is safe to pass to the executor
```

---

## Control Coverage

| Control | Name | Enforcement Point |
|---|---|---|
| **P1.T1.2** | Malicious Prompt Filtering | `CodeBlockGuard.protect_code_block()` |
| **P1.T1.5** | Sensitive Data Masking | Message content credential scan |
| **P1.T1.10** | Indirect Injection Coverage | `SovereignAssistantProxy.on_messages()` |
| **P1.T2.3** | API Gateway Restrictions | Network patterns in code blocks |
| **S1.3** | Semantic Isolation Boundary | Message = untrusted data-plane |
| **S1.5** | Memory Governance | Agent state write governance |
| **F3.2** | Recursion Limit Governor | Message exchange ceiling |
| **F3.5** | Cascade Containment | Agent error isolation |
| **A2.5** | Execution Trace Logging | Per-message OCSF event |
| **M4.5** | Tool-Misuse Detection | Repeated message pattern detection |
| **P2.T3.6** | Compliance Validation | `compliance_report()` |
| **CP.3** | ACT Capability Tiers 1-4 | Constructor `act_tier` |
| **CP.4** | Agentic Control Plane | `register_nhi()` per agent |
| **CP.8** | Catastrophic Risk Threshold | **MANDATORY** for CodeExecutorAgent |
| **CP.10** | HEAR Doctrine | HEAR gate on Class-H code patterns |

---

*AI SAFE² v3.0 | Cyber Strategy Institute | cyberstrategyinstitute.com*
