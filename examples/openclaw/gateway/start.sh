#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════════════════
# AI SAFE² Control Gateway for OpenClaw — Startup Script v3.0
# ═════════════════════════════════════════════════════════════════════════════
# Validates ALL security prerequisites before allowing the gateway to start.
# Any critical failure = hard abort. No partial starts.
#
# Startup sequence:
#   [1] Python version
#   [2] pip dependencies
#   [3] Required environment variables (ANTHROPIC_API_KEY, AUDIT_CHAIN_KEY,
#       OPERATOR_DEACTIVATION_KEY)
#   [4] Configuration file
#   [5] Network security (bind_host != 0.0.0.0)
#   [6] Pre-flight scanner.py run (full security audit)
#   [7] HEARTBEAT.md initialization (first run only) or validation
#   [8] Audit log directory and permissions
#   [9] Launch gateway
# ═════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS() { echo -e "  ${GREEN}✓${NC} $1"; }
FAIL() { echo -e "  ${RED}✗ FAIL: $1${NC}"; }
WARN() { echo -e "  ${YELLOW}⚠ WARN: $1${NC}"; }
INFO() { echo -e "  ${CYAN}ℹ${NC} $1"; }

# ─── Config ───────────────────────────────────────────────────────────────────
CONFIG_FILE="${GATEWAY_CONFIG:-config.yaml}"
GATEWAY_SCRIPT="gateway.py"
SCANNER_SCRIPT="../scanner/scanner.py"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  AI SAFE² Control Gateway for OpenClaw — v3.0               ${NC}"
echo -e "${BOLD}  Startup Validation Sequence                                  ${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

HARD_FAILURES=0

abort_if_failures() {
    if [ "$HARD_FAILURES" -gt 0 ]; then
        echo ""
        FAIL "Startup aborted: $HARD_FAILURES prerequisite(s) failed."
        echo ""
        echo "  Resolve the failures above before starting the gateway."
        echo "  No partial start. No silent degradation."
        echo ""
        exit 1
    fi
}

# ─── Step 1: Python version ───────────────────────────────────────────────────
echo -e "${BOLD}[1/9] Python version${NC}"
if ! command -v python3 &>/dev/null; then
    FAIL "python3 not found. Install Python 3.9+"
    HARD_FAILURES=$((HARD_FAILURES + 1))
else
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
        FAIL "Python $PY_VERSION found. Python 3.9+ required."
        HARD_FAILURES=$((HARD_FAILURES + 1))
    else
        PASS "Python $PY_VERSION"
    fi
fi
echo ""

# ─── Step 2: Dependencies ─────────────────────────────────────────────────────
echo -e "${BOLD}[2/9] Python dependencies${NC}"
REQUIRED_PACKAGES=("flask" "requests" "jsonschema" "pyyaml")
MISSING_PACKAGES=()
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        VERSION=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>/dev/null || echo "unknown")
        PASS "$pkg==$VERSION"
    else
        FAIL "$pkg not installed"
        MISSING_PACKAGES+=("$pkg")
        HARD_FAILURES=$((HARD_FAILURES + 1))
    fi
done
if [ "${#MISSING_PACKAGES[@]}" -gt 0 ]; then
    INFO "Fix: pip3 install ${MISSING_PACKAGES[*]}"
fi
echo ""

# ─── Step 3: Required environment variables ───────────────────────────────────
echo -e "${BOLD}[3/9] Environment variables${NC}"

check_env_var() {
    local var="$1"
    local description="$2"
    local is_required="${3:-true}"
    local value="${!var:-}"

    if [ -z "$value" ]; then
        if [ "$is_required" = "true" ]; then
            FAIL "$var not set ($description)"
            HARD_FAILURES=$((HARD_FAILURES + 1))
        else
            WARN "$var not set ($description) — some features will be limited"
        fi
    elif [ "$var" = "ANTHROPIC_API_KEY" ] && [[ ! "$value" =~ ^sk-ant- ]]; then
        WARN "$var set but format unexpected (expected sk-ant-...)"
    elif [ "$var" = "AUDIT_CHAIN_KEY" ] && [ "$value" = "default-change-me" ]; then
        FAIL "$var is set to default insecure value"
        INFO "Generate: export AUDIT_CHAIN_KEY=\$(openssl rand -hex 32)"
        HARD_FAILURES=$((HARD_FAILURES + 1))
    else
        PASS "$var is set"
    fi
}

