# Compliance Mapping
**Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0**
**Cyber Strategy Institute**

This document maps HSR controls to applicable compliance frameworks. Use it to demonstrate control coverage during audits, vendor assessments, and enterprise procurement reviews.

---

## Framework Coverage Matrix

| Framework | Coverage | Evidence Location |
|-----------|---------|------------------|
| NIST AI RMF (2023) | Govern, Map, Measure, Manage | This document + audit logs |
| CSA AICM v1.0 | AI Supply Chain, Deployment, Runtime | supervisor/, gateway/, skills-registry/ |
| CSA MAESTRO | Layer 3 (Agent Framework), Layer 4 (Deployment) | docs/THREAT-MODEL.md |
| ISO 42001:2023 | Clauses 6 (Planning), 8 (Operation), 10 (Improvement) | This document |
| NIST SP 800-207 (Zero Trust) | Pillars 1-4 | .env, vault config, ishi_config.yaml |
| OWASP LLM Top 10 | LLM01-LLM09 | gateway/gateway.py, core/hermes_memory_vaccine.md |
| CMMC 2.0 Level 2 | AU, CM, IA, IR, SC | monitoring/, scripts/, docs/ |

---

## NIST AI RMF Mapping

### GOVERN Function

| GOVERN Control | HSR Implementation | File |
|---------------|-------------------|------|
| GV-1.1: AI risk management policies documented | Ishi supervisor policy | supervisor/ishi_config.yaml |
| GV-1.2: Roles and responsibilities defined | Ten expert domain model | docs/ARCHITECTURE.md |
| GV-2.1: AI risk tolerances established | Alignment band thresholds (Green/Yellow/Red) | supervisor/ishi_config.yaml |
| GV-4.1: Organizational policies applied to AI | Tool approval policy (default deny) | supervisor/policies/tool_approval.rego |
| GV-5.2: AI practices monitored | Prometheus + alert rules | monitoring/prometheus.yml, alerts.yaml |
| GV-6.1: Policies for transparency | Audit trail with HMAC chaining | gateway/gateway.py |

### MAP Function

| MAP Control | HSR Implementation | File |
|------------|-------------------|------|
| MP-1.1: Context of AI deployment documented | Architecture + threat model | docs/ARCHITECTURE.md, docs/THREAT-MODEL.md |
| MP-2.1: Scientific evidence for AI behavior | Love Equation mathematical model | core/SOUL.md |
| MP-3.1: AI system categorized by risk | ACT Capability Tier classification | docs/ARCHITECTURE.md |
| MP-4.1: Risks mapped across lifecycle | Risk register with CVSS scores | docs/THREAT-MODEL.md |
| MP-5.1: Likelihood and impact assessed | Risk register table | docs/THREAT-MODEL.md |

### MEASURE Function

| MEASURE Control | HSR Implementation | File |
|----------------|-------------------|------|
| MS-1.1: Methods to test AI risks documented | 5-pass validation framework | validation/ |
| MS-2.1: AI systems tested for risks | Adversarial red team suite | validation/pass3_adversarial.py |
| MS-2.5: Privacy risks measured | PII filtering + memory encryption | gateway/gateway.py |
| MS-2.6: Security risks measured | Vulnerability scanner | gateway/scanner.py |
| MS-2.7: Bias and fairness measured | Alignment monitoring | monitoring/prometheus.yml |
| MS-4.1: Measurement results tracked | Audit log + metrics | gateway/gateway.py, monitoring/ |

### MANAGE Function

| MANAGE Control | HSR Implementation | File |
|---------------|-------------------|------|
| MG-1.1: AI risks prioritized | Severity-ranked risk register | docs/THREAT-MODEL.md |
| MG-2.2: Mechanisms for AI to be overridden | Kill switch + HITL gates | scripts/kill-switch.sh |
| MG-2.4: Incident response plans documented | 7 incident runbooks | docs/INCIDENT-RESPONSE.md |
| MG-3.1: Risks tracked over time | Rotating audit reports | scripts/audit-report.sh |
| MG-4.1: Deployed AI monitored | Memory auditor + Prometheus | monitoring/ |

