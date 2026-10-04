# OpenTelemetry Evidence Interoperability

AI SAFE² can translate an explicit OpenTelemetry OTLP/JSON traces file into
provider-attributed evidence and export non-content evidence metadata as OTLP
LogsData. This lets existing observability systems exchange evidence with SAFE²
without replacing the user's agent harness.

```bash
safe2 adapter otel-jsonl agent-traces.jsonl \
  --otel-version YOUR_OTEL_VERSION --output otel-evidence.json
safe2 adapter otel-descriptor \
  --otel-version YOUR_OTEL_VERSION --output otel-adapter.json
safe2 adapter conformance otel-adapter.json otel-evidence.json \
  --output otel-conformance.json
safe2 adapter otel-export otel-evidence.json --output safe2-metadata.jsonl
```

The [OpenTelemetry file-exporter specification](https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/)
defines UTF-8 JSON Lines containing exactly one signal type encoded as OTLP JSON
and warns that records are not guaranteed to be ordered. This adapter therefore
aggregates trace batches without assuming chronological line order. It currently
accepts TracesData only; logs, metrics, and mixed signals fail closed.

The adapter uses GenAI semantic attributes for operation, provider, model, token
usage, and span status. Content-bearing attributes—including input/output
messages, system instructions, prompts, completions, retrieval text/documents,
and tool definitions—are excluded. Trace IDs, span IDs, span names, events, and
arbitrary attributes are not retained.

Imported counts remain provider-reported or observed telemetry evidence, not
proof that an operation occurred, succeeded, was authorized, or was billed as
reported. Export includes only SAFE² identity, status, decision scope, coverage
gap count, and source digest; it excludes claims, payloads, source paths, and
content. Neither direction makes a conformance or certification claim.
