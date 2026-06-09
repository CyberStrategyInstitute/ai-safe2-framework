#!/bin/bash
################################################################################
# run-all-verifications.sh — AI SAFE² Unified Verification Runner
#
# Runs both repo hygiene checks AND sovereign runtime adversarial tests.
# Supports profiles for targeted execution.
#
# Usage:
#   ./scripts/run-all-verifications.sh
#   ./scripts/run-all-verifications.sh --profile sovereign-runtime
#   ./scripts/run-all-verifications.sh --profile hygiene
#   ./scripts/run-all-verifications.sh --json
#   ./scripts/run-all-verifications.sh --tier 2
################################################################################

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'  GREEN='\033[0;32m'
YELLOW='\033[1;33m'  BLUE='\033[0;34m'
NC='\033[0m'

# Flags
PROFILE="all"
JSON_OUTPUT=false
TIER_FILTER=""

for arg in "$@"; do
  case $arg in
    --profile) PROFILE="${2}"; shift 2 ;;
    --json)    JSON_OUTPUT=true ;;
    --tier)    TIER_FILTER="${2}"; shift 2 ;;
  esac
done

TOTAL_PASS=0
TOTAL_FAIL=0

log_section() { echo -e "\n${BLUE}══════════════════════════════════════════${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}══════════════════════════════════════════${NC}\n"; }
log_pass()    { echo -e "${GREEN}[PASS]${NC} $1"; TOTAL_PASS=$((TOTAL_PASS+1)); }
log_fail()    { echo -e "${RED}[FAIL]${NC} $1"; TOTAL_FAIL=$((TOTAL_FAIL+1)); }
log_skip()    { echo -e "${YELLOW}[SKIP]${NC} $1"; }
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }

if [ "$JSON_OUTPUT" = false ]; then
  echo -e "${BLUE}"
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🛡️  AI SAFE²  //  UNIFIED VERIFICATION RUNNER"
  echo "     Profile: $PROFILE  |  $(date '+%Y-%m-%d %H:%M:%S')"
  echo "═══════════════════════════════════════════════════════════════"
  echo -e "${NC}"
fi

################################################################################
# Profile: hygiene — repo structure & security config checks
################################################################################

run_hygiene_checks() {
  log_section "Repo Hygiene Checks"

  # Required directories
  for dir in core enforcement controls tests reports scripts; do
    if [ -d "$REPO_ROOT/$dir" ]; then
      log_pass "Directory exists: $dir/"
    else
      log_fail "Missing directory: $dir/"
    fi
  done

  # Required enforcement files
  for file in enforcement/safe_gateway.js enforcement/circuit_breaker.js enforcement/audit_logger.js; do
    if [ -f "$REPO_ROOT/$file" ]; then
      log_pass "Enforcement file: $file"
    else
      log_fail "Missing enforcement file: $file"
    fi
  done

  # Required governance files
  for file in core/IDENTITY.md core/SOUL.md core/GOVERNANCE.md core/TOOLS.md core/USER.md core/MEMORY.md; do
    if [ -f "$REPO_ROOT/$file" ]; then
      log_pass "Governance file: $file"
    else
      log_fail "Missing governance file: $file"
    fi
  done

  # Machine-readable policy manifest
  if [ -f "$REPO_ROOT/controls/policy.yaml" ]; then
    log_pass "Policy manifest: controls/policy.yaml"
  else
    log_fail "Missing policy manifest: controls/policy.yaml"
  fi

  # Verify .gitignore excludes reports/ and audit.log
  if [ -f "$REPO_ROOT/.gitignore" ]; then
    if grep -q "reports/" "$REPO_ROOT/.gitignore"; then
      log_pass ".gitignore excludes reports/"
    else
      log_fail ".gitignore should exclude reports/ (generated files)"
    fi
    if grep -q "audit.log" "$REPO_ROOT/.gitignore"; then
      log_pass ".gitignore excludes audit.log"
    else
      log_fail ".gitignore should exclude audit.log (runtime log)"
    fi
  else
    log_fail ".gitignore not found"
  fi

  # Node syntax check
  if command -v node &> /dev/null; then
    for jsfile in enforcement/safe_gateway.js enforcement/circuit_breaker.js enforcement/audit_logger.js smoke_test.js; do
      if [ -f "$REPO_ROOT/$jsfile" ]; then
        if node --check "$REPO_ROOT/$jsfile" 2>/dev/null; then
          log_pass "Syntax valid: $jsfile"
        else
          log_fail "Syntax error: $jsfile"
        fi
      fi
    done
  else
    log_skip "node not found — skipping syntax checks"
  fi
}

