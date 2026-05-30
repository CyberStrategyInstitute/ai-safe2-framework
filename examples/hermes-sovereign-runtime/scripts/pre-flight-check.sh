#!/usr/bin/env bash
# HSR Pre-Flight Check — 25-Point Deployment Validation
# AI SAFE² v3.0 · Cyber Strategy Institute
#
# Validates sovereign runtime configuration before deploy.
# Run before every production deployment.
#
# Usage: bash scripts/pre-flight-check.sh [--strict]
# Exit codes:
#   0 — All critical checks passed
#   1 — Non-critical warnings
#   2 — Critical failures (do not deploy)

set -euo pipefail

STRICT="${1:-}"
PASS=0
WARN=0
FAIL=0
CRITICAL_FAIL=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

check_pass() {
  echo -e "  ${GREEN}✓${NC} $1"
  ((PASS++))
}

check_warn() {
  echo -e "  ${YELLOW}⚠${NC} $1"
  ((WARN++))
}

check_fail() {
  echo -e "  ${RED}✗${NC} ${BOLD}$1${NC}"
  ((FAIL++))
  ((CRITICAL_FAIL++))
}

section() {
  echo ""
  echo -e "${CYAN}── $1 ──────────────────────────────────────────${NC}"
}

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║    HSR Pre-Flight Check · AI SAFE² v3.0                  ║${NC}"
echo -e "${BOLD}║    Cyber Strategy Institute                              ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Running $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# ─── Section 1: Environment File ─────────────────────────────────────────────

section "1. Environment Configuration"

# Check 1: .env exists
if [[ -f ".env" ]]; then
  check_pass ".env file exists"
else
  check_fail ".env file missing — copy from .env.example and configure"
fi

# Check 2: AUDIT_CHAIN_KEY set
if grep -q "^AUDIT_CHAIN_KEY=.\{16,\}" .env 2>/dev/null; then
  check_pass "AUDIT_CHAIN_KEY is configured"
else
  check_fail "AUDIT_CHAIN_KEY not set — run: export AUDIT_CHAIN_KEY=\$(openssl rand -hex 32)"
fi

# Check 3: At least one provider key set
if grep -qE "^(ANTHROPIC|OPENAI|OPENROUTER|GEMINI)_API_KEY=.{8,}" .env 2>/dev/null; then
  check_pass "LLM provider API key is configured"
else
  check_fail "No LLM provider API key configured in .env"
fi

# Check 4: .env file permissions
if [[ -f ".env" ]]; then
  perms=$(stat -c "%a" .env 2>/dev/null || stat -f "%Lp" .env 2>/dev/null || echo "000")
  if [[ "$perms" == "600" || "$perms" == "400" ]]; then
    check_pass ".env permissions are secure (${perms})"
  else
    check_fail ".env permissions are ${perms} — fix: chmod 600 .env"
  fi
fi

# Check 5: VAULT_ROOT_TOKEN not default in production
if grep -q "^VAULT_ROOT_TOKEN=hsr-dev-token" .env 2>/dev/null; then
  check_warn "VAULT_ROOT_TOKEN is using development default — change before production"
else
  check_pass "VAULT_ROOT_TOKEN appears customized"
fi

# ─── Section 2: Core Governance Files ────────────────────────────────────────

section "2. Core Governance Files"

CORE_FILES=(
  "core/hermes_memory_vaccine.md"
  "core/IDENTITY.md"
  "core/SOUL.md"
  "core/SUBAGENT-POLICY.md"
  "core/HEARTBEAT.md"
)

for f in "${CORE_FILES[@]}"; do
  if [[ -f "$f" ]]; then
    check_pass "$f present"
  else
    check_fail "$f missing — sovereign governance incomplete"
  fi
done

# Check vaccine has critical directives
if [[ -f "core/hermes_memory_vaccine.md" ]]; then
  if grep -q "DIRECTIVE 1" core/hermes_memory_vaccine.md && \
     grep -q "DIRECTIVE 2" core/hermes_memory_vaccine.md; then
    check_pass "Memory vaccine contains required directives"
  else
    check_fail "Memory vaccine appears truncated or modified"
  fi
fi

# ─── Section 3: Gateway Configuration ────────────────────────────────────────

section "3. AI SAFE² Gateway"

if [[ -f "gateway/gateway.py" ]]; then
  check_pass "gateway.py present"
else
  check_fail "gateway.py missing"
fi

if [[ -f "gateway/config.yaml" ]]; then
  check_pass "gateway config.yaml present"
  # Check PII filter enabled
  if grep -q "block_pii: true" gateway/config.yaml 2>/dev/null; then
    check_pass "PII filter enabled in config"
  else
    check_warn "PII filter not confirmed enabled in config.yaml"
  fi
  # Check secrets filter enabled
  if grep -q "block_secrets: true" gateway/config.yaml 2>/dev/null; then
    check_pass "Secrets filter enabled in config"
  else
    check_warn "Secrets filter not confirmed enabled in config.yaml"
  fi
else
  check_warn "gateway/config.yaml missing — defaults will be used"
fi

# ─── Section 4: Docker Compose Hardening ─────────────────────────────────────

section "4. Docker Compose Hardening"

