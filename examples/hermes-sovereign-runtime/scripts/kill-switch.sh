#!/usr/bin/env bash
# HSR Kill Switch — Immediate Execution Suspension
# AI SAFE² v3.0 · P3.F-C05
# Cyber Strategy Institute
#
# Suspends ALL Hermes tool execution in under 1 second.
# Writes a kill file that the gateway checks on every request.
#
# Usage:
#   bash scripts/kill-switch.sh                     # Activate with default reason
#   bash scripts/kill-switch.sh "Suspected injection attack in session XYZ"
#   bash scripts/kill-switch.sh --revive            # Deactivate
#   bash scripts/kill-switch.sh --status            # Check status

set -euo pipefail

KILL_FILE="${KILL_SWITCH_FILE:-/tmp/hsr_kill_switch}"
GATEWAY_API="${GATEWAY_API:-http://127.0.0.1:8000}"
AUDIT_LOG="${AUDIT_LOG_PATH:-/tmp/hsr_audit.jsonl}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_banner() {
  echo -e "${RED}"
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║         HSR KILL SWITCH — AI SAFE² v3.0                  ║"
  echo "║         Cyber Strategy Institute                         ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

log_audit() {
  local event="$1"
  local reason="$2"
  local entry
  entry=$(cat <<EOF
{"event":"$event","reason":"$reason","timestamp":"$TIMESTAMP","operator":"$(whoami)","host":"$(hostname)"}
EOF
)
  echo "$entry" >> "$AUDIT_LOG" 2>/dev/null || true
  # Also attempt to notify gateway
  curl -sf -X POST "$GATEWAY_API/hsr/$([ "$event" = "kill_switch_activated" ] && echo "kill" || echo "revive")" \
    -H "Content-Type: application/json" \
    -d "{\"reason\":\"$reason\"}" > /dev/null 2>&1 || true
}

activate_kill_switch() {
  local reason="${1:-Manual kill switch activation}"
  print_banner
  
  # Write kill file
  cat > "$KILL_FILE" <<EOF
{
  "activated_at": "$TIMESTAMP",
  "reason": "$reason",
  "operator": "$(whoami)",
  "host": "$(hostname)"
}
EOF
  
  log_audit "kill_switch_activated" "$reason"
  
  echo -e "${RED}██ KILL SWITCH ACTIVATED ██${NC}"
  echo ""
  echo -e "  Reason   : ${YELLOW}$reason${NC}"
  echo -e "  At       : $TIMESTAMP"
  echo -e "  Kill file: $KILL_FILE"
  echo ""
  echo -e "${RED}ALL Hermes tool execution is now suspended.${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Investigate the incident"
  echo "  2. Review audit log: tail -f $AUDIT_LOG | jq ."
  echo "  3. If credentials may be compromised: bash scripts/rotate-credentials.sh"
  echo "  4. When safe to resume: bash scripts/kill-switch.sh --revive"
  echo ""
  
  # Docker: pause the hermes container if running
  if command -v docker &>/dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "hsr-hermes"; then
      echo -e "${YELLOW}Pausing hsr-hermes container...${NC}"
      docker pause hsr-hermes 2>/dev/null && echo "Container paused." || echo "Container pause failed (may not be running)."
    fi
  fi
  
  # Send alert webhook if configured
  if [[ -n "${ALERT_WEBHOOK_URL:-}" ]]; then
    curl -sf -X POST "$ALERT_WEBHOOK_URL" \
      -H "Content-Type: application/json" \
      -d "{
        \"text\": \"🚨 HSR KILL SWITCH ACTIVATED\\nReason: $reason\\nTime: $TIMESTAMP\\nHost: $(hostname)\"
      }" > /dev/null 2>&1 || echo "Webhook notification failed."
  fi
}

deactivate_kill_switch() {
  print_banner
  
  if [[ ! -f "$KILL_FILE" ]]; then
    echo -e "${GREEN}Kill switch is not active.${NC}"
    exit 0
  fi
  
  echo -e "${YELLOW}Deactivating kill switch...${NC}"
  
  # Show what activated it
  echo "Previous activation:"
  cat "$KILL_FILE" | python3 -m json.tool 2>/dev/null || cat "$KILL_FILE"
  echo ""
  
  read -r -p "Confirm deactivation? Type 'REVIVE' to confirm: " confirm
  if [[ "$confirm" != "REVIVE" ]]; then
    echo "Deactivation cancelled."
    exit 1
  fi
  
  rm -f "$KILL_FILE"
  log_audit "kill_switch_deactivated" "Manual deactivation by $(whoami)"
  
  # Unpause container if paused
  if command -v docker &>/dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "hsr-hermes"; then
      docker unpause hsr-hermes 2>/dev/null && echo "Container unpaused." || true
    fi
  fi
  
  echo -e "${GREEN}Kill switch deactivated. Hermes operations resumed.${NC}"
  echo ""
  echo -e "${YELLOW}Reminder: Review the incident before resuming autonomous operations.${NC}"
}

check_status() {
  echo -e "${CYAN}HSR Kill Switch Status${NC}"
  echo "─────────────────────"
  
  if [[ -f "$KILL_FILE" ]]; then
    echo -e "Status: ${RED}ACTIVE — All operations suspended${NC}"
    echo ""
    echo "Activation details:"
    cat "$KILL_FILE" | python3 -m json.tool 2>/dev/null || cat "$KILL_FILE"
  else
    echo -e "Status: ${GREEN}INACTIVE — Operations running normally${NC}"
  fi
  
  echo ""
  echo "Gateway API: $GATEWAY_API"
  if curl -sf "$GATEWAY_API/hsr/health" > /dev/null 2>&1; then
    echo -e "Gateway: ${GREEN}reachable${NC}"
    curl -sf "$GATEWAY_API/hsr/health" | python3 -m json.tool 2>/dev/null || true
  else
    echo -e "Gateway: ${YELLOW}unreachable (may be down)${NC}"
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────

case "${1:-}" in
  --revive|--deactivate|--off)
    deactivate_kill_switch
    ;;
  --status|--check)
    check_status
    ;;
  --help|-h)
    echo "Usage: kill-switch.sh [reason] | --revive | --status"
    echo ""
    echo "  (no args)     Activate with default reason"
    echo "  'reason text' Activate with custom reason"
    echo "  --revive      Deactivate (requires confirmation)"
    echo "  --status      Check current status"
    ;;
  *)
    reason="${1:-Manual kill switch activation - no reason provided}"
    activate_kill_switch "$reason"
    ;;
esac