################################################################################
# Profile: sovereign-runtime — adversarial threat tests
################################################################################

run_sovereign_runtime() {
  log_section "Sovereign Runtime Adversarial Tests"

  if ! command -v node &> /dev/null && ! command -v agy-node &> /dev/null; then
    log_fail "Neither 'node' nor 'agy-node' found in PATH"
    return
  fi

  NODE_CMD=$(command -v agy-node 2>/dev/null || command -v node)
  log_info "Using runtime: $NODE_CMD"

  SMOKE_ARGS=""
  [ -n "$TIER_FILTER" ] && SMOKE_ARGS="--tier $TIER_FILTER"
  [ "$JSON_OUTPUT" = true ] && SMOKE_ARGS="$SMOKE_ARGS --json"

  if "$NODE_CMD" "$REPO_ROOT/smoke_test.js" $SMOKE_ARGS; then
    log_pass "Sovereign runtime tests: all scenarios passed"
  else
    log_fail "Sovereign runtime tests: one or more scenarios failed"
    TOTAL_FAIL=$((TOTAL_FAIL+1))
    TOTAL_PASS=$((TOTAL_PASS-1))  # adjust for the aggregate
  fi
}

################################################################################
# Profile: evidence — verify outputs were generated and hashed
################################################################################

run_evidence_checks() {
  log_section "Evidence & Report Validation"

  # Check reports directory
  for output in \
    "reports/ai_safe2_compliance_report.md" \
    "reports/ai_safe2_evidence.json" \
    "reports/ai_safe2_results.sarif";
  do
    if [ -f "$REPO_ROOT/$output" ]; then
      size=$(wc -c < "$REPO_ROOT/$output")
      log_pass "Report generated: $output ($size bytes)"
    else
      log_fail "Missing report output: $output (run smoke_test.js first)"
    fi
  done

  # Validate SARIF schema version
  if [ -f "$REPO_ROOT/reports/ai_safe2_results.sarif" ] && command -v jq &> /dev/null; then
    sarif_version=$(jq -r '.version' "$REPO_ROOT/reports/ai_safe2_results.sarif" 2>/dev/null)
    if [ "$sarif_version" = "2.1.0" ]; then
      log_pass "SARIF version: 2.1.0 (GitHub-compatible)"
    else
      log_fail "SARIF version mismatch: got '$sarif_version', expected '2.1.0'"
    fi
  fi

  # Validate evidence JSON has expected fields
  if [ -f "$REPO_ROOT/reports/ai_safe2_evidence.json" ] && command -v jq &> /dev/null; then
    controls_count=$(jq '.controls | length' "$REPO_ROOT/reports/ai_safe2_evidence.json" 2>/dev/null || echo "0")
    verified_count=$(jq '[.controls[] | select(.verified == true)] | length' "$REPO_ROOT/reports/ai_safe2_evidence.json" 2>/dev/null || echo "0")
    compliance=$(jq '.summary.compliancePercent' "$REPO_ROOT/reports/ai_safe2_evidence.json" 2>/dev/null || echo "0")
    log_pass "Evidence ledger: $verified_count/$controls_count controls verified ($compliance% compliance)"
  fi
}

################################################################################
# Run selected profile
################################################################################

case "$PROFILE" in
  hygiene)          run_hygiene_checks ;;
  sovereign-runtime) run_sovereign_runtime ;;
  evidence)         run_evidence_checks ;;
  all|*)
    run_hygiene_checks
    run_sovereign_runtime
    run_evidence_checks
    ;;
esac

################################################################################
# Final summary
################################################################################

if [ "$JSON_OUTPUT" = false ]; then
  echo ""
  echo -e "${BLUE}══════════════════════════════════════════${NC}"
  echo -e "  Verification Summary"
  echo -e "  ${GREEN}Passed: $TOTAL_PASS${NC}  ${RED}Failed: $TOTAL_FAIL${NC}"
  echo -e "${BLUE}══════════════════════════════════════════${NC}"
  echo ""

  if [ $TOTAL_FAIL -eq 0 ]; then
    echo -e "${GREEN}🛡️  ALL VERIFICATIONS PASSED${NC}"
  else
    echo -e "${RED}🚨 VERIFICATION FAILURES DETECTED — Review output above${NC}"
  fi
  echo ""
fi

exit $( [ $TOTAL_FAIL -eq 0 ] && echo 0 || echo 1 )
