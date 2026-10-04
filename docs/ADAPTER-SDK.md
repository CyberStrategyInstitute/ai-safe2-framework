# Provider-Neutral Adapter SDK

AI SAFE² adapters translate attributed third-party evidence into a stable
exchange contract. They do not turn provider output into an AI SAFE² decision,
certification, or conformance claim.

```bash
safe2 adapter validate adapter.json
safe2 adapter conformance adapter.json evidence.json --output conformance.json
```

The first reference translator covers explicit Codex CLI JSONL exports. See the
[Codex JSONL Adapter](CODEX-JSONL-ADAPTER.md) for its command sequence, privacy
defaults, documented event surface, and evidence limitations.

For harness-neutral observability exchange, see
[OpenTelemetry Evidence Interoperability](OPENTELEMETRY-ADAPTER.md). It imports
OTLP/JSON TracesData into attributed aggregate evidence and exports only
non-content SAFE² metadata as OTLP LogsData.

An adapter descriptor declares its provider, version, evidence types, transport,
and privacy needs. Evidence supports harness, scanner, evaluator, ledger, usage,
and cloud providers. Every record preserves provider attribution, coverage gaps,
claim basis, provenance, and an `evidence_only` decision scope.

The conformance kit checks structural contracts plus cross-document invariants:
adapter and provider identity, declared evidence type, complete/partial/unavailable
coverage semantics, claim source references, and the prohibition on adapter-level
AI SAFE² conformance claims. It never executes the adapter or trusts the truth of
its payload.
