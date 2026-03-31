#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Stop Hook
# Sovereign Runtime Governor: Session Termination & Cleanup
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Runs when a Claude Code session ends (normally or via interruption).
# Responsibilities:
#   1. Log session summary
#   2. Purge any temp credentials scoped to this session
#   3. Check alert log for session and summarize
#   4. Optionally notify SIEM of session end
# =============================================================================

set -euo pipefail

LOG_DIR="${CLAUDE_CODE_LOG_DIR:-$HOME/.claude/logs}"
LOG_FILE="$LOG_DIR/sessions.log"
ALERT_FILE="$LOG_DIR/security-alerts.log"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-unknown-$$}"

# Read stdin (session end context -- may be empty)
# Read stdin (session end context -- consumed but not parsed)
cat 2>/dev/null || true

# =============================================================================
# Count session activity
# =============================================================================
ALLOWED_COUNT=0
BLOCKED_COUNT=0
SECRET_COUNT=0
SUBAGENT_COUNT=0

if [[ -f "$LOG_DIR/pre-tool-use.log" ]]; then
  ALLOWED_COUNT=$(grep -c "ALLOWED" "$LOG_DIR/pre-tool-use.log" 2>/dev/null || echo 0)
  BLOCKED_COUNT=$(grep -c "BLOCKED" "$LOG_DIR/pre-tool-use.log" 2>/dev/null || echo 0)
fi

if [[ -f "$ALERT_FILE" ]]; then
  SECRET_COUNT=$(grep -c "SECRET_DETECTED" "$ALERT_FILE" 2>/dev/null || echo 0)
fi

if [[ -f "$LOG_DIR/post-tool-use.log" ]]; then
  SUBAGENT_COUNT=$(grep -c "SUBAGENT_SPAWNED" "$LOG_DIR/post-tool-use.log" 2>/dev/null || echo 0)
fi

# Write session summary
SESSION_SUMMARY="$TIMESTAMP | SESSION_END | session=$SESSION_ID | allowed=$ALLOWED_COUNT | blocked=$BLOCKED_COUNT | secrets_detected=$SECRET_COUNT | subagents=$SUBAGENT_COUNT"
echo "$SESSION_SUMMARY" >> "$LOG_FILE"

# =============================================================================
# Purge JIT credentials if used
# =============================================================================
# If this session used JIT-scoped credentials (see scripts/jit-wrapper.sh),
# the JIT wrapper will handle revocation. This is a safety net.

JIT_KEY_ENV="${CLAUDE_CODE_JIT_KEY_ID:-}"
if [[ -n "$JIT_KEY_ENV" ]]; then
  echo "$TIMESTAMP | JIT_REVOKE | key_id=$JIT_KEY_ENV -- ensure JIT wrapper revoked this key" >> "$LOG_FILE"
fi

# =============================================================================
# Rotate temp session marker
# =============================================================================
TEMP_SESSION_FILE="$HOME/.claude/.current-session"
rm -f "$TEMP_SESSION_FILE"

# =============================================================================
# Print summary if any security events occurred
# =============================================================================
if [[ "$BLOCKED_COUNT" -gt 0 ]] || [[ "$SECRET_COUNT" -gt 0 ]]; then
  echo ""
  echo "================================================================"
  echo "AI SAFE2 SESSION SECURITY SUMMARY"
  echo "================================================================"
  echo "Session ended: $TIMESTAMP"
  echo "Tool executions allowed: $ALLOWED_COUNT"
  echo "Tool executions BLOCKED: $BLOCKED_COUNT"
  echo "Potential secrets in output: $SECRET_COUNT"
  echo "Subagents spawned: $SUBAGENT_COUNT"
  echo ""
  if [[ "$BLOCKED_COUNT" -gt 0 ]]; then
    echo "REVIEW REQUIRED: $BLOCKED_COUNT operations were blocked this session."
    echo "Check $LOG_DIR/pre-tool-use.log for details."
  fi
  if [[ "$SECRET_COUNT" -gt 0 ]]; then
    echo "CRITICAL REVIEW: $SECRET_COUNT potential secrets were detected in output."
    echo "Check $ALERT_FILE and rotate any exposed credentials immediately."
  fi
  echo "================================================================"
fi

exit 0