---

## OWASP LLM Top 10 Mapping

| OWASP LLM Risk | HSR Control |
|---------------|------------|
| LLM01: Prompt Injection | Gateway injection pattern blocking (8 signatures); memory vaccine; taint-tracking |
| LLM02: Insecure Output Handling | Gateway output sanitization; PII and secret pattern blocking on responses |
| LLM03: Training Data Poisoning | Memory isolation; vaccine prevents persistent adversarial writes |
| LLM04: Model Denial of Service | Max request size limits (32KB) in gateway config |
| LLM05: Supply Chain Vulnerabilities | Sovereign skills registry; scanner.py supply chain analysis |
| LLM06: Sensitive Information Disclosure | Gateway secret pattern blocking; HERMES_READ_SAFE_ROOT enforcement |
| LLM07: Insecure Plugin Design | Signed plugin requirement; plugin code review gate |
| LLM08: Excessive Agency | Tool allowlist; Ishi approval gates; subagent scope limits |
| LLM09: Overreliance | Ishi HITL gates; kill switch for suspension |
| LLM10: Model Theft | Credential scoping; ephemeral Vault tokens |

---

## CSA MAESTRO Layer Mapping

### Layer 3 — Agent Framework

| Threat | HSR Mitigation |
|--------|---------------|
| Prompt injection via tool outputs | Taint-tracking on all external input surfaces |
| Memory poisoning | Memory vaccine + hourly audit scan |
| Skill supply chain compromise | Sovereign registry + scanner.py |
| LLM jailbreak | Identity anchor (IDENTITY.md) + SOUL.md alignment |

### Layer 4 — Deployment/Infrastructure

| Threat | HSR Mitigation |
|--------|---------------|
| Container privilege escalation | gVisor (runsc) + no-new-privileges + cap_drop ALL |
| API key exfiltration | Gateway secret blocking + Vault ephemeral tokens |
| Approval gate bypass | HERMES_FORCE_APPROVAL=true override |
| Unattended automation risk | Ishi cron governance + cron_governance.rego |

---

## CMMC 2.0 Level 2 Domain Mapping

| Domain | Control | HSR Implementation |
|--------|---------|------------------|
| AU (Audit) | AU.2.041 | Append-only audit log with HMAC chaining |
| AU (Audit) | AU.2.042 | Audit trail covers all tool calls with parameters |
| CM (Config Mgmt) | CM.2.061 | Baseline config in docker-compose.yml + .env.example |
| CM (Config Mgmt) | CM.2.064 | Security configuration settings enforced via OPA policies |
| IA (Identification) | IA.3.083 | NHI inventory; Vault-issued ephemeral identity tokens |
| IR (Incident Response) | IR.2.092 | 7 incident runbooks in docs/INCIDENT-RESPONSE.md |
| IR (Incident Response) | IR.2.093 | Kill switch enables immediate incident containment |
| SC (System Comms) | SC.3.177 | Internal-only Docker network; no direct agent egress |
| SC (System Comms) | SC.3.187 | Vault manages cryptographic key material |

---

## Evidence Collection for Audits

Run the following to generate audit evidence packages:

```bash
# Generate compliance report
./scripts/audit-report.sh --output "evidence/compliance-$(date +%Y-%m).md"

# Run full validation suite
./validation/pass1_static.sh  > evidence/pass1.log 2>&1
./validation/pass4_compliance.sh > evidence/pass4.log 2>&1

# Export gateway metrics snapshot
curl http://localhost:8000/hsr/metrics > evidence/gateway-metrics-$(date +%Y-%m-%d).txt

# Export audit log
curl http://localhost:8000/hsr/audit/tail > evidence/audit-log-$(date +%Y-%m-%d).jsonl
```

---

*Compliance mapping version: 1.0 | AI SAFE² v3.0 | Cyber Strategy Institute*
