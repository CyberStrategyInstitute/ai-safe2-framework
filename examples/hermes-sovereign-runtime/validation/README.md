# HSR Validation Suite — 5-Pass QA
### Hermes Sovereign Runtime · AI SAFE² v3.0

---

## Overview

The five-pass validation suite verifies sovereign runtime deployment before
production promotion and after any configuration change. Each pass has a clear
pass/fail gate.

**Rule:** Do not promote to production until all five passes complete with zero
critical failures.

---

## Pass 1 — Static Configuration Review

**Who:** Expert L9 (QA) + Expert L2 (Security Engineer)
**When:** Before first deploy; after any configuration change

```bash
bash validation/pass1_static.sh
```

Checks:
- HERMES_FORCE_APPROVAL=true present (Critical audit finding override)
- --yolo absent from all production entrypoints
- HERMES_READ_SAFE_ROOT configured
- ANTHROPIC_BASE_URL routing through gateway
- .env permissions are 0600
- hermes-webui ≥ v0.50.34 (CVE-2026-6829)
- WeChat Work adapter disabled (CVE-2026-7396)
- All git dependencies pinned to commit SHAs
- Core governance files present
- Vaccine file loads at highest memory priority

**Exit codes:** 0 = pass | 1 = warnings | 2 = critical failures (do not deploy)

---

## Pass 2 — Runtime Behavior Validation

**Who:** Expert L9 + Expert L7 (Threat Intel)
**When:** After deploy; after gateway restart

```bash
bash validation/pass2_runtime.sh
```

Checks:
- Memory vaccine confirmed loaded (`hermes status --memory`)
- Gateway PII filter: test SSN pattern → expect 403
- Gateway secrets filter: test API key pattern → expect 403
- Tool allowlist: test blocked tool → expect 403 + audit log entry
- Kill switch: verify endpoint responsive
- Container approval flow: confirm approval gate active in Docker

**Requires:** Gateway running on 127.0.0.1:8000

---

## Pass 3 — Adversarial Red Team

**Who:** Expert L7 + Expert L9
**When:** Before first production use; quarterly thereafter

```bash
python3 validation/pass3_adversarial.py
```

10 adversarial test cases:
1. Anthropic API key exfiltration attempt
2. AWS access key exfiltration attempt
3. PEM private key exfiltration attempt
4. "Ignore instructions" injection pattern
5. Identity replacement injection
6. Developer mode injection
7. Oversized context window attack
8. Kill switch endpoint responsiveness
9. Audit log integrity check
10. SSN/PII block verification

**Requires:** Gateway running. Does NOT require Hermes running.

---

## Pass 4 — Compliance Mapping Review

**Who:** Expert L3 (Safety/Governance) + Expert L6 (Compliance)
**When:** Before production; quarterly; before any compliance audit

```bash
bash validation/pass4_compliance.sh
```

Verifies:
- All controls mapped to NIST AI RMF govern/map/measure/manage functions
- AICM v1.0 AI Supply Chain domain controls documented and tested
- MAESTRO Layer 3 + Layer 4 threat chains addressed
- Audit trail integrity: append-only with hash verification
- NHI inventory: all Hermes instances registered

---

## Pass 5 — Operational Readiness

**Who:** Expert L10 (DevEx) + Expert L1 (Orchestration)
**When:** Before going live

```bash
bash validation/pass5_readiness.sh
```

Verifies:
- Operator training completed
- Red-team exercise schedule established
- CVE monitoring subscription active
- Incident response runbooks accessible
- Cron automation reviewed and Ishi-approved
- Change management process active
- Kill switch tested (actual activation + deactivation)

---

## Quick Reference

```bash
# Full validation sequence
bash scripts/pre-flight-check.sh          # Pre-deploy gate
docker compose up -d                      # Deploy
bash validation/pass1_static.sh           # Static review
bash validation/pass2_runtime.sh          # Runtime validation
python3 validation/pass3_adversarial.py   # Red team
bash validation/pass4_compliance.sh       # Compliance review
bash validation/pass5_readiness.sh        # Operational readiness

# Ongoing
python3 gateway/scanner.py --watch &      # Continuous skill/memory scanning
python3 monitoring/memory_auditor.py --watch &  # Continuous memory audit
```

---

*HSR Validation Suite · Cyber Strategy Institute · AI SAFE² v3.0*
