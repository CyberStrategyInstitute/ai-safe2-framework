# Code Executor Safety Guide — AI SAFE² v3.0

## Never Run CodeExecutorAgent Without sovereign.wrap_code_executor()

```python
# WRONG — unprotected code execution
executor = CodeExecutorAgent("executor", executor=LocalCommandLineCodeExecutor(...))
team = RoundRobinGroupChat([assistant, executor])

# RIGHT — always wrap first
executor = sovereign.wrap_code_executor(
    CodeExecutorAgent("executor", executor=LocalCommandLineCodeExecutor(...)),
    agent_id="executor-prod-01",
)
team = RoundRobinGroupChat([assistant, executor])
```

## Docker vs Local Execution

| Mode | Risk | Recommendation |
|---|---|---|
| `DockerCommandLineCodeExecutor` | Medium | Default for production |
| `LocalCommandLineCodeExecutor` | High | Dev/test only |
| No executor | N/A | Use if no code execution needed |

Even with Docker, `CodeBlockGuard` still scans before execution.
Defense in depth: don't rely on container isolation alone.

## Code Block Languages Scanned

| Language | Python Dangerous | Shell Dangerous | Network Patterns |
|---|---|---|---|
| `python` / `py` | ✅ | | ✅ |
| `bash` / `sh` / `shell` | | ✅ | |
| `zsh` / `fish` | | ✅ | |
| Unknown | ✅ | ✅ | ✅ |

## What CodeBlockGuard Does NOT Block

- Pure data manipulation (pandas, numpy, etc.) — no dangerous patterns
- File reads (`open(..., 'r')`) — reads are not flagged
- Standard print/return statements
- Math operations, string formatting, list comprehensions

The guard targets execution surfaces, not data processing.

## ACT Tier Behavior for Code

| ACT Tier | Dangerous patterns | Catastrophic patterns |
|---|---|---|
| ACT-1 | Log only | CP.8 event + log |
| ACT-2 | Log + CP.8 catastrophic blocks | CP.8 event + BLOCK |
| ACT-3 | Block all dangerous | CP.8 event + BLOCK |
| ACT-4 | Block all dangerous + HEAR | CP.8 event + BLOCK + HEAR |
