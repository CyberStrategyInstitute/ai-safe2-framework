#!/usr/bin/env bash
# =============================================================================
# Pass 1: Static Configuration Review
# Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0
# Cyber Strategy Institute
#
# SCOPE: File-system and configuration validation. No network calls, no
# container interaction. Safe to run before any services are up.
#
# Validates:
#   - .env critical variable presence
#   - File permissions (0600 for secrets)
#   - Vaccine file placement
#   - Docker Compose critical settings
#   - Dependency pinning
#   - CVE mitigation flags
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HSR_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${HSR_ROOT}/.env"

PASS=0; FAIL=0; WARN=0
PASS_RESULTS=()
FAIL_RESULTS=()
WARN_RESULTS=()

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

check() {
    local id="$1" desc="$2" result="$3" severity="${4:-fail}"
    if [[ "$result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓${NC} [${id}] ${desc}"
        PASS=$((PASS + 1))
        PASS_RESULTS+=("${id}: ${desc}")
    elif [[ "$result" == "WARN" ]]; then
        echo -e "  ${YELLOW}⚠${NC} [${id}] ${desc}"
        WARN=$((WARN + 1))
        WARN_RESULTS+=("${id}: ${desc}")
    else
        echo -e "  ${RED}✗${NC} [${id}] ${desc}"
        FAIL=$((FAIL + 1))
        FAIL_RESULTS+=("${id}: ${desc}")
    fi
}

env_var_set() {
    grep -q "^${1}=" "${ENV_FILE}" 2>/dev/null && \
    [[ "$(grep "^${1}=" "${ENV_FILE}" | cut -d'=' -f2-)" != "" ]] && \
    [[ "$(grep "^${1}=" "${ENV_FILE}" | cut -d'=' -f2-)" != '""' ]] && \
    [[ "$(grep "^${1}=" "${ENV_FILE}" | cut -d'=' -f2-)" != "your-*" ]]
}

env_var_value() {
    grep "^${1}=" "${ENV_FILE}" 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo ""
}

echo ""
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  HSR Pass 1: Static Configuration Review${NC}"
echo -e "${BOLD}${CYAN}  AI SAFE² v3.0 | Cyber Strategy Institute${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# ---------------------------------------------------------------------------
echo -e "${BOLD}[A] Environment File Validation${NC}"
# ---------------------------------------------------------------------------

# A1: .env exists
if [[ -f "$ENV_FILE" ]]; then
    check "A1" ".env file exists" "PASS"
else
    check "A1" ".env file exists — copy from .env.example and configure" "FAIL"
fi

# A2: .env permissions
if [[ -f "$ENV_FILE" ]]; then
    perms=$(stat -c "%a" "$ENV_FILE" 2>/dev/null || stat -f "%Lp" "$ENV_FILE" 2>/dev/null || echo "000")
    [[ "$perms" == "600" ]] && \
        check "A2" ".env permissions are 0600" "PASS" || \
        check "A2" ".env permissions are ${perms} (must be 0600: chmod 600 .env)" "FAIL"
fi

# A3: HERMES_FORCE_APPROVAL=true (Critical container bypass mitigation)
if env_var_set "HERMES_FORCE_APPROVAL" && [[ "$(env_var_value HERMES_FORCE_APPROVAL)" == "true" ]]; then
    check "A3" "HERMES_FORCE_APPROVAL=true (container bypass mitigated)" "PASS"
else
    check "A3" "HERMES_FORCE_APPROVAL not set to true — CRITICAL: container approval bypass active" "FAIL"
fi

# A4: HERMES_READ_SAFE_ROOT set
env_var_set "HERMES_READ_SAFE_ROOT" && \
    check "A4" "HERMES_READ_SAFE_ROOT configured" "PASS" || \
    check "A4" "HERMES_READ_SAFE_ROOT not set — unrestricted file read" "FAIL"

# A5: ANTHROPIC_BASE_URL points to gateway
if env_var_set "ANTHROPIC_BASE_URL"; then
    val=$(env_var_value "ANTHROPIC_BASE_URL")
    if echo "$val" | grep -qE "localhost:8000|safe2-gateway"; then
        check "A5" "ANTHROPIC_BASE_URL routes through gateway" "PASS"
    else
        check "A5" "ANTHROPIC_BASE_URL does not route through HSR gateway (${val})" "FAIL"
    fi
else
    check "A5" "ANTHROPIC_BASE_URL not set — LLM requests bypassing gateway" "WARN"
fi

# A6: HERMES_YOLO not true
if env_var_set "HERMES_YOLO" && [[ "$(env_var_value HERMES_YOLO)" == "true" ]]; then
    check "A6" "HERMES_YOLO=true detected in production — ALL security checks disabled" "FAIL"
else
    check "A6" "HERMES_YOLO not enabled (production safe)" "PASS"
fi

# A7: WECOM disabled (CVE-2026-7396)
if env_var_set "WECOM_ENABLED" && [[ "$(env_var_value WECOM_ENABLED)" == "true" ]]; then
    check "A7" "WECOM_ENABLED=true — CVE-2026-7396 path traversal active" "FAIL"
else
    check "A7" "WeChat Work adapter disabled (CVE-2026-7396 mitigated)" "PASS"
fi

# A8: At least one LLM API key set
if env_var_set "ANTHROPIC_API_KEY" || env_var_set "OPENAI_API_KEY" || env_var_set "OPENROUTER_API_KEY"; then
    check "A8" "LLM provider API key configured" "PASS"
else
    check "A8" "No LLM API key configured" "FAIL"
fi

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}[B] Core File Validation${NC}"
# ---------------------------------------------------------------------------

# B1: Memory vaccine installed
vaccine="${HOME}/.hermes/memories/000_VACCINE_sovereign.md"
if [[ -f "$vaccine" ]]; then
    check "B1" "Memory vaccine installed (${vaccine})" "PASS"
else
    check "B1" "Memory vaccine not installed — run: cp core/hermes_memory_vaccine.md ${vaccine}" "FAIL"
fi

# B2: IDENTITY.md in memories
identity="${HOME}/.hermes/memories/IDENTITY.md"
if [[ -f "$identity" ]]; then
    check "B2" "IDENTITY.md anchor present" "PASS"
else
    check "B2" "IDENTITY.md not installed — run: cp core/IDENTITY.md ${identity}" "WARN"
fi

# B3: SOUL.md in memories
soul="${HOME}/.hermes/memories/SOUL.md"
if [[ -f "$soul" ]]; then
    check "B3" "SOUL.md Love Equation alignment installed" "PASS"
else
    check "B3" "SOUL.md not installed — run: cp core/SOUL.md ${soul}" "WARN"
fi

# B4: Gateway files present
for f in gateway/gateway.py gateway/scanner.py gateway/config.yaml gateway/provider_adapters.py; do
    if [[ -f "${HSR_ROOT}/${f}" ]]; then
        check "B4-${f}" "${f} present" "PASS"
    else
        check "B4-${f}" "${f} MISSING — gateway will not start" "FAIL"
    fi
done

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}[C] Docker Compose Validation${NC}"
# ---------------------------------------------------------------------------