check_env_var "ANTHROPIC_API_KEY"          "Anthropic upstream API key"         "true"
check_env_var "AUDIT_CHAIN_KEY"            "HMAC key for audit log integrity"   "true"
check_env_var "OPERATOR_DEACTIVATION_KEY"  "Safe mode deactivation key"         "true"
check_env_var "ALERT_WEBHOOK_URL"          "Security alert webhook (optional)"  "false"
echo ""

abort_if_failures

# ─── Step 4: Configuration file ───────────────────────────────────────────────
echo -e "${BOLD}[4/9] Configuration file${NC}"
if [ ! -f "$CONFIG_FILE" ]; then
    FAIL "Config file not found: $CONFIG_FILE"
    INFO "Create from template or specify: GATEWAY_CONFIG=path/to/config.yaml ./start.sh"
    HARD_FAILURES=$((HARD_FAILURES + 1))
else
    PASS "Config found: $CONFIG_FILE"
    # Validate YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
        PASS "Config YAML is valid"
    else
        FAIL "Config YAML has syntax errors"
        HARD_FAILURES=$((HARD_FAILURES + 1))
    fi
fi
echo ""

abort_if_failures

# ─── Step 5: Network security ─────────────────────────────────────────────────
echo -e "${BOLD}[5/9] Network security${NC}"
# Parse bind_host using Python (not brittle grep)
BIND_HOST=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$CONFIG_FILE'))
print(cfg.get('gateway', {}).get('bind_host', '127.0.0.1'))
" 2>/dev/null || echo "127.0.0.1")

BIND_PORT=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$CONFIG_FILE'))
print(cfg.get('gateway', {}).get('bind_port', 8888))
" 2>/dev/null || echo "8888")

if [ "$BIND_HOST" = "0.0.0.0" ] || [ "$BIND_HOST" = "::" ]; then
    echo ""
    FAIL "SECURITY RISK: bind_host=$BIND_HOST exposes gateway to all network interfaces."
    echo ""
    echo -e "  ${RED}  This means any host on your network can send requests to this gateway.${NC}"
    echo -e "  ${RED}  Change bind_host to 127.0.0.1 in $CONFIG_FILE${NC}"
    echo ""
    read -rp "  Accept risk and continue anyway? (Type YES to proceed): " confirm
    echo ""
    if [ "$confirm" != "YES" ]; then
        echo "  Aborting. Change bind_host: 127.0.0.1 in config.yaml."
        exit 1
    fi
    WARN "Proceeding with public bind (operator acknowledged risk)"
else
    PASS "bind_host=$BIND_HOST (localhost only)"
fi
PASS "bind_port=$BIND_PORT"
echo ""

# ─── Step 6: Pre-flight scanner ───────────────────────────────────────────────
echo -e "${BOLD}[6/9] Pre-flight security scanner${NC}"
if [ -f "$SCANNER_SCRIPT" ]; then
    echo "  Running scanner.py..."
    # Run scanner with exit code capture
    SCANNER_OUTPUT=$(python3 "$SCANNER_SCRIPT" --config "$CONFIG_FILE" 2>&1) || SCANNER_EXIT=$?
    SCANNER_EXIT="${SCANNER_EXIT:-0}"

    if [ "$SCANNER_EXIT" -eq 0 ]; then
        PASS "Scanner: all checks passed"
    elif [ "$SCANNER_EXIT" -eq 1 ]; then
        WARN "Scanner: warnings found (non-fatal)"
        echo ""
        echo "$SCANNER_OUTPUT" | grep -E "(⚠|WARNING)" | head -10 | sed 's/^/    /'
    elif [ "$SCANNER_EXIT" -ge 2 ]; then
        FAIL "Scanner: CRITICAL issues found — gateway cannot start safely"
        echo ""
        echo "$SCANNER_OUTPUT" | grep -E "(❌|CRITICAL)" | head -10 | sed 's/^/    /'
        echo ""
        INFO "Run 'python3 $SCANNER_SCRIPT' for full report."
        HARD_FAILURES=$((HARD_FAILURES + 1))
    fi
