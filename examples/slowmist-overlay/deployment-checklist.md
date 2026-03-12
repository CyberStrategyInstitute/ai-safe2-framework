# Deployment Checklist: Adding AI SAFE² to an Existing SlowMist Deployment

> **Use this checklist** if you have already applied (or are currently applying) the SlowMist OpenClaw Security Practice Guide v2.7 and want to add the AI SAFE² Framework's external enforcement layer.
> 
> If you are starting from scratch, complete the SlowMist guide first, then return here.

---

## Phase 0 — Baseline Assessment (Before Adding Anything)

- [ ] Confirm SlowMist deployment status: red/yellow lines active, skill installation audit protocol in place, nightly cron running and pushing successfully
- [ ] Run `scanner.py` against your OpenClaw data directory — record the baseline risk score
- [ ] Resolve all CRITICAL (red) scanner findings before proceeding
- [ ] Document your current skill inventory (names, versions, install dates, approval records)
- [ ] Identify all humans who have access to the OpenClaw host and its credentials

---

## Phase 1 — Cognitive Layer (Memory Vaccine)

- [ ] Download `openclaw_memory.md` from `examples/openclaw/` in the AI SAFE² repo
- [ ] Copy to `~/.openclaw/workspace/`
- [ ] In OpenClaw chat: "Please load and prioritize the security context in `openclaw_memory.md`. Confirm when loaded."
- [ ] Verify: ask OpenClaw "What are your top three security priorities?" — response should reflect Memory Vaccine directives
- [ ] Run SlowMist's cognitive injection red-team test (hidden instruction injection) — confirm OpenClaw refuses
- [ ] Document Memory Vaccine version and load date in your deployment log

---

## Phase 2 — API Gateway Layer (Control Gateway)

- [ ] Review `gateway/README.md` for configuration options
- [ ] Configure gateway with your LLM provider API endpoint
- [ ] Set risk score thresholds appropriate to your risk tolerance (default: block at ≥8/10)
- [ ] Configure audit log destination (local path + optional remote aggregation)
- [ ] Point OpenClaw's API calls through the gateway
- [ ] Verify: run a yellow-line operation (e.g., a `sudo` command) — confirm gateway logs the request and routes for human approval
- [ ] Verify: attempt a known prompt injection payload — confirm gateway blocks it
- [ ] Enable circuit-breaker configuration for automated halts
- [ ] Document gateway version, config hash, and deployment date

---

## Phase 3 — Scanner Integration (Recurring Audit)

- [ ] Add `scanner.py` execution to SlowMist's nightly audit cron (or as a separate parallel cron)
- [ ] Route scanner output to `/tmp/openclaw/security-reports/scanner-$(date +%Y-%m-%d).txt`
- [ ] Include scanner summary in SlowMist's push notification report (add a "14th metric" to the daily brief)
- [ ] Set up scanner risk score trending (track score week-over-week; alert on increases ≥10 points)
- [ ] Run scanner after every new skill installation (in addition to nightly)
- [ ] Document scanner integration in your deployment runbook

---

## Phase 4 — Organizational Controls

- [ ] Create a centralized deployment registry: document every OpenClaw instance, host, privilege level, installed skills, and responsible operator
- [ ] Route all nightly audit reports and Gateway logs to a centralized log store (private repo, SIEM, or log aggregation service)
- [ ] Define escalation contacts for CRITICAL findings: who gets paged, in what order, within what SLA
- [ ] Implement credential rotation schedule: API keys, OAuth tokens, and backup repo credentials on defined intervals
- [ ] Document the process for adding or removing an OpenClaw deployment from the registry

---

## Phase 5 — Red-Team Validation

- [ ] Schedule initial red-team exercise using SlowMist's Validation Guide as curriculum (see `red-team-schedule.md`)
- [ ] Test in an isolated environment — never against production memory state
- [ ] Validate all three defense tiers: Memory Vaccine (cognitive layer), Gateway (API layer), SlowMist matrix (host layer)
- [ ] Document results and remediate any failures before declaring the deployment production-ready
- [ ] Add red-team exercises to the organizational calendar (quarterly minimum)

---

## Ongoing Maintenance

| Task | Frequency | Owner |
|---|---|---|
| Review nightly audit + scanner report | Daily | Operator |
| Review Gateway audit logs for anomalies | Weekly | Operator |
| Check skill baseline against approved inventory | Weekly | Operator |
| Run Scanner manually after any skill install | Per event | Operator |
| Red-team exercise (SlowMist curriculum) | Quarterly | Security team |
| Memory Vaccine review + update | On SlowMist guide update | Security team |
| Gateway config review | On OpenClaw major release | Security team |
| Deployment registry audit | Semi-annual | Security lead |
| Threat model review | Annual | Security lead |

---

*Cross-reference: [`README.md`](./README.md) | [`safe2-for-slowmist-overlay.md`](./safe2-for-slowmist-overlay.md)*
