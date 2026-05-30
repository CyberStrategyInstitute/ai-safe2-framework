# Scripts — Operational Tooling

Production scripts for deploying, operating, and recovering a Hermes Sovereign Runtime.

## Scripts

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `pre-flight-check.sh` | 25-point deployment validation | Before every deployment, after any config change |
| `kill-switch.sh` | Immediate execution suspension | Active incident, suspected compromise |
| `rotate-credentials.sh` | Full credential rotation | Any credential exposure suspicion, every 30 days |
| `audit-report.sh` | Security audit report generator | Monthly, before compliance reviews, post-incident |

## Quick Reference

```bash
# Validate deployment is sovereign-runtime compliant
./scripts/pre-flight-check.sh

# Emergency: suspend all Hermes tool execution NOW
./scripts/kill-switch.sh

# Emergency: rotate all credentials immediately (no prompts)
./scripts/rotate-credentials.sh --emergency

# Generate monthly audit report
./scripts/audit-report.sh --output "reports/audit-$(date +%Y-%m).md"

# JSON audit report for SIEM integration
./scripts/audit-report.sh --json | curl -X POST https://your-siem/events -d @-
```

## Runbook: Incident Response Sequence

```
INCIDENT DETECTED
     ↓
1. KILL SWITCH:  ./scripts/kill-switch.sh
2. ASSESS:       ./scripts/audit-report.sh
3. ROTATE:       ./scripts/rotate-credentials.sh --emergency
4. VALIDATE:     ./scripts/pre-flight-check.sh
5. REVIVE:       curl -X POST http://localhost:8000/hsr/revive -H "X-Deactivation-Key: $KEY"
```

Full incident runbooks: [docs/INCIDENT-RESPONSE.md](../docs/INCIDENT-RESPONSE.md)

## Permissions

All scripts require execute permission:
```bash
chmod +x scripts/*.sh
```

Scripts must run as the same user that owns the Hermes process. Never run as root.
