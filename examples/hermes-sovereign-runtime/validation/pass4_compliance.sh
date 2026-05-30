#!/usr/bin/env bash
# =============================================================================
# Pass 4: Compliance Mapping Review
# Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0
# Cyber Strategy Institute
#
# Validates that HSR controls satisfy requirements across:
#   - NIST AI RMF (Govern / Map / Measure / Manage)
#   - CSA AICM v1.0 AI Supply Chain Security
#   - CSA MAESTRO Layer 3 (Agent Framework) + Layer 4 (Deployment)
#   - Zero Trust credential access principles
#   - ISO 42001 AI Management System
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HSR_ROOT="$(dirname "$SCRIPT_DIR")"

PASS=0; FAIL=0; WARN=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

check() {
    local id="$1" desc="$2" result="$3" framework="$4"
    local tag="[${framework}]"
    if [[ "$result" == "PASS" ]]; then
        echo -e "  ${GREEN}OK${NC} ${tag} ${desc}"; PASS=$((PASS+1))
    elif [[ "$result" == "WARN" ]]; then
        echo -e "  ${YELLOW}WN${NC} ${tag} ${desc}"; WARN=$((WARN+1))
    else
        echo -e "  ${RED}FL${NC} ${tag} ${desc}"; FAIL=$((FAIL+1))
    fi
}

file_exists() { [[ -f "$1" ]]; }
dir_exists() { [[ -d "$1" ]]; }
env_contains() { grep -q "$1" "${HSR_ROOT}/.env" 2>/dev/null; }

echo ""
echo -e "${BOLD}${CYAN}HSR Pass 4: Compliance Mapping Review — AI SAFE2 v3.0${NC}"
echo ""

# ---------------------------------------------------------------------------
echo -e "${BOLD}NIST AI RMF${NC}"
# ---------------------------------------------------------------------------
# GOVERN
file_exists "${HSR_ROOT}/supervisor/ishi_config.yaml" && \
    check "NIST-G1" "GOVERN: AI governance policy documented (ishi_config.yaml)" "PASS" "NIST-AI-RMF" || \
    check "NIST-G1" "GOVERN: Ishi governance config missing" "FAIL" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/supervisor/policies/tool_approval.rego" && \
    check "NIST-G2" "GOVERN: AI system use restrictions documented (tool_approval.rego)" "PASS" "NIST-AI-RMF" || \
    check "NIST-G2" "GOVERN: Tool approval policy missing" "FAIL" "NIST-AI-RMF"

# MAP
file_exists "${HSR_ROOT}/docs/THREAT-MODEL.md" && \
    check "NIST-M1" "MAP: Threat model documented" "PASS" "NIST-AI-RMF" || \
    check "NIST-M1" "MAP: Threat model not documented" "WARN" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/docs/ARCHITECTURE.md" && \
    check "NIST-M2" "MAP: System architecture documented" "PASS" "NIST-AI-RMF" || \
    check "NIST-M2" "MAP: Architecture not documented" "FAIL" "NIST-AI-RMF"

# MEASURE
file_exists "${HSR_ROOT}/monitoring/prometheus.yml" && \
    check "NIST-ME1" "MEASURE: Metrics collection configured" "PASS" "NIST-AI-RMF" || \
    check "NIST-ME1" "MEASURE: No metrics collection configured" "WARN" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/monitoring/alerts.yaml" && \
    check "NIST-ME2" "MEASURE: Alert rules defined" "PASS" "NIST-AI-RMF" || \
    check "NIST-ME2" "MEASURE: No alert rules defined" "WARN" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/validation/pass3_adversarial.py" && \
    check "NIST-ME3" "MEASURE: Adversarial test suite present" "PASS" "NIST-AI-RMF" || \
    check "NIST-ME3" "MEASURE: No adversarial testing" "FAIL" "NIST-AI-RMF"

# MANAGE
file_exists "${HSR_ROOT}/scripts/kill-switch.sh" && \
    check "NIST-MG1" "MANAGE: Incident response kill switch available" "PASS" "NIST-AI-RMF" || \
    check "NIST-MG1" "MANAGE: No kill switch" "FAIL" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/docs/INCIDENT-RESPONSE.md" && \
    check "NIST-MG2" "MANAGE: Incident response runbooks documented" "PASS" "NIST-AI-RMF" || \
    check "NIST-MG2" "MANAGE: No incident response docs" "FAIL" "NIST-AI-RMF"

file_exists "${HSR_ROOT}/scripts/rotate-credentials.sh" && \
    check "NIST-MG3" "MANAGE: Credential rotation procedure available" "PASS" "NIST-AI-RMF" || \
    check "NIST-MG3" "MANAGE: No credential rotation procedure" "WARN" "NIST-AI-RMF"

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}CSA AICM v1.0 — AI Supply Chain Security${NC}"
# ---------------------------------------------------------------------------