dc="${HSR_ROOT}/docker-compose.yml"
if [[ -f "$dc" ]]; then
    # C1: gVisor runtime configured
    grep -q "runsc" "$dc" && \
        check "C1" "gVisor (runsc) kernel isolation configured" "PASS" || \
        check "C1" "gVisor not configured — consider enabling runtime:runsc for OS isolation" "WARN"

    # C2: no-new-privileges
    grep -q "no-new-privileges" "$dc" && \
        check "C2" "no-new-privileges security option set" "PASS" || \
        check "C2" "no-new-privileges not set" "WARN"

    # C3: Internal-only network
    grep -q "internal: true" "$dc" && \
        check "C3" "Internal-only network configured (no direct egress)" "PASS" || \
        check "C3" "Internal-only network not enforced" "WARN"

    # C4: Vault service present
    grep -q "hashicorp/vault" "$dc" && \
        check "C4" "HashiCorp Vault service present" "PASS" || \
        check "C4" "Vault not in compose — using .env flat secrets" "WARN"
else
    check "C1" "docker-compose.yml not found at ${dc}" "FAIL"
fi

echo ""
# ---------------------------------------------------------------------------
echo -e "${BOLD}[D] Dependency & Supply Chain${NC}"
# ---------------------------------------------------------------------------

# D1: requirements.txt / pyproject.toml present
if [[ -f "${HSR_ROOT}/requirements.txt" ]] || [[ -f "${HSR_ROOT}/pyproject.toml" ]]; then
    check "D1" "Python dependency file present" "PASS"
else
    check "D1" "No requirements.txt or pyproject.toml found" "WARN"
fi

# D2: Skills registry has at least one approved entry
if ls "${HSR_ROOT}/skills-registry/approved/"*.yaml &>/dev/null 2>&1; then
    count=$(ls "${HSR_ROOT}/skills-registry/approved/"*.yaml | wc -l)
    check "D2" "Sovereign skills registry has ${count} approved skill(s)" "PASS"
else
    check "D2" "Sovereign skills registry is empty — any installed skill is unapproved" "WARN"
fi

# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}PASS 1 RESULTS: ${GREEN}${PASS} passed${NC} | ${RED}${FAIL} failed${NC} | ${YELLOW}${WARN} warnings${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}${BOLD}FAILED CHECKS — address before deploying:${NC}"
    for r in "${FAIL_RESULTS[@]}"; do echo -e "  ${RED}•${NC} $r"; done
    echo ""
fi

if [[ $WARN -gt 0 ]]; then
    echo -e "${YELLOW}${BOLD}WARNINGS — recommended fixes:${NC}"
    for r in "${WARN_RESULTS[@]}"; do echo -e "  ${YELLOW}•${NC} $r"; done
    echo ""
fi

[[ $FAIL -gt 0 ]] && exit 1 || exit 0
