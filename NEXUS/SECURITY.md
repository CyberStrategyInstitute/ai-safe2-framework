# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.3.x | Active security support |
| 0.2.x | Security patches only |
| < 0.2 | Not supported |

---

## Reporting a Vulnerability

**Do not report security vulnerabilities in public GitHub issues.**

NEXUS-A2A implements security-critical protocol primitives. A vulnerability
in the Guardian policy engine, CAEL envelope validation, Memory Vaccine, or
delegation chain enforcement could affect deployed agentic AI systems.

### Disclosure Channel

Email: **security@cyberstrategyinstitute.com**

PGP key: Available at https://cyberstrategyinstitute.com/.well-known/pgp

Response time: Initial acknowledgment within 24 hours.
Target resolution: 14 days for critical (CVSS 9.0+), 30 days for high.

### What to Include

- Protocol version or SDK version affected
- Description of the vulnerability
- Steps to reproduce or proof-of-concept code
- Affected controls (Guardian, Memory Vaccine, CAEL, delegation, etc.)
- Your assessment of exploitability
- Whether you have contacted any other party

### What We Commit To

- Acknowledge your report within 24 hours
- Keep you informed of our investigation timeline
- Credit you in the security advisory (unless you prefer anonymity)
- Not pursue legal action against good-faith security researchers
- Issue a CVE-tracked advisory for confirmed vulnerabilities affecting deployed systems

---

## Security Design Principles

NEXUS-A2A is designed with the following security assumptions:

1. **OPA runs outside the agent process.** An agent cannot read, modify, or override
   OPA policy decisions. This is a deployment requirement, not a code assertion.

2. **SPIFFE SVID provides workload attestation.** The security of L2 identity depends
   on a correctly configured SPIFFE/SPIRE deployment. Dev stub mode (no SPIRE)
   does not satisfy ACT-Tier 3+ requirements.

3. **Stub mode is not production mode.** `use_stub_embeddings=True` provides
   deterministic test results but does not catch novel ATPA patterns.
   Never deploy with stub mode in ACT-2+ environments.

4. **Kill switches require infrastructure.** The 500ms propagation guarantee
   requires a correctly deployed NEXUS gateway or equivalent. An SDK alone
   does not provide this.

5. **FAIL_CLOSED is the correct default.** Guardian failover should always be
   FAIL_CLOSED in production. FAIL_OPEN exists for specific use cases
   (development, non-critical pipelines) and is explicitly labeled dangerous
   in the SDK and documentation.

---

## Known Limitations (Not Vulnerabilities)

The following are documented design limitations, not security vulnerabilities:

- **Stub embeddings**: `use_stub_embeddings=True` uses deterministic hashing
  instead of real semantic embeddings. Novel adversarial steering that falls
  outside the 28 static injection pattern families will not be detected.

- **L6 self-evolution**: The cryptographic amendment pipeline is Phase 2 (2027).
  Protocol governance is currently manual.

- **NEXUS-Micro profile**: Edge agents in NEXUS-Micro mode defer mandate
  enforcement to the gateway. Gateway compromise cascades to edge agents.

---

## Acknowledgments

We thank the following researchers for responsible disclosures:
*(This section will be updated as disclosures are resolved.)*