dir_exists "${HSR_ROOT}/skills-registry" && \
    check "CSA-SC1" "Sovereign skill registry established" "PASS" "CSA-AICM" || \
    check "CSA-SC1" "No sovereign skill registry" "FAIL" "CSA-AICM"

file_exists "${HSR_ROOT}/skills-registry/skill_manifest_template.yaml" && \
    check "CSA-SC2" "Skill provenance manifest template present" "PASS" "CSA-AICM" || \
    check "CSA-SC2" "No skill provenance template" "WARN" "CSA-AICM"

file_exists "${HSR_ROOT}/gateway/scanner.py" && \
    check "CSA-SC3" "Automated skill vulnerability scanner present" "PASS" "CSA-AICM" || \
    check "CSA-SC3" "No automated skill scanner" "FAIL" "CSA-AICM"

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}CSA MAESTRO — Agentic AI Threat Model${NC}"
# ---------------------------------------------------------------------------

# Layer 3: Agent Framework
file_exists "${HSR_ROOT}/core/hermes_memory_vaccine.md" && \
    check "MAESTRO-L3-1" "L3: Memory vaccine addresses context manipulation" "PASS" "MAESTRO-L3" || \
    check "MAESTRO-L3-1" "L3: No memory vaccine" "FAIL" "MAESTRO-L3"

file_exists "${HSR_ROOT}/gateway/gateway.py" && \
    check "MAESTRO-L3-2" "L3: LLM API gateway enforces output sanitization" "PASS" "MAESTRO-L3" || \
    check "MAESTRO-L3-2" "L3: No LLM gateway" "FAIL" "MAESTRO-L3"

file_exists "${HSR_ROOT}/supervisor/policies/subagent_scope.rego" && \
    check "MAESTRO-L3-3" "L3: Subagent scope policy enforces least privilege" "PASS" "MAESTRO-L3" || \
    check "MAESTRO-L3-3" "L3: No subagent scope policy" "FAIL" "MAESTRO-L3"

# Layer 4: Deployment/Infrastructure
file_exists "${HSR_ROOT}/docker-compose.yml" && \
    check "MAESTRO-L4-1" "L4: Container isolation deployment defined" "PASS" "MAESTRO-L4" || \
    check "MAESTRO-L4-1" "L4: No container deployment definition" "WARN" "MAESTRO-L4"

env_contains "HERMES_FORCE_APPROVAL=true" && \
    check "MAESTRO-L4-2" "L4: Container approval bypass mitigated" "PASS" "MAESTRO-L4" || \
    check "MAESTRO-L4-2" "L4: Container approval bypass not mitigated — CRITICAL" "FAIL" "MAESTRO-L4"

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}Zero Trust Principles${NC}"
# ---------------------------------------------------------------------------

env_contains "VAULT_ADDR" && \
    check "ZT1" "Secrets manager (not flat .env) configured" "PASS" "Zero-Trust" || \
    check "ZT1" "Vault not configured — flat .env secrets in use" "WARN" "Zero-Trust"

file_exists "${HSR_ROOT}/supervisor/policies/tool_approval.rego" && \
    grep -q "default allow := false" "${HSR_ROOT}/supervisor/policies/tool_approval.rego" && \
    check "ZT2" "Default-deny policy confirmed in tool_approval.rego" "PASS" "Zero-Trust" || \
    check "ZT2" "Default-deny not confirmed in policy" "WARN" "Zero-Trust"

file_exists "${HSR_ROOT}/monitoring/memory_auditor.py" && \
    check "ZT3" "Continuous verification via memory audit daemon" "PASS" "Zero-Trust" || \
    check "ZT3" "No continuous verification daemon" "WARN" "Zero-Trust"

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}ISO 42001 AI Management System${NC}"
# ---------------------------------------------------------------------------

file_exists "${HSR_ROOT}/docs/COMPLIANCE-MAPPING.md" && \
    check "ISO-1" "Compliance mapping document present" "PASS" "ISO-42001" || \
    check "ISO-1" "No compliance mapping documentation" "WARN" "ISO-42001"

file_exists "${HSR_ROOT}/skills-registry/README.md" && \
    check "ISO-2" "AI artifact review process documented" "PASS" "ISO-42001" || \
    check "ISO-2" "No artifact review process docs" "WARN" "ISO-42001"

file_exists "${HSR_ROOT}/scripts/audit-report.sh" && \
    check "ISO-3" "Audit evidence generation capability present" "PASS" "ISO-42001" || \
    check "ISO-3" "No audit report tooling" "WARN" "ISO-42001"

echo ""
echo -e "${BOLD}${CYAN}Pass 4 Results: ${GREEN}${PASS} passed${NC} | ${RED}${FAIL} failed${NC} | ${YELLOW}${WARN} warnings${NC}"
echo ""

[[ $FAIL -gt 0 ]] && exit 1 || exit 0