if [[ -f "docker-compose.yml" ]]; then
  check_pass "docker-compose.yml present"
  
  # Check HERMES_FORCE_APPROVAL
  if grep -q "HERMES_FORCE_APPROVAL=true" docker-compose.yml; then
    check_pass "HERMES_FORCE_APPROVAL=true — container approval bypass overridden (Critical finding)"
  else
    check_fail "HERMES_FORCE_APPROVAL=true missing — CRITICAL: container deployment disables all approvals"
  fi
  
  # Check no-new-privileges
  if grep -q "no-new-privileges:true" docker-compose.yml; then
    check_pass "no-new-privileges security option set"
  else
    check_warn "no-new-privileges not set on hermes container"
  fi
  
  # Check HERMES_YOLO is false or not present
  if grep -q "HERMES_YOLO=true" docker-compose.yml; then
    check_fail "HERMES_YOLO=true detected in docker-compose — YOLO mode enabled in production"
  else
    check_pass "YOLO mode not enabled"
  fi
  
  # Check read_only or workspace restriction
  if grep -q "HERMES_READ_SAFE_ROOT" docker-compose.yml; then
    check_pass "HERMES_READ_SAFE_ROOT filesystem restriction configured"
  else
    check_fail "HERMES_READ_SAFE_ROOT not set — agent can read arbitrary files"
  fi
  
  # Check gateway routing
  if grep -q "ANTHROPIC_BASE_URL=http://safe2-gateway" docker-compose.yml; then
    check_pass "LLM traffic routed through AI SAFE² gateway"
  else
    check_fail "ANTHROPIC_BASE_URL not routing through gateway — controls bypassed"
  fi
  
  # Check internal-only network
  if grep -q "internal: true" docker-compose.yml; then
    check_pass "internal-only network configured (hermes has no direct egress)"
  else
    check_warn "internal-only network not confirmed — hermes may have direct internet access"
  fi
  
  # Check WeChat Work disabled
  if grep -q "WECOM_ENABLED=false" docker-compose.yml; then
    check_pass "WeChat Work adapter disabled (CVE-2026-7396 mitigation)"
  else
    check_warn "WECOM_ENABLED not explicitly disabled — verify CVE-2026-7396 not applicable"
  fi
  
else
  check_fail "docker-compose.yml missing"
fi

# ─── Section 5: Supervisor and Kill Switch ───────────────────────────────────

section "5. Ishi Supervisor and Kill Switch"

if [[ -f "supervisor/ishi_config.yaml" ]]; then
  check_pass "Ishi supervisor config present"
else
  check_warn "Ishi supervisor config missing"
fi

if [[ -f "supervisor/policies/tool_approval.rego" ]]; then
  check_pass "Tool approval policy (OPA) present"
else
  check_warn "Tool approval OPA policy missing"
fi

if [[ -f "scripts/kill-switch.sh" ]]; then
  check_pass "Kill switch script present"
  if [[ -x "scripts/kill-switch.sh" ]]; then
    check_pass "Kill switch script is executable"
  else
    check_warn "Kill switch script not executable — run: chmod +x scripts/kill-switch.sh"
  fi
else
  check_fail "Kill switch script missing"
fi

# ─── Section 6: Sovereign Skills Registry ────────────────────────────────────

section "6. Skills Registry"

if [[ -d "skills-registry" ]]; then
  check_pass "Sovereign skills registry directory present"
else
  check_warn "skills-registry/ missing — community skills will be used unreviewed"
fi

if [[ -f "skills-registry/verify_skill.sh" ]]; then
  check_pass "Skill verification script present"
else
  check_warn "Skill verification script missing"
fi

# ─── Section 7: Monitoring ────────────────────────────────────────────────────

section "7. Monitoring"

if [[ -f "monitoring/memory_auditor.py" ]]; then
  check_pass "Memory auditor daemon present"
else
  check_warn "Memory auditor missing — indirect prompt injection via memory unmonitored"
fi

if [[ -f "monitoring/prometheus.yml" ]]; then
  check_pass "Prometheus config present"
fi

# ─── Section 8: Validation Suite ─────────────────────────────────────────────

section "8. Validation Suite"

VALIDATION_FILES=(
  "validation/pass1_static.sh"
  "validation/pass2_runtime.sh"
  "validation/pass3_adversarial.py"
  "validation/pass4_compliance.sh"
  "validation/pass5_readiness.sh"
)

for f in "${VALIDATION_FILES[@]}"; do
  if [[ -f "$f" ]]; then
    check_pass "$f present"
  else
    check_warn "$f missing"
  fi
done

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                    PRE-FLIGHT SUMMARY                    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}PASSED  : $PASS${NC}"
echo -e "  ${YELLOW}WARNINGS: $WARN${NC}"
echo -e "  ${RED}FAILED  : $FAIL${NC}"
echo ""

if [[ $CRITICAL_FAIL -gt 0 ]]; then
  echo -e "  ${RED}${BOLD}⛔ DO NOT DEPLOY — $CRITICAL_FAIL critical check(s) failed${NC}"
  echo ""
  echo "  Fix all FAILED items before deploying."
  echo "  See docs/ARCHITECTURE.md for remediation guidance."
  echo ""
  exit 2
elif [[ $WARN -gt 0 ]]; then
  echo -e "  ${YELLOW}⚠ DEPLOY WITH CAUTION — $WARN warning(s)${NC}"
  echo ""
  if [[ "$STRICT" == "--strict" ]]; then
    echo "  Strict mode: treating warnings as failures."
    exit 1
  fi
  exit 1
else
  echo -e "  ${GREEN}${BOLD}✅ ALL CHECKS PASSED — Safe to deploy${NC}"
  echo ""
  echo "  Next step: docker compose up -d"
  echo "  Then run: bash validation/pass2_runtime.sh"
  echo ""
  exit 0
fi
