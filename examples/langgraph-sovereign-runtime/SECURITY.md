# Security Policy — LangChain Sovereign Runtime

**AI SAFE² v3.0 | Cyber Strategy Institute**

---

## Supported Versions

| Version | Supported |
|---|---|
| AI SAFE² v3.0 (current) | ✅ Active |
| AI SAFE² v2.1 | Security patches only |
| AI SAFE² v2.0 and below | ❌ End of life |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities privately to:

- **Email:** security@cyberstrategyinstitute.com
- **Subject:** `[VULN] langchain-sovereign-runtime — <brief description>`
- **PGP:** Available at [cyberstrategyinstitute.com/pgp](https://cyberstrategyinstitute.com)

### What to include

1. Control ID affected (e.g., P1.T1.2) — if known
2. Steps to reproduce (minimum reproducible example)
3. Impact assessment: which control is bypassed, what attacker capability it enables
4. Suggested fix — if you have one

---

## Severity Classification

We classify AI SAFE² vulnerabilities using AI SAFE² v3.0 severity levels:

| Level | Criteria | Response SLA |
|---|---|---|
| **FATAL** | CP.8 threshold — allows full control-plane bypass or agent replication without governance | 24 hours |
| **CRITICAL** | Bypasses P1.T1.2, P1.T1.10, CP.10 HEAR, or F3.2 hard ceiling | 48 hours |
| **HIGH** | Bypasses P1.T1.5 masking, S1.5 memory governance, or F3.5 cascade containment | 5 days |
| **MEDIUM** | Audit log manipulation, false-positive DoS on legitimate inputs | 14 days |
| **LOW** | Documentation error, misconfiguration risk | 30 days |

---

## What Is In Scope

- Injection patterns in `ai_safe2_engine.py` that can be bypassed with real-world payloads
- Logic errors in ACT tier enforcement (ACT-3 behaving as ACT-1)
- SHA-256 chain manipulation allowing audit log tampering
- CP.10 HEAR gate bypass
- False positive rate exceeding 0.1% on common legitimate inputs

## What Is Out of Scope

- The underlying LangChain library itself (report to langchain-ai/langchain)
- LLM model behavior
- Issues requiring physical access to the host

---

## Disclosure Timeline

1. **Day 0:** Vulnerability reported privately
2. **Day 1-2:** Acknowledgment and severity assessment
3. **Day 3-14:** Fix developed and tested
4. **Day 14-30:** Patch released with CVE request if warranted
5. **Day 30+:** Public disclosure with researcher credit (if desired)

---

*AI SAFE² v3.0 | Cyber Strategy Institute | security@cyberstrategyinstitute.com*
