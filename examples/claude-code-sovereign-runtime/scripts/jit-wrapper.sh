#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- JIT Credential Wrapper
# Pillar 3: Fail-Safe & Recovery
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Wraps Claude Code with short-lived, scoped credentials.
# Instead of exposing your long-lived ANTHROPIC_API_KEY directly,
# this script can request a session-scoped token (if your org supports it)
# and revokes it automatically when the session ends.
#
# Usage:
#   ./scripts/jit-wrapper.sh [claude-code-args...]
#   ./scripts/jit-wrapper.sh --session-timeout 3600 [claude-code-args...]
#
# For teams using AWS: replace the ANTHROPIC section with STS assume-role
# For teams using Vault: replace with vault token create
# For teams using 1Password CLI: replace with op run
# =============================================================================

set -euo pipefail

SESSION_TIMEOUT="${CLAUDE_CODE_SESSION_TIMEOUT:-3600}"  # 1 hour default
LOG_DIR="${CLAUDE_CODE_LOG_DIR:-$HOME/.claude/logs}"
LOG_FILE="$LOG_DIR/jit-sessions.log"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_ID="jit-$(date +%s)-$$"

# Parse --session-timeout arg if provided
if [[ "${1:-}" == "--session-timeout" ]]; then
  SESSION_TIMEOUT="${2:?'--session-timeout requires a value in seconds'}"
  shift 2
fi

log() { echo "$TIMESTAMP | $1" | tee -a "$LOG_FILE"; }

log "SESSION_START | id=$SESSION_ID | timeout=$SESSION_TIMEOUT"

# =============================================================================
# Credential acquisition
# Choose ONE of the methods below for your environment.
# =============================================================================

# --- Method 1: Direct API key (BASELINE -- no JIT, but adds env scrubbing) ---
# This is the minimum viable implementation. Your long-lived key is still used,
# but subprocess scrubbing prevents it from leaking to child processes.
# Upgrade to Method 2 or 3 when your infrastructure supports it.

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set. Set it before running jit-wrapper.sh"
  exit 1
fi

# Validate key format
if ! echo "$ANTHROPIC_API_KEY" | grep -qE '^sk-ant-[a-zA-Z0-9\-_]{90,}$'; then
  echo "WARNING: ANTHROPIC_API_KEY format looks unusual. Verify it is correct."
fi

SCOPED_KEY="$ANTHROPIC_API_KEY"

# --- Method 2: 1Password CLI (recommended for teams) ---
# Uncomment and configure if you use 1Password:
# SCOPED_KEY=$(op read "op://vault/anthropic-api-key/credential" 2>/dev/null) || {
#   echo "ERROR: Could not retrieve key from 1Password. Is 'op' signed in?"
#   exit 1
# }

# --- Method 3: HashiCorp Vault (recommended for enterprise) ---
# Uncomment and configure if you use Vault:
# VAULT_TOKEN=$(vault auth ... 2>/dev/null)
# SCOPED_KEY=$(vault kv get -field=api_key secret/anthropic/claude-code 2>/dev/null) || {
#   echo "ERROR: Could not retrieve key from Vault"
#   exit 1
# }

# --- Method 4: AWS Secrets Manager ---
# SCOPED_KEY=$(aws secretsmanager get-secret-value \
#   --secret-id anthropic/claude-code-api-key \
#   --query SecretString \
#   --output text 2>/dev/null | jq -r '.api_key') || {
#   echo "ERROR: Could not retrieve key from AWS Secrets Manager"
#   exit 1
# }

# =============================================================================
# Session file for cleanup tracking
# =============================================================================
SESSION_FILE="$HOME/.claude/.current-session"
echo "$SESSION_ID" > "$SESSION_FILE"
export CLAUDE_CODE_SESSION_ID="$SESSION_ID"
export CLAUDE_CODE_JIT_KEY_ID="$SESSION_ID"

# =============================================================================
# Cleanup function -- runs on exit regardless of how session ends
# =============================================================================
cleanup() {
  local exit_code=$?
  local end_time
  end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  log "SESSION_END | id=$SESSION_ID | exit_code=$exit_code | ended=$end_time"

  # Remove session tracking file
  rm -f "$SESSION_FILE"

  # For JIT tokens: add revocation here
  # vault token revoke "$VAULT_TOKEN" 2>/dev/null || true
  # aws sts revoke ... 2>/dev/null || true

  # Wipe the scoped key from memory (best effort in bash)
  SCOPED_KEY=""
  unset SCOPED_KEY

  exit $exit_code
}

trap cleanup EXIT INT TERM

# =============================================================================
# Timeout enforcement
# =============================================================================
timeout_kill() {
  echo "SESSION TIMEOUT: Claude Code session exceeded $SESSION_TIMEOUT seconds."
  echo "Session ID: $SESSION_ID"
  echo "This is a security control. Start a new session to continue."
  log "SESSION_TIMEOUT | id=$SESSION_ID"
  kill $CLAUDE_PID 2>/dev/null || true
}

# =============================================================================
# Launch Claude Code with:
# - Scoped credentials
# - Subprocess env scrubbing enabled
# - Session timeout enforcement
# =============================================================================

(
  sleep "$SESSION_TIMEOUT"
  timeout_kill
) &
TIMEOUT_PID=$!

ANTHROPIC_API_KEY="$SCOPED_KEY" \
  CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 \
  CLAUDE_CODE_SESSION_ID="$SESSION_ID" \
  CLAUDE_CODE_LOG_DIR="$LOG_DIR" \
  claude "$@" &

CLAUDE_PID=$!

log "CLAUDE_LAUNCHED | pid=$CLAUDE_PID | args=$*"

# Wait for Claude to finish
wait $CLAUDE_PID
CLAUDE_EXIT=$?

# Kill timeout watchdog
kill $TIMEOUT_PID 2>/dev/null || true
wait $TIMEOUT_PID 2>/dev/null || true

exit $CLAUDE_EXIT
