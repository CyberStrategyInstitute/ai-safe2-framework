# Monitoring — Observability Stack

Real-time security telemetry for the Hermes Sovereign Runtime.

## Components

| File | Purpose |
|------|---------|
| `memory_auditor.py` | Continuous injection detection daemon — scans memory stores hourly |
| `prometheus.yml` | Scrape config for gateway, Hermes, Ishi, and OPA metrics |
| `alerts.yaml` | 17 Prometheus alert rules covering alignment, injection, credentials, and infrastructure |

## Quick Start

```bash
# Start full observability stack (included in docker-compose.yml)
docker-compose up -d prometheus grafana

# Grafana: http://localhost:3000 (admin / GRAFANA_PASSWORD from .env)
# Prometheus: http://localhost:9090

# Run memory auditor standalone
python3 monitoring/memory_auditor.py --watch --interval 3600

# Check for alerts firing
curl http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

## Alert Severity Reference

| Severity | Response Time | Action |
|----------|--------------|--------|
| `critical` | Immediate | Page on-call; consider kill switch |
| `warning` | Within 1 hour | Investigate; may not need kill switch |
| `info` | Next business day | Review audit log |

## Key Alerts

- `AlignmentRedBand` — Agent autonomy below safe threshold; operations suspended
- `PromptInjectionDetected` — Active injection attempt blocked
- `CredentialPatternInMemory` — CRITICAL: rotate immediately
- `GatewayDown` — Control plane offline; all requests unfiltered
- `KillSwitchActivated` — Operations suspended; manual intervention required