else
    WARN "scanner.py not found at $SCANNER_SCRIPT — skipping pre-flight scan"
    INFO "Expected location: $SCANNER_SCRIPT"
fi
echo ""

abort_if_failures

# ─── Step 7: HEARTBEAT.md ─────────────────────────────────────────────────────
echo -e "${BOLD}[7/9] Heartbeat file${NC}"
HB_PATH=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$CONFIG_FILE'))
print(cfg.get('heartbeat', {}).get('path', 'HEARTBEAT.md'))
" 2>/dev/null || echo "HEARTBEAT.md")

if [ ! -f "$HB_PATH" ]; then
    INFO "HEARTBEAT.md not found — initializing for first run"
    if python3 "$GATEWAY_SCRIPT" --init-heartbeat --config "$CONFIG_FILE"; then
        PASS "HEARTBEAT.md initialized"
    else
        FAIL "Failed to initialize HEARTBEAT.md"
        HARD_FAILURES=$((HARD_FAILURES + 1))
    fi
elif [ ! -s "$HB_PATH" ]; then
    FAIL "HEARTBEAT.md is EMPTY — Bug #11766 failure condition detected"
    FAIL "Delete the file and re-run to reinitialize. Investigate why it was emptied."
    HARD_FAILURES=$((HARD_FAILURES + 1))
else
    LAST_LINE=$(tail -1 "$HB_PATH")
    if [[ "$LAST_LINE" =~ ^ALIVE: ]]; then
        PASS "HEARTBEAT.md valid: $LAST_LINE"
    else
        FAIL "HEARTBEAT.md last line malformed: '$LAST_LINE'"
        HARD_FAILURES=$((HARD_FAILURES + 1))
    fi
fi
echo ""

abort_if_failures

# ─── Step 8: Log directories and permissions ──────────────────────────────────
echo -e "${BOLD}[8/9] Log directories${NC}"
AUDIT_LOG=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('$CONFIG_FILE'))
print(cfg.get('logging', {}).get('audit_log', 'logs/gateway_audit.jsonl'))
" 2>/dev/null || echo "logs/gateway_audit.jsonl")

AUDIT_DIR=$(dirname "$AUDIT_LOG")
mkdir -p "$AUDIT_DIR" "data"
chmod 750 "$AUDIT_DIR" "data"

if [ -f "$AUDIT_LOG" ]; then
    chmod 640 "$AUDIT_LOG"
    AUDIT_SIZE=$(wc -l < "$AUDIT_LOG" 2>/dev/null || echo "0")
    PASS "Audit log: $AUDIT_LOG ($AUDIT_SIZE entries)"
else
    PASS "Audit log directory ready: $AUDIT_DIR (new log will be created)"
fi
PASS "data/ directory ready (action history)"
echo ""

# ─── Step 9: Launch ───────────────────────────────────────────────────────────
echo -e "${BOLD}[9/9] Launching gateway${NC}"
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Starting AI SAFE² Gateway v3.0${NC}"
echo -e "  Endpoint: http://${BIND_HOST}:${BIND_PORT}/v1/messages"
echo -e "  Health:   http://${BIND_HOST}:${BIND_PORT}/health"
echo -e "  Stats:    http://${BIND_HOST}:${BIND_PORT}/stats"
echo -e "  Chain:    http://${BIND_HOST}:${BIND_PORT}/audit/verify-chain"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

exec python3 "$GATEWAY_SCRIPT" --config "$CONFIG_FILE" "$@"
