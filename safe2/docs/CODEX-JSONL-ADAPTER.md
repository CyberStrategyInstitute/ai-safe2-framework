# Codex JSONL Evidence Adapter

The Codex reference adapter translates an explicitly supplied `codex exec --json`
trace into provider-attributed AI SAFE² evidence. It is offline, requires no
credentials, and does not read Codex session storage.

```bash
codex exec --json "run the approved task" > codex-trace.jsonl
safe2 adapter codex-jsonl codex-trace.jsonl \
  --codex-version YOUR_CODEX_VERSION \
  --output codex-evidence.json
safe2 adapter codex-descriptor \
  --codex-version YOUR_CODEX_VERSION \
  --output codex-adapter.json
safe2 adapter conformance codex-adapter.json codex-evidence.json \
  --output codex-conformance.json
```

The [official OpenAI documentation](https://developers.openai.com/blog/eval-skills)
documents `codex exec --json` as an ordered JSONL event stream, including
`item.started`, `item.completed`, command-execution items, and token usage in
`turn.completed` events. This adapter consumes only that documented surface.

## Privacy and evidence boundary

The output contains aggregate event, item, command-status, and token counts.
It never copies prompts, messages, reasoning, command strings, command output,
or arbitrary item bodies. The source filename and SHA-256 digest bind the result
to exact bytes without retaining an absolute local path.

Unknown event types or documented events with unmodeled shapes are counted as
explicit coverage gaps and produce `status: partial`; malformed, duplicate-key,
non-finite, oversized, blank-line, symlinked, and non-object inputs fail closed.
The adapter does not execute Codex, validate task success, independently verify
provider-reported usage, authorize an action, or claim AI SAFE² conformance.
