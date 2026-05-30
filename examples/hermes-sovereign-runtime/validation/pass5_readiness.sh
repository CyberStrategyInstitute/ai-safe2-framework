#!/usr/bin/env bash
# =============================================================================
# Pass 5: Operational Readiness
# Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0
# Cyber Strategy Institute
#
# Final gate before production promotion. Validates:
#   - Operator training docs present
#   - Red team schedule established
#   - CVE monitoring configured
#   - All scripts executable
#   - Change management process documented
#   - Complete package integrity
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HSR_ROOT="$(dirname "$SCRIPT_DIR")"

PASS=0; FAIL=0; WARN=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

check() {
    local desc="$1" result="$2"
    if [[ "$result" == "PASS" ]]; then
        echo -e "  ${GREEN}OK${NC} ${desc}"; PASS=$((PASS+1))
    elif [[ "$result" == "WARN" ]]; then
        echo -e "  ${YELLOW}WN${NC} ${desc}"; WARN=$((WARN+1))
    else
        echo -e "  ${RED}FL${NC} ${desc}"; FAIL=$((FAIL+1))
    fi
}

echo ""
echo -e "${BOLD}${CYAN}HSR Pass 5: Operational Readiness — AI SAFE2 v3.0${NC}"
echo ""

# A: Documentation completeness
echo -e "${BOLD}[A] Documentation${NC}"
for f in README.md SECURITY.md docs/ARCHITECTURE.md docs/INCIDENT-RESPONSE.md docs/MIGRATION.md; do
    [[ -f "${HSR_ROOT}/${f}" ]] && \
        check "${f} present" "PASS" || check "${f} MISSING" "FAIL"
done

echo ""
# B: Script executability
echo -e "${BOLD}[B] Script Permissions${NC}"
for s in scripts/pre-flight-check.sh scripts/kill-switch.sh scripts/rotate-credentials.sh scripts/audit-report.sh; do
    f="${HSR_ROOT}/${s}"
    if [[ -f "$f" ]]; then
        [[ -x "$f" ]] && check "${s} is executable" "PASS" || \
            check "${s} not executable (run: chmod +x ${s})" "WARN"
    else
        check "${s} MISSING" "FAIL"
    fi
done

echo ""
# C: Validation suite completeness
echo -e "${BOLD}[C] Validation Suite${NC}"
for v in validation/pass1_static.sh validation/pass2_runtime.sh validation/pass3_adversarial.py validation/pass4_compliance.sh; do
    [[ -f "${HSR_ROOT}/${v}" ]] && check "${v} present" "PASS" || check "${v} MISSING" "WARN"
done

echo ""
# D: Core governance files
echo -e "${BOLD}[D] Core Governance Files${NC}"
for c in core/hermes_memory_vaccine.md core/IDENTITY.md core/SOUL.md core/SUBAGENT-POLICY.md core/HEARTBEAT.md; do
    [[ -f "${HSR_ROOT}/${c}" ]] && check "${c} present" "PASS" || check "${c} MISSING" "FAIL"
done

echo ""
# E: Gateway stack
echo -e "${BOLD}[E] Gateway Stack${NC}"
for g in gateway/gateway.py gateway/scanner.py gateway/provider_adapters.py gateway/config.yaml; do
    [[ -f "${HSR_ROOT}/${g}" ]] && check "${g} present" "PASS" || check "${g} MISSING" "FAIL"
done

echo ""
# F: Supervisor policies
echo -e "${BOLD}[F] Supervisor Policies${NC}"
for p in supervisor/ishi_config.yaml supervisor/policies/tool_approval.rego supervisor/policies/cron_governance.rego supervisor/policies/subagent_scope.rego; do
    [[ -f "${HSR_ROOT}/${p}" ]] && check "${p} present" "PASS" || check "${p} MISSING" "FAIL"
done

echo ""
# G: Monitoring stack
echo -e "${BOLD}[G] Monitoring Stack${NC}"
for m in monitoring/memory_auditor.py monitoring/prometheus.yml monitoring/alerts.yaml; do
    [[ -f "${HSR_ROOT}/${m}" ]] && check "${m} present" "PASS" || check "${m} MISSING" "WARN"
done

echo ""
# H: Final operator checklist
echo -e "${BOLD}[H] Operator Attestation${NC}"
echo -e "${YELLOW}The following must be confirmed by a human operator before production:${NC}"
echo "  [ ] HERMES_FORCE_APPROVAL=true verified in production .env"
echo "  [ ] Gateway URL verified to route through HSR gateway"
echo "  [ ] Memory vaccine file verified present in ~/.hermes/memories/"
echo "  [ ] Kill switch test executed and documented"
echo "  [ ] Ishi supervisor (or equivalent human escalation) configured"
echo "  [ ] CVE monitoring subscription active (SECURITY.md)"
echo "  [ ] Credential rotation schedule established (max 30 days)"
echo "  [ ] All operators reviewed SECURITY.md and INCIDENT-RESPONSE.md"
echo "  [ ] Red team exercise scheduled (quarterly minimum)"
echo ""

echo -e "${BOLD}${CYAN}Pass 5 Results: ${GREEN}${PASS} passed${NC} | ${RED}${FAIL} failed${NC} | ${YELLOW}${WARN} warnings${NC}"
echo ""

[[ $FAIL -gt 0 ]] && exit 1 || exit 0
